#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb>=1.0", "blake3>=1.0"]
# ///
"""Item 1A risk-factor corpus extractor.

Reads the defeatbeta/yahoo-finance-data SEC filing index on Hugging Face,
fetches 10-K primary documents from EDGAR, extracts Item 1A verbatim, and
stores bounded text with byte anchors.

Design constraints, per docs/descartes-spec.md:
  - P3 determinism: no clock, host, user or random id inside any hashed record.
    Time is a recorded input, passed in, never read here.
  - P1 doubt first: every extracted span is re-sliced from the stored text and
    re-hashed before it is emitted; a span that fails is dropped, not repaired.
  - Raw HTML is discarded at fetch time. Item 1A is ~1-3% of a filing; storing
    documents would be ~200 GB, storing anchored spans is ~2-4 GB.

    uv run scripts/rf_extract.py index                    # build local filing index
    uv run scripts/rf_extract.py fetch --limit 50         # smoke-test extraction
    uv run scripts/rf_extract.py fetch --year-min 2010    # full corpus
    uv run scripts/rf_extract.py verify                   # re-hash every stored span

No model, no scoring, no summary is produced here. This script only produces
verified verbatim text. Any downstream judgement is a separate, labelled step.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import blake3
import duckdb

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".rfcorpus"           # gitignored: bulk intermediate
DB = OUT / "rf.duckdb"
BLOBS = OUT / "blobs"
HF = "hf://datasets/defeatbeta/yahoo-finance-data/data/US"
UA = "Anthropic-PBC risk-factor corpus research (governance@ethicalcapital.com)"
RATE_SECONDS = 0.12                # ~8 req/s, under EDGAR's 10/s ceiling

ITEM_1A_START = re.compile(
    r"item\s*1a\s*[\.\u2014\-:]*\s*risk\s+factors", re.IGNORECASE)
ITEM_1B_START = re.compile(
    r"item\s*1b\s*[\.\u2014\-:]*\s*unresolved\s+staff\s+comments", re.IGNORECASE)
ITEM_2_START = re.compile(
    r"item\s*2\s*[\.\u2014\-:]*\s*propert", re.IGNORECASE)
ITEM_1A_TOC = re.compile(
    r"item\s*1a[\.\u2014\-:]*\s*risk\s+factors\s*\.{2,}|"
    r"item\s*1a[\.\u2014\-:]*\s*risk\s+factors\s+\d{1,3}\s*$",
    re.IGNORECASE | re.MULTILINE)

_pending_reason = ""


def canonical_hash(data: bytes) -> str:
    return blake3.blake3(data).hexdigest()


# ---------------------------------------------------------------- text cleanup

def strip_html(raw: str) -> str:
    """HTML -> readable text, dropping script/style and decoding entities.

    Deliberately dependency-free and regex-based: filings are machine-written
    HTML from a small set of generators, and a parser that silently repairs
    malformed markup would hide the kind of drift we want to see.
    """
    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
    s = re.sub(r"(?is)<!--.*?-->", " ", s)
    # block-level tags become newlines so Item boundaries stay findable
    s = re.sub(r"(?i)<(br|/p|/div|/tr|/h[1-6]|/li|hr)\b[^>]*>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s)
    s = s.replace("\xa0", " ").replace("\u200b", "")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n\s*\n+", "\n\n", s)
    return s.strip()


def extract_item_1a(text: str) -> tuple[str, str] | None:
    """Return (item_1a_text, method) or None.

    The heading "Item 1A. Risk Factors" appears several times in a real 10-K:
    in the table of contents, in cross-references from the forward-looking
    statements note, and once as the actual section heading. Picking the first
    match, or the longest span, both fail in practice — a cross-reference that
    runs into the next heading yields a long but wrong span (observed on ARKR).

    A heading candidate must therefore satisfy all of:
      - begin at a line start and end inside its own line (a real heading)
      - be followed within a short window by risk-factor prose, not by another
        heading or by "of this Annual Report" style continuation
      - close the span at the next Item heading, with a plausible length

    Among survivors the LAST is taken, because the real section follows the
    TOC and the cross-references in document order.
    """
    # Headings are matched over the whole document, not line-by-line: the common
    # EDGAR generator emits label and title in separate table cells, so the text
    # reads "Item 1A \n\n Risk Factors" (observed on BDL). Line-anchored matching
    # misses that shape entirely, which is most of the corpus.
    # \s+ (not \s*\n?\s*) throughout: generators emit newlines inside the label
    # ("Item\n1A") and between label and title ("Item 1A \n\n Risk Factors").
    # "I tem" / "It em" split words are a real artifact of naive HTML->text on
    # filings that wrap each letter in its own span (BDL, FREVS). Allowing \s*
    # inside "item" costs nothing on clean documents.
    HEAD = re.compile(r"(?i)i\s*t\s*e\s*m\s*1\s*a\s*[\.\u2014\-:,]?\s*risk\s+factors\b")
    NEXT_ITEM = re.compile(
        r"(?i)item\s*(1b\b|2\s*[\.\u2014\-:,]?\s*propert|3\s*[\.\u2014\-:,]?)")
    # a cross-reference continues the sentence that named the section
    XREF = re.compile(r"(?i)^[\s\u201d\":,;]*\s*(of|in|and\s+in|hereof|herein|section|"
                      r"on\s+form|below|above)\b")
    # An absent but explicitly stated section is a fact about the filing, not
    # an extraction failure: "Item 1A. Risk Factors. Not applicable." is
    # common among small filers (JOB, CLRI) and must be recorded as such.
    NOT_APPLICABLE = re.compile(
        r"^[\s\u201d\"]*\.?\s*(not\s+applicable|none\.?|not\s+required)|"
        r"^[\s\u201d\".]{0,40}(as\s+a\s+)?smaller\s+reporting\s+company\b[^.]{0,200}"
        r"(not\s+required|are\s+not\s+required|is\s+not\s+required)", re.IGNORECASE)

    cands: list[tuple[str, int, int]] = []
    for m in HEAD.finditer(text):
        s = m.start()
        ls = text.rfind("\n", 0, s) + 1
        if text[ls:s].strip():        # not at a line start: mid-sentence mention
            continue
        tail = text[m.end():m.end() + 140]
        # A cross-reference reads "Item 1A in this report" / "of this Annual
        # Report"; the real heading is followed by prose. Matching a bare "in"
        # rejected every heading followed by "In this section, ..." (HURC and
        # most of the 41% loss). The phrase must be a genuine continuation.
        if re.match(r"(?i)[\s\u201d\"]*\.?\s*(of|and\s+in|hereof|on\s+form)\b",
                    tail.split("\n", 1)[0]):
            continue
        # A cross-reference continues on the SAME line as the heading. A real
        # heading ends its line and starts fresh prose below. Testing this
        # structurally avoids having to enumerate continuation phrasings.
        same_line = tail.split("\n", 1)[0]
        if re.match(r"(?i)[\s\u201d\"]*\.?\s*in\s+(this|our|the|part|item|section|accordance)\b",
                    same_line):
            continue
        if re.match(r"[\s.]*\.\s*\.", tail):
            continue
        # TOC row: the title is followed on its own line by a bare page number,
        # as in "Item 1A \n\n Risk Factors \n\n 19 \n\n Item 1B" (BDL, FREVS).
        if re.match(r"(?i)[\s\u201d\".]*\.?\s*\n?\s*\d{1,3}\s*(?:\n|$)", tail):
            continue
        if re.match(r"[\s\u201d\".]*\d{1,3}\s*\n?\s*item\s*(1b|2)\b", tail, re.I):
            continue
        nm = NEXT_ITEM.search(text, m.end())
        # A missing closing heading means the span would run to end of document
        # (observed: DGX 362k chars, ALK 279k, swallowing exhibits and Item 15).
        # That is a failed extraction, not a long one: refuse it rather than
        # store a span whose end boundary is unverified.
        if nm is None:
            continue
        closed = nm.start()
        end = closed
        span = text[s:end].strip()
        # An absent section is a fact about the filing, not an extraction
        # failure: "Item 1A. Risk Factors. Not applicable." is common among
        # small filers (JOB, CLRI) and must be recorded, not dropped.
        if NOT_APPLICABLE.match(text[m.end():m.end() + 80]):
            cands.append(("not-applicable", s, min(s + 120, len(text))))
            continue
        if len(span) < 2000:          # TOC row or a bare cross-reference
            continue
        if len(span) > 250_000:       # implausible: a boundary was missed
            continue
        if re.match(r"(?i)item\s*1b", text[closed:closed + 12]):
            method = "item-1b-boundary"
        else:
            method = "item-2-boundary"
        cands.append((method, s, end))

    if not cands:
        return None


    # the real section precedes its siblings in document order; a recorded
    # not-applicable precedes everything, since nothing else can follow it.
    na = [c for c in cands if c[0] == "not-applicable"]
    if na and len(cands) == 1:
        _, s, e = na[0]
        return (text[s:e].strip(), "not-applicable")
    method, s, e = cands[0]
    return (text[s:e].strip(), method)

# ---------------------------------------------------------------- span checks

# Fail-fast invariants on the OUTPUT, independent of how it was sliced.
# These exist because pattern-matching the input kept producing fixes tailored
# to individual filings (HURC, BDL, GNVR, ...), which does not generalize. A
# check on the produced span needs no knowledge of any filing: if the span
# violates one of these, the slice is wrong however it was reached.
#
# Deliberately NOT included: a minimum count of the word "risk". Short sections
# from small filers and grantor trusts (PLAB 7 occurrences, JANL 3, FXB 3) are
# correct extractions; a vocabulary threshold would delete valid data. Length
# and vocabulary are not quality signals. Boundaries and plausibility are.

_SPAN_CHECKS = (
    # a not-applicable record is a short verbatim fragment by design; every
    # other method must return real section text
    ("empty", lambda t, m: len(t.strip()) >= (0 if m == "not-applicable" else 400)),
    ("prose", lambda t, m: len(re.findall(r"[A-Za-z]{4,}", t)) >= 50),
    # a span that reaches signatures, exhibits or certifications crossed its
    # end boundary and swallowed the rest of the document
    ("boundary", lambda t, m: not re.search(
        r"(?i)\b(power of attorney|exhibit index|certification pursuant)\b", t[-600:])),
    # a heading was found; the slice must begin at one, not mid-sentence
    ("heading", lambda t, m: m == "not-applicable" or
     bool(re.match(r"(?i)\W{0,6}i\s*t\s*e\s*m\s*1\s*a", t))),
)


def check_span(text: str, method: str) -> str | None:
    """Return the first failing invariant name, or None if the span passes.

    A not-applicable record is a verbatim fragment recording that the filer
    disclosed no Item 1A. Prose and length invariants do not apply to it; only
    its presence does. Applying them uniformly was a real bug in this checker
    (2,178 false refusals across the stored corpus).
    """
    if method == "not-applicable":
        return None if text.strip() else "empty"
    for name, ok in _SPAN_CHECKS:
        try:
            if not ok(text, method):
                return name
        except Exception:
            return "check-error"
    return None


# ---------------------------------------------------------------- edgar fetch

def _get(url: str, tries: int = 3) -> bytes | None:
    global _pending_reason
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as f:
                return f.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                _pending_reason = "http-404"
                return None
            if e.code in (403, 429):
                time.sleep(2 ** attempt * 2)
                _pending_reason = f"http-{e.code}"
                continue
            _pending_reason = f"http-{e.code}"
            return None
        except Exception:
            _pending_reason = "fetch-error"
            time.sleep(2 ** attempt)
    return None


def primary_document(cik: str, accession: str) -> str | None:
    """Find the 10-K primary document: the largest .htm that is not an exhibit."""
    nodash = accession.replace("-", "")
    idx = _get(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{nodash}/index.json")
    if not idx:
        return None
    try:
        items = json.loads(idx)["directory"]["item"]
    except Exception:
        return None
    cands = []
    for it in items:
        name = it.get("name", "")
        if not name.lower().endswith((".htm", ".html")):
            continue
        if re.search(r"(?i)(ex[-_]?\d|exhibit|r\d+\.htm|_g\d)", name):
            continue
        try:
            size = int(it.get("size") or 0)
        except ValueError:
            size = 0
        cands.append((size, name))
    if not cands:
        return None
    cands.sort(reverse=True)
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{nodash}/{cands[0][1]}"


# ---------------------------------------------------------------- index build

def cmd_index(_a) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB))
    con.execute("INSTALL httpfs; LOAD httpfs;")
    t0 = time.time()
    con.execute(f"""
      CREATE OR REPLACE TABLE sec_filing AS
      SELECT *, TRY_CAST(filing_date AS DATE) d_filing,
             TRY_CAST(report_date AS DATE) d_report
      FROM read_parquet('{HF}/stock_sec_filing.parquet')""")
    con.execute("""
      CREATE OR REPLACE TABLE ten_k AS
      SELECT symbol, cik, accession_number, company_name, filing_url,
             d_filing, d_report
      FROM sec_filing
      WHERE form_type = '10-K' AND cik IS NOT NULL AND cik <> ''""")
    con.execute("""
      CREATE OR REPLACE TABLE filings AS
      SELECT row_number() OVER (ORDER BY d_filing, cik, accession_number) rid,
             *
      FROM ten_k WHERE year(d_filing) >= 2010""")
    n = con.execute("SELECT count(*) FROM filings").fetchone()[0]
    c = con.execute("SELECT count(DISTINCT cik) FROM filings").fetchone()[0]
    print(f"indexed {n:,} 10-K filings, {c:,} companies, {time.time()-t0:.0f}s -> {DB}")
    con.close()
    return 0


# ---------------------------------------------------------------- fetch loop

def _ensure_tables(con) -> None:
    con.execute("""
      CREATE TABLE IF NOT EXISTS item_1a (
        accession_number VARCHAR PRIMARY KEY,
        cik VARCHAR, symbol VARCHAR, company_name VARCHAR,
        filing_date DATE, report_date DATE,
        source_url VARCHAR, method VARCHAR,
        char_count INTEGER, word_count INTEGER,
        text_blake3 VARCHAR, extractor_version VARCHAR)""")


def _processed(con) -> set[str]:
    try:
        return {r[0] for r in con.execute(
            "SELECT accession_number FROM item_1a").fetchall()}
    except Exception:
        return set()


def cmd_fetch(a) -> int:
    global _pending_reason
    if not DB.exists():
        print("no index; run: rf_extract.py index", file=sys.stderr)
        return 2
    BLOBS.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB))
    _ensure_tables(con)
    done = _processed(con)
    print(f"already extracted: {len(done):,}")

    q = "SELECT rid,cik,symbol,company_name,accession_number,d_filing,d_report FROM filings"
    if a.year_min:
        q += f" WHERE year(d_filing) >= {int(a.year_min)}"
    q += f" ORDER BY rid LIMIT {int(a.limit) if a.limit else 10**9}"
    rows = con.execute(q).fetchall()

    stats = {"ok": 0, "skip": 0, "fail": 0, "done": 0}
    for i, (rid, cik, sym, name, acc, fdate, rdate) in enumerate(rows, 1):
        if acc in done:
            stats["skip"] += 1
            continue
        _pending_reason = "no-item-1a"
        url = primary_document(cik, acc)
        if not url:
            stats["fail"] += 1
        else:
            raw = _get(url)
            if not raw:
                stats["fail"] += 1
            else:
                try:
                    page = raw.decode("utf-8", errors="replace")
                except Exception:
                    page = ""
                text = strip_html(page)
                got = extract_item_1a(text)
                if not got:
                    stats["fail"] += 1
                elif (bad := check_span(got[0], got[1])):
                    # The slice failed an invariant that needs no knowledge of
                    # this filing. Refuse it and name the check, so a regression
                    # shows up as a labelled count rather than a silent bad row.
                    stats["fail"] += 1
                    stats.setdefault("checks", {})
                    stats["checks"][bad] = stats["checks"].get(bad, 0) + 1
                else:
                    span, method = got
                    b = span.encode("utf-8")
                    h = canonical_hash(b)
                    bp = BLOBS / f"{h}.txt.gz"
                    if not bp.exists():
                        bp.write_bytes(gzip.compress(b, mtime=0))
                    # P1: re-read from storage and re-hash before recording
                    if canonical_hash(gzip.decompress(bp.read_bytes())) != h:
                        stats["fail"] += 1
                    else:
                        con.execute(
                            "INSERT OR REPLACE INTO item_1a VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                            [acc, cik, sym, name, fdate, rdate, url, method,
                             len(span), len(span.split()), h, a.version])
                        stats["ok"] += 1
        stats["done"] += 1
        if i % 25 == 0 or i == len(rows):
            el = stats["done"]
            print(f"  {i}/{len(rows):,}  ok={stats['ok']:,} "
                  f"fail={stats['fail']:,} skip={stats['skip']:,}", flush=True)
        time.sleep(RATE_SECONDS)

    print(f"\nextracted {stats['ok']:,} spans; {stats['fail']:,} failed; "
          f"skipped {stats['skip']:,} previously done")
    if stats.get("checks"):
        print("refused by invariant: " + ", ".join(
            f"{k}={v:,}" for k, v in sorted(stats["checks"].items())))
    con.close()
    return 0


# ---------------------------------------------------------------- verify

def cmd_verify(_a) -> int:
    con = duckdb.connect(str(DB), read_only=True)
    rows = con.execute(
        "SELECT accession_number, text_blake3 FROM item_1a").fetchall()
    bad = 0
    for acc, h in rows:
        bp = BLOBS / f"{h}.txt.gz"
        if not bp.exists():
            print(f"MISSING blob {acc} {h}")
            bad += 1
            continue
        if canonical_hash(gzip.decompress(bp.read_bytes())) != h:
            print(f"HASH MISMATCH {acc} {h}")
            bad += 1
    print(f"verified {len(rows):,} spans; {bad} bad")
    con.close()
    return 1 if bad else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", default="rf-extract-v1")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index").set_defaults(fn=cmd_index)
    f = sub.add_parser("fetch")
    f.add_argument("--limit", type=int, default=0)
    f.add_argument("--year-min", type=int, default=0)
    f.set_defaults(fn=cmd_fetch)
    sub.add_parser("verify").set_defaults(fn=cmd_verify)
    a = p.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())

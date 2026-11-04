#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["blake3==1.0.11", "pypdf==5.4.0"]
# ///
"""Health-of-democracy proxies: GDELT phrase timelines and Rooney Report toplines.

These series measure ATTENTION to democracy (how often news and television use
the words) and stated CONDITIONS (what survey respondents say). None of them
measures any effect of Anthropic on democracy. See docs/democracy-proxies.md.

Two sources, each pinned by the bytes actually received:

  gdelt   GDELT TV 2.0 API (television captions, Internet Archive TV News
          Archive) and GDELT DOC 2.0 API (online news). API responses are not
          reproducible later, so every response is saved verbatim into the
          gitignored .democorpus/gdelt/ and recorded in MANIFEST.tsv with request
          URL, bytes, SHA-256, BLAKE3 and the --as-of date. The saved bytes ARE
          the pin; `fetch-gdelt` never overwrites a saved response.
  rooney  Notre Dame Rooney Democracy Institute "Rooney Reports" (Health of
          Democracy Survey). The PDFs are pinned the same way into
          .democorpus/rooney/. Toplines are HAND-TRANSCRIBED into
          corpus/democracy/rooney-transcription.tsv, each with a verbatim quote
          and page; `build` re-extracts the page text from the pinned PDF and
          fails unless every quote is on its stated page and every percent is
          in its quote. Numbers that appear only in chart images are not
          transcribed.

    uv run scripts/democracy_proxies.py fetch-gdelt  --as-of 2026-11-04
    uv run scripts/democracy_proxies.py fetch-rooney --as-of 2026-11-04
    uv run scripts/democracy_proxies.py build     # TSVs from saved bytes only; no network
    uv run scripts/democracy_proxies.py verify    # re-hash every pin; rebuild must match byte for byte

No clock, host or random id enters any output: the as-of date is an argument.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import blake3

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus" / "democracy"
BULK = ROOT / ".democorpus"                       # gitignored: every saved response and PDF
MANIFEST = CORPUS / "MANIFEST.tsv"
TRANSCRIPTION = CORPUS / "rooney-transcription.tsv"   # hand-transcribed report numbers (input)
QUESTIONNAIRE = CORPUS / "rooney-questionnaire.tsv"   # hand-copied questionnaire stems (input)
OUTPUTS = ("gdelt-timelines.tsv", "gdelt-summary.tsv", "rooney-reports.tsv", "rooney-toplines.tsv", "rooney-items.tsv")
UA = "anthropic-pbc democracy-proxies research (public CC0 research repo; contact sloane@ethicic.com)"
TSV = {"delimiter": "\t", "quoting": csv.QUOTE_NONE, "quotechar": None}   # plain TSV: no quoting, no tabs in fields
MANIFEST_COLS = ["source", "item", "path", "url", "bytes", "sha256", "blake3", "as_of"]

# ------------------------------------------------------------------ GDELT
DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"
TV_API = "https://api.gdeltproject.org/api/v2/tv/tv"
DOC_START = "20170101000000"     # DOC 2.0 timeline modes reach back to 1 January 2017
TV_START = "20090701000000"      # TV 2.0 reaches back to July 2009
TV_MARKET = 'market:"National"'  # the national networks GDELT monitors (CNN, MSNBC, FOX News, ...)
GDELT_SLEEP = 20                 # GDELT asks for at most one request every 5 seconds; stay well under

# (id, phrase query). DOC: terms are ANDed within an article; near20 requires the
# two words within 20 words of each other. TV: terms are ANDed within one
# 15-second caption clip, which is already a proximity constraint.
DOC_QUERIES = [
    ("hod", '"health of democracy"'),
    ("anthropic_hod", 'anthropic "health of democracy"'),
    ("anthropic_near20_democracy", 'near20:"anthropic democracy"'),
    ("claude_near20_democracy", 'near20:"claude democracy"'),
    ("democracy", "democracy"),
    ("anthropic", "anthropic"),
]
TV_QUERIES = [
    ("hod", '"health of democracy"'),
    ("anthropic_hod", 'anthropic "health of democracy"'),
    ("anthropic_democracy_clip", "anthropic democracy"),
    ("claude_democracy_clip", "claude democracy"),
    ("democracy", "democracy"),
    ("anthropic", "anthropic"),
]


def gdelt_requests(as_of: str) -> list[dict[str, str]]:
    end = as_of.replace("-", "") + "000000"
    out = []
    for qid, q in DOC_QUERIES:
        for mode in ("timelinevol", "timelinevolraw"):
            p = {"query": q, "mode": mode, "format": "json", "startdatetime": DOC_START, "enddatetime": end}
            out.append({"item": f"doc_{qid}_{mode}", "api": "doc", "qid": qid, "query": q, "mode": mode,
                        "url": DOC_API + "?" + urllib.parse.urlencode(p, quote_via=urllib.parse.quote)})
    for qid, q in TV_QUERIES:
        for norm in ("percent", "raw"):
            p = {"query": f"{q} {TV_MARKET}", "mode": "timelinevol", "format": "json", "datacomb": "combined",
                 "startdatetime": TV_START, "enddatetime": end}
            if norm == "raw":
                p["datanorm"] = "raw"
            out.append({"item": f"tv_{qid}_timelinevol_{norm}", "api": "tv", "qid": qid,
                        "query": f"{q} {TV_MARKET}", "mode": f"timelinevol/{norm}",
                        "url": TV_API + "?" + urllib.parse.urlencode(p, quote_via=urllib.parse.quote)})
    return out


# ------------------------------------------------------------------ Rooney
ROONEY_BASE = "https://rooneyinstitute.nd.edu"
ROONEY_PAGES = [
    ("listing", "/research/health-of-democracy-survey/rooney-reports/"),
    ("survey_page", "/research/health-of-democracy-survey/"),
]
# (report id, date as listed, title as listed, asset path) -- from the listing page pinned above.
ROONEY_REPORTS = [
    ("R01", "October 2024", "Democracy in the Balance: Partisan Perspectives on Support for Democratic Values", "/assets/590560/rooney_report_1.pdf"),
    ("R02", "November 2024", "The Representation Paradox: How Pure Independents Navigate Democratic Values", "/assets/597615/241112_rooney_report_2.pdf"),
    ("R03", "December 2024", "Christian Nationalism and Democracy: Attitudes Towards Democratic Participation and Representation", "/assets/598034/rooney_report_3.pdf"),
    ("R04", "February 2025", "Views on Democratic Principles and Leadership: Divides Between Trump and Non-Trump Voters", "/assets/612507/rooney_february.pdf"),
    ("R05", "March 2025", "Trump Voters Back Strong Leadership — But Not Radical Democratic Reform", "/assets/612503/rooney_report_5.pdf"),
    ("R06", "April 2025", "Who do Americans like least? Polarization, Consesus, and the Politics of Dislike", "/assets/613114/rooney_report_6.pdf"),
    ("R07", "September 2025", "The State of Democratic Sentiment in America", "/assets/636474/rooney_report_7_sep_2025.pdf"),
    ("R08", "December 2025", "The Growth of Support for Political Violence", "/assets/652986/rooney_report_8_dec_2025.pdf"),
    ("R09", "January 2026", "The Rising Tide of Christian Nationalism", "/assets/652984/rooney_report_9_jan_2026.pdf"),
    ("R10", "February 2026", "Post-Election Anxieties: The 2024 Election and Feelings of Threat", "/assets/652985/rooney_report_10_feb_2026.pdf"),
    ("R11", "March 2026", "Americans Agree on Democratic Principles- but Opinions Diverge on their Application", "/assets/656052/rooney_report_11_mar_2026.pdf"),
    ("R12", "April 2026", "The Fairness Divide: How Americans View Opportunity and Advantage", "/assets/656053/rooney_report_12_apr_2026.pdf"),
    ("R13", "May 2026", "Who Counts? Political Tolerance in American Democracy", "/assets/658265/rooney_report_13_may_2026_1_.pdf"),
]
# Questionnaires (no frequencies) published on the survey page; pinned for question wording.
ROONEY_CODEBOOKS = [
    ("CB_2025_10", "NDHDS October 2025 questionnaire", "/assets/661813/notredamedemocracyamerispeakomnibusoctw2docx.pdf"),
    ("CB_2026_05", "NDHDS May 2026 questionnaire", "/assets/661814/ndamerispeakomnibusmayw1docx.pdf"),
]
AI_DISCLOSURE = re.compile(r"AI transparency statement:.*?(?:discretion of the author\.|$)")


# ------------------------------------------------------------------ helpers
def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def b3(b: bytes) -> str:
    return blake3.blake3(b).hexdigest()


def read_manifest() -> list[dict[str, str]]:
    if not MANIFEST.exists():
        return []
    with MANIFEST.open(newline="") as f:
        return list(csv.DictReader(f, **TSV))


def write_manifest(rows: list[dict[str, str]]) -> None:
    CORPUS.mkdir(parents=True, exist_ok=True)
    rows = sorted(rows, key=lambda r: (r["source"], r["item"]))
    with MANIFEST.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_COLS, **TSV, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def http_get(url: str, tries: int = 4) -> tuple[int, bytes]:
    last: Exception | None = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=240) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429 or e.code >= 500:
                wait = min(60 * 2 ** i, 300)          # 60, 120, 240, 300 ...: back off, do not hammer
                print(f"  HTTP {e.code}; waiting {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            wait = 30 * (i + 1)
            print(f"  {type(e).__name__}: {e}; waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"giving up on {url}: {last}")


def pin(source: str, item: str, rel: str, url: str, as_of: str, sleep: float) -> bool:
    """Fetch url into BULK/rel unless already pinned; record it in MANIFEST. Returns True if fetched."""
    rows = read_manifest()
    have = {(r["source"], r["item"]) for r in rows}
    dst = BULK / rel
    if (source, item) in have and dst.exists():
        return False
    status, body = http_get(url)
    if source == "gdelt":
        try:
            json.loads(body)
        except ValueError:
            raise RuntimeError(f"{item}: response is not JSON (first bytes: {body[:120]!r}); not pinned")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(body)
    rows = [r for r in rows if (r["source"], r["item"]) != (source, item)]
    rows.append({"source": source, "item": item, "path": rel, "url": url, "bytes": str(len(body)),
                 "sha256": sha256(body), "blake3": b3(body), "as_of": as_of})
    write_manifest(rows)
    print(f"  pinned {item}: {len(body)} bytes")
    time.sleep(sleep)
    return True


def norm_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = (s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
          .replace("–", "-").replace("—", "-").replace("­", "").replace("​", ""))
    return re.sub(r"\s+", " ", s).strip()


def write_tsv(path: Path, header: list[str], rows: list[list[str]]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, **TSV, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    data = buf.getvalue().encode("utf-8")
    path.write_bytes(data)
    return data


# ------------------------------------------------------------------ fetch
def cmd_fetch_gdelt(as_of: str) -> int:
    # TV first: the DOC API rate-limits harder, and a DOC stall should not block the TV pins.
    prio = ["anthropic_hod", "anthropic_near20_democracy", "claude_near20_democracy", "anthropic", "democracy", "hod"]
    reqs = sorted(gdelt_requests(as_of), key=lambda r: (r["api"] != "tv", r["mode"].endswith("raw"),
                                                      prio.index(r["qid"]) if r["qid"] in prio else -1))
    for r in reqs:
        print(r["item"], flush=True)
        try:
            pin("gdelt", r["item"], f"gdelt/{r['item']}.json", r["url"], as_of, GDELT_SLEEP)
        except RuntimeError as e:   # stop rather than keep hitting a rate-limited API; rerun resumes
            print(f"STOPPED at {r['item']}: {e}", file=sys.stderr)
            return 1
    print(f"ok: {len(reqs)} GDELT responses pinned")
    return 0


def cmd_fetch_rooney(as_of: str) -> int:
    for item, path in ROONEY_PAGES:
        pin("rooney", item, f"rooney/{item}.html", ROONEY_BASE + path, as_of, 2)
    for rid, _, _, path in ROONEY_REPORTS:
        pin("rooney", rid, f"rooney/{rid}_{Path(path).name}", ROONEY_BASE + path, as_of, 2)
    for cid, _, path in ROONEY_CODEBOOKS:
        pin("rooney", cid, f"rooney/{cid}_{Path(path).name}", ROONEY_BASE + path, as_of, 2)
    # Cross-check: every PDF linked from the pinned listing page is in ROONEY_REPORTS.
    listing = (BULK / "rooney/listing.html").read_text("utf-8", "replace")
    linked = sorted(set(re.findall(r'href="(/assets/[^"]+\.pdf)"', listing)))
    known = {p for *_, p in ROONEY_REPORTS}
    missing = [p for p in linked if p not in known]
    if missing:
        print(f"WARNING: listing links PDFs not in ROONEY_REPORTS: {missing}", file=sys.stderr)
        return 1
    print(f"ok: {len(ROONEY_REPORTS)} reports (= {len(linked)} PDFs linked from the listing) and "
          f"{len(ROONEY_CODEBOOKS)} questionnaires pinned")
    return 0


# ------------------------------------------------------------------ build
def load_pinned(source: str, item: str) -> bytes:
    for r in read_manifest():
        if r["source"] == source and r["item"] == item:
            b = (BULK / r["path"]).read_bytes()
            if sha256(b) != r["sha256"] or b3(b) != r["blake3"] or len(b) != int(r["bytes"]):
                raise RuntimeError(f"{source}/{item}: saved bytes do not match MANIFEST")
            return b
    raise KeyError(f"{source}/{item} not pinned; run fetch-{source}")


def fmt(v: float) -> str:
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return s if s else "0"


def build_gdelt(as_of: str) -> dict[str, bytes]:
    rows: list[list[str]] = []
    summ: list[list[str]] = []
    for r in gdelt_requests(as_of):
        try:
            d = json.loads(load_pinned("gdelt", r["item"]))
        except KeyError:          # never received (rate-limited): reported, not silently dropped
            summ.append([r["api"], r["qid"], r["query"], r["mode"], "NOT PINNED", "", "", "", "", "0", "0",
                         "", "", "", "", ""])
            continue
        timeline = d.get("timeline", [])
        if r["api"] == "doc":
            unit = "pct_of_monitored_articles" if r["mode"] == "timelinevol" else "articles"
        else:
            unit = "pct_of_monitored_airtime" if r["mode"].endswith("percent") else "caption_clips_15s"
        res = (d.get("query_details") or {}).get("date_resolution", "")
        for s in timeline:
            series = s.get("series", "")
            pts = s.get("data", [])
            for p in pts:
                date = p["date"][:8]
                rows.append([r["api"], r["qid"], r["query"], r["mode"], series, date, fmt(float(p["value"])), unit])
                if "norm" in p:
                    rows.append([r["api"], r["qid"], r["query"], r["mode"], series + " (norm)", date,
                                 fmt(float(p["norm"])), "articles_monitored_total"])
            nz = [p for p in pts if float(p["value"]) > 0]
            peak = max(pts, key=lambda p: (float(p["value"]), p["date"])) if pts else None
            summ.append([r["api"], r["qid"], r["query"], r["mode"], series, unit, res,
                         pts[0]["date"][:8] if pts else "", pts[-1]["date"][:8] if pts else "",
                         str(len(pts)), str(len(nz)),
                         nz[0]["date"][:8] if nz else "", nz[-1]["date"][:8] if nz else "",
                         peak["date"][:8] if peak and nz else "", fmt(float(peak["value"])) if peak and nz else "0",
                         fmt(sum(float(p["value"]) for p in pts))])
        if not timeline:
            summ.append([r["api"], r["qid"], r["query"], r["mode"], "", unit, res, "", "", "0", "0", "", "", "", "0", "0"])
    rows.sort(key=lambda x: (x[0], x[1], x[3], x[4], x[5]))
    summ.sort(key=lambda x: (x[0], x[1], x[3], x[4]))
    out = {}
    out["gdelt-timelines.tsv"] = write_tsv(CORPUS / "gdelt-timelines.tsv",
        ["source", "query_id", "query", "mode", "series", "date", "value", "unit"], rows)
    out["gdelt-summary.tsv"] = write_tsv(CORPUS / "gdelt-summary.tsv",
        ["source", "query_id", "query", "mode", "series", "unit", "resolution", "first_period", "last_period",
         "n_periods", "n_nonzero", "first_nonzero", "last_nonzero", "peak_period", "peak_value", "sum_value"], summ)
    return out


def pdf_pages(b: bytes) -> tuple[list[str], list[int]]:
    from pypdf import PdfReader
    rd = PdfReader(io.BytesIO(b))
    texts, imgs = [], []
    for p in rd.pages:
        texts.append(norm_text(p.extract_text() or ""))
        try:
            imgs.append(len(p.images))
        except Exception:
            imgs.append(-1)
    return texts, imgs


def build_rooney() -> dict[str, bytes]:
    pages: dict[str, list[str]] = {}
    rep_rows = []
    for rid, date, title, path in ROONEY_REPORTS:
        raw = load_pinned("rooney", rid)
        texts, imgs = pdf_pages(raw)
        pages[rid] = texts
        disc, disc_page = "", ""
        for i, t in enumerate(texts, 1):
            m = AI_DISCLOSURE.search(t)
            if m:
                disc, disc_page = m.group(0), str(i)
        rep_rows.append([rid, date, title, ROONEY_BASE + path, sha256(raw), str(len(texts)),
                         ";".join(str(n) for n in imgs), disc_page, disc])
    with TRANSCRIPTION.open(newline="") as f:
        trans = list(csv.DictReader(f, **TSV))
    top_rows, errors = [], []
    for i, t in enumerate(trans, 2):
        rid, pg = t["report"], int(t["page"])
        quote = norm_text(t["quote"])
        text = pages[rid][pg - 1] if 0 < pg <= len(pages[rid]) else ""
        if quote not in text:
            found = [str(j) for j, x in enumerate(pages[rid], 1) if quote in x]
            errors.append(f"line {i} {rid} p{pg}: quote not on page (found on: {found or 'none'}): {quote!r}")
            continue
        vt = norm_text(t["value_text"])
        if vt not in quote:
            errors.append(f"line {i}: value_text {vt!r} not in quote")
        if t["percent"] and not re.search(r"(?<![\d.])" + re.escape(t["percent"]) + r"(?![\d.])", quote):
            errors.append(f"line {i}: percent {t['percent']} not in quote")
        top_rows.append([rid, t["page"], t["wave_as_stated"], t["group"], t["item"], t["wording_in_report"],
                         t["wording_kind"], t["response"], t["value_text"], t["percent"], quote,
                         blake3.blake3(quote.encode()).hexdigest()])
    # Questionnaire wording: each hand-copied stem must occur in the pinned questionnaire PDF.
    cb_pages = {cid: pdf_pages(load_pinned("rooney", cid))[0] for cid, _, _ in ROONEY_CODEBOOKS}
    item_rows = []
    with QUESTIONNAIRE.open(newline="") as f:
        for i, q in enumerate(csv.DictReader(f, **TSV), 2):
            stem = norm_text(q["stem_quote"])
            found = [str(j) for j, x in enumerate(cb_pages[q["codebook"]], 1) if stem in x]
            if not found:
                errors.append(f"questionnaire line {i}: stem not in {q['codebook']}: {stem!r}")
                continue
            item_rows.append([q["item"], q["codebook"], q["block"], q["letter"], ";".join(found), stem,
                              blake3.blake3(stem.encode()).hexdigest(), q["note"]])
    if errors:
        raise RuntimeError("transcription check failed:\n  " + "\n  ".join(errors))
    order = {r[0]: i for i, r in enumerate(ROONEY_REPORTS)}
    top_rows.sort(key=lambda r: (order[r[0]], int(r[1]), r[4], r[3], r[2]))
    out = {}
    out["rooney-reports.tsv"] = write_tsv(CORPUS / "rooney-reports.tsv",
        ["report", "date_listed", "title_listed", "url", "pdf_sha256", "pages", "images_per_page",
         "ai_disclosure_page", "ai_disclosure_verbatim"], rep_rows)
    out["rooney-toplines.tsv"] = write_tsv(CORPUS / "rooney-toplines.tsv",
        ["report", "page", "wave_as_stated", "group", "item", "wording_in_report", "wording_kind", "response",
         "value_text", "percent", "quote_normalised", "quote_blake3"], top_rows)
    out["rooney-items.tsv"] = write_tsv(CORPUS / "rooney-items.tsv",
        ["item", "codebook", "block", "letter", "pages", "stem_normalised", "stem_blake3", "note"], item_rows)
    return out


def cmd_build(as_of: str) -> dict[str, bytes]:
    out = build_gdelt(as_of)
    out.update(build_rooney())
    for k, v in out.items():
        print(f"  {k}: {v.count(b'\n') - 1} rows, sha256 {sha256(v)[:16]}")
    return out


def cmd_verify(as_of: str) -> int:
    bad = 0
    rows = read_manifest()
    for r in rows:
        p = BULK / r["path"]
        if not p.exists():
            print(f"MISSING {r['path']}")
            bad += 1
            continue
        b = p.read_bytes()
        if len(b) != int(r["bytes"]) or sha256(b) != r["sha256"] or b3(b) != r["blake3"]:
            print(f"MISMATCH {r['path']}")
            bad += 1
    before = {n: (CORPUS / n).read_bytes() for n in OUTPUTS if (CORPUS / n).exists()}
    after = cmd_build(as_of)
    for n, b in after.items():
        if before.get(n) != b:
            print(f"NOT BYTE-IDENTICAL on rebuild: {n}")
            bad += 1
    print(f"{'ok' if not bad else 'FAIL'}: {len(rows)} pins re-hashed, {len(after)} outputs rebuilt, {bad} problems")
    return 1 if bad else 0


def as_of_from_manifest() -> str:
    vals = sorted({r["as_of"] for r in read_manifest()})
    if len(vals) != 1:
        raise SystemExit(f"expected one as-of in MANIFEST, found {vals}")
    return vals[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("fetch-gdelt", "fetch-rooney"):
        sp = sub.add_parser(c)
        sp.add_argument("--as-of", required=True, help="recorded fetch date, YYYY-MM-DD (also the GDELT end date)")
    sub.add_parser("build")
    sub.add_parser("verify")
    a = ap.parse_args()
    if a.cmd == "fetch-gdelt":
        return cmd_fetch_gdelt(a.as_of)
    if a.cmd == "fetch-rooney":
        return cmd_fetch_rooney(a.as_of)
    if a.cmd == "build":
        cmd_build(as_of_from_manifest())
        return 0
    return cmd_verify(as_of_from_manifest())


if __name__ == "__main__":
    sys.exit(main())

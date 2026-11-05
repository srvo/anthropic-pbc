#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb==2.0.0", "blake3>=1.0"]
# ///
"""S&P 500 earnings-call AI corpus: deterministic, verbatim, byte-anchored.

Source: defeatbeta/yahoo-finance-data on Hugging Face (ODC-BY 1.0), table
stock_earning_call_transcripts, pinned to one dataset commit. Universe: the
"S&P 500 component stocks" table of Wikipedia's List of S&P 500 companies,
pinned to one revision id. Both pins live in corpus/earnings-calls/MANIFEST.tsv.

Design constraints, per docs/descartes-spec.md and docs/risk-factor-corpus.md:
  - P3 determinism: no clock, host, user or random id in any output. Rows are
    sorted; parquet is written by a pinned DuckDB.
  - Verbatim only: every window is a [start, end) character slice of a source
    paragraph, re-sliced from the pinned source and re-hashed by `verify`. Nothing is summarised.
  - No model, no scoring. Matching is a published regex; classification is a
    separate, labelled step (scripts/ec_classify.py).

    uv run scripts/ec_extract.py fetch         # download the pinned parquet, check BLAKE3
    uv run scripts/ec_extract.py constituents  # pinned Wikipedia revision -> sp500-constituents.tsv
    uv run scripts/ec_extract.py build         # calls.tsv, ai-paragraphs.parquet, ai-windows.parquet
    uv run scripts/ec_extract.py verify        # re-slice every window from the source and re-hash it

The committed tables hold ids, metadata, [start, end) offsets and BLAKE3 hashes,
never text: quotes from the calls may be published, whole transcripts and the
whole corpus may not (maintainer decision, 2026-11-04). `build` also writes the
full tables, text included, into the gitignored .eccorpus/ (scripts/ec_text.py).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.request
from pathlib import Path

import blake3
import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ec_text as ect  # noqa: E402  (where committed tables and local text live)

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus" / "earnings-calls"
BULK = ROOT / ".eccorpus"                      # gitignored: 2.3 GB source parquet
MANIFEST = CORPUS / "MANIFEST.tsv"
UA = "anthropic-pbc earnings-call corpus research (github.com/ethicalcapital/anthropic-pbc)"

# Term families. `AI` is case-sensitive (avoids "ai" inside words and "Ai" names);
# the phrases are case-insensitive. Python `re` and DuckDB RE2 accept both forms.
TERMS = {
    "ai":        r"\bAI\b|\bA\.I\.|\bGenAI\b|\bAGI\b",
    "ai_phrase": r"(?i:artificial intelligence|generative ai|generative model|gen ai\b)",
    "ml":        r"(?i:machine learning|deep learning|neural net)",
    "llm":       r"\bLLMs?\b|(?i:large language model)",
    "vendor":    r"(?i:chatgpt|openai|anthropic|\bclaude\b|\bgemini\b|copilot)",
    "agentic":   r"(?i:agentic|ai agents?\b)",
}
ANY = "(" + "|".join(f"(?:{p})" for p in TERMS.values()) + ")"
TERM_RE = {k: re.compile(v) for k, v in TERMS.items()}
ANY_RE = re.compile(ANY)
SENT_END = re.compile(r"(?<=[.!?])\s+")
MAX_WINDOW = 1500     # chars; longer sentence windows are clipped around the match
CLIP_PAD = 600


def b3(s: str) -> str:
    return blake3.blake3(s.encode("utf-8")).hexdigest()


def manifest() -> dict[str, dict[str, str]]:
    with MANIFEST.open(newline="") as f:
        return {r["id"]: r for r in csv.DictReader(f, delimiter="\t")}


def source_path() -> Path:
    m = manifest()["transcripts"]
    return BULK / m["path"]


# ---------------------------------------------------------------- fetch
def cmd_fetch() -> int:
    m = manifest()["transcripts"]
    dst = BULK / m["path"]
    BULK.mkdir(exist_ok=True)
    if not dst.exists():
        req = urllib.request.Request(m["url"], headers={"User-Agent": UA})
        tmp = dst.with_suffix(".part")
        with urllib.request.urlopen(req, timeout=60) as r, tmp.open("wb") as f:
            while chunk := r.read(1 << 22):
                f.write(chunk)
        tmp.rename(dst)
    h = blake3.blake3(max_threads=blake3.blake3.AUTO)
    with dst.open("rb") as f:
        while chunk := f.read(1 << 24):
            h.update(chunk)
    got, size = h.hexdigest(), dst.stat().st_size
    if str(size) != m["bytes"] or got != m["blake3"]:
        print(f"FAIL: {dst.name} bytes={size} blake3={got}\n  manifest bytes={m['bytes']} blake3={m['blake3']}")
        return 1
    print(f"ok: {dst.name} {size} bytes blake3 {got}")
    return 0


# ---------------------------------------------------------------- constituents
def cmd_constituents() -> int:
    m = manifest()["sp500"]
    req = urllib.request.Request(m["url"], headers={"User-Agent": UA})
    page = json.load(urllib.request.urlopen(req, timeout=30))["query"]["pages"][0]
    rev = page["revisions"][0]
    text = rev["slots"]["main"]["content"]
    if b3(text) != m["blake3"]:
        print(f"FAIL: revision {rev['revid']} wikitext blake3 {b3(text)} != manifest {m['blake3']}")
        return 1
    section = text.split('id="constituents"', 1)[1].split("|}", 1)[0]
    rows = []
    for line in section.split("\n|-")[1:]:
        t = re.search(r"\{\{(?:NyseSymbol|NasdaqSymbol|BZX link|Cboe ticker)\|([A-Za-z.]+)", line, re.I)
        cik = re.search(r"\|\|\s*(\d{10})\s*\|\|", line) or re.search(r"\b(\d{10})\b", line)
        if t:
            rows.append((t.group(1).upper().replace(".", "-"), cik.group(1) if cik else ""))
    rows = sorted(set(rows))
    out = CORPUS / "sp500-constituents.tsv"
    with out.open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["symbol", "cik"])
        w.writerows(rows)
    print(f"ok: {len(rows)} constituents from wikipedia revid {rev['revid']} -> {out.relative_to(ROOT)}")
    return 0


# ---------------------------------------------------------------- build
def windows_for(content: str) -> list[tuple[int, int, list[str]]]:
    """Merged sentence windows (match sentence +/- 1) as [start, end) offsets."""
    bounds, pos = [], 0
    for m in SENT_END.finditer(content):
        bounds.append((pos, m.start()))
        pos = m.end()
    bounds.append((pos, len(content)))
    hits = sorted({i for i, (s, e) in enumerate(bounds) if ANY_RE.search(content, s, e)})
    spans: list[list[int]] = []
    for i in hits:
        lo, hi = max(i - 1, 0), min(i + 1, len(bounds) - 1)
        if spans and lo <= spans[-1][1] + 1:
            spans[-1][1] = max(spans[-1][1], hi)
        else:
            spans.append([lo, hi])
    out = []
    for lo, hi in spans:
        s, e = bounds[lo][0], bounds[hi][1]
        if e - s > MAX_WINDOW:  # one run-on "sentence": clip around matches, snap to spaces
            pieces = []
            for m in ANY_RE.finditer(content, s, e):
                a, b = max(m.start() - CLIP_PAD, s), min(m.end() + CLIP_PAD, e)
                if pieces and a <= pieces[-1][1]:
                    pieces[-1][1] = b
                else:
                    pieces.append([a, b])
            for a, b in pieces:
                if a > s:
                    a = content.find(" ", a, b) + 1 or a
                if b < e:
                    b = content.rfind(" ", a, b) if content.rfind(" ", a, b) > a else b
                out.append((a, b))
        else:
            out.append((s, e))
    res = []
    for s, e in out:
        seg = content[s:e]
        fam = sorted(k for k, r in TERM_RE.items() if r.search(seg))
        if fam:
            res.append((s, e, fam))
    return res


def cmd_build() -> int:
    src = source_path()
    if not src.exists():
        sys.exit("source parquet missing: run `fetch` first")
    sp = CORPUS / "sp500-constituents.tsv"
    con = duckdb.connect()
    con.execute("SET threads=8")
    con.execute(f"CREATE TABLE sp AS SELECT * FROM read_csv('{sp}', delim='\t', header=true, all_varchar=true)")
    con.execute(f"CREATE VIEW src AS SELECT * FROM '{src}'")

    # Speaker-role heuristic over the WHOLE dataset: sell-side analysts appear on many
    # issuers' calls; executives on one or two. Stored as a heuristic, never as fact.
    con.execute("""
      CREATE TABLE spk AS
      SELECT speaker, count(DISTINCT symbol) AS n_issuers
      FROM (SELECT symbol, unnest(transcripts).speaker AS speaker FROM src)
      WHERE speaker IS NOT NULL GROUP BY 1""")

    # S&P calls, with a content hash to collapse share-class duplicates (GOOG/GOOGL).
    con.execute("""
      CREATE TABLE calls AS
      SELECT s.symbol, s.fiscal_year, s.fiscal_quarter, s.report_date,
             len(s.transcripts) AS n_paragraphs,
             md5(string_agg(t.content, chr(10) ORDER BY t.paragraph_number)) AS call_md5
      FROM src s SEMI JOIN sp USING (symbol),
           LATERAL (SELECT unnest(s.transcripts, recursive := true)) t
      GROUP BY ALL""")
    con.execute("""
      CREATE TABLE canon AS
      SELECT *, CASE WHEN n_paragraphs > 2 THEN first_value(symbol) OVER w ELSE symbol END AS canonical_symbol
      FROM calls
      -- Same quarter, identical text: one call listed under two share classes.
      -- Stub transcripts (<=2 paragraphs) repeat across unrelated issuers; never merged.
      WINDOW w AS (PARTITION BY call_md5, fiscal_year, fiscal_quarter ORDER BY symbol)""")

    rows = con.execute(f"""
      SELECT s.symbol, s.fiscal_year, s.fiscal_quarter, s.report_date,
             t.paragraph_number, t.speaker, t.content, coalesce(k.n_issuers, 0)
      FROM src s SEMI JOIN sp USING (symbol),
           LATERAL (SELECT unnest(s.transcripts, recursive := true)) t
      LEFT JOIN spk k ON k.speaker = t.speaker
      WHERE regexp_matches(t.content, '{ANY.replace("'", "''")}')
      """).fetchall()

    canon = {(r[0], r[1], r[2]): r[3] for r in
             con.execute("SELECT symbol, fiscal_year, fiscal_quarter, canonical_symbol FROM canon").fetchall()}
    paras, wins = [], []
    for sym, fy, fq, rdate, pn, spkr, content, n_iss in rows:
        if canon[(sym, fy, fq)] != sym:
            continue  # duplicate share-class listing of an identical call
        ws = windows_for(content)
        if not ws:
            continue
        role = "operator" if (spkr or "").strip().lower() == "operator" else (
            "analyst_heuristic" if n_iss >= 3 else "issuer_heuristic")
        ph = b3(content)
        paras.append((sym, fy, fq, rdate, pn, spkr, role, n_iss, ph, content))
        for s, e, fam in ws:
            seg = content[s:e]
            wid = b3(f"{sym}|{fy}|{fq}|{pn}|{s}|{e}|{ph}")[:16]
            wins.append((wid, sym, fy, fq, rdate, pn, spkr, role, ph, s, e, b3(seg), ",".join(fam), seg))
    paras.sort(key=lambda r: (r[0], r[1], r[2], r[4]))
    wins.sort(key=lambda r: (r[1], r[2], r[3], r[5], r[9]))

    con.execute("""CREATE TABLE p (symbol VARCHAR, fiscal_year INT, fiscal_quarter INT, report_date VARCHAR,
                   paragraph_number INT, speaker VARCHAR, role VARCHAR, speaker_issuers INT,
                   paragraph_blake3 VARCHAR, content VARCHAR)""")
    con.executemany("INSERT INTO p VALUES (?,?,?,?,?,?,?,?,?,?)", paras)
    con.execute("""CREATE TABLE w (window_id VARCHAR, symbol VARCHAR, fiscal_year INT, fiscal_quarter INT,
                   report_date VARCHAR, paragraph_number INT, speaker VARCHAR, role VARCHAR,
                   paragraph_blake3 VARCHAR, start_char INT, end_char INT, window_blake3 VARCHAR,
                   term_families VARCHAR, text VARCHAR)""")
    con.executemany("INSERT INTO w VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", wins)
    if con.execute("SELECT count(*) - count(DISTINCT window_id) FROM w").fetchone()[0]:
        sys.exit("window_id collision")
    opts = "(FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 8192)"
    p_order = "ORDER BY symbol, fiscal_year, fiscal_quarter, paragraph_number"
    w_order = "ORDER BY symbol, fiscal_year, fiscal_quarter, paragraph_number, start_char"
    # Full tables, text included, into the gitignored bulk dir (byte-identical to the tables
    # committed before 2026-11-04, whose BLAKE3 the witness run records cite).
    BULK.mkdir(exist_ok=True)
    con.execute(f"COPY (SELECT * FROM p {p_order}) TO '{ect.PARAGRAPHS_TEXT}' {opts}")
    con.execute(f"COPY (SELECT * FROM w {w_order}) TO '{ect.WINDOWS_TEXT}' {opts}")
    # Committed tables: ids, metadata, offsets and hashes; no text.
    con.execute(f"COPY (SELECT * EXCLUDE (content) FROM p {p_order}) TO '{ect.PARAGRAPHS}' {opts}")
    con.execute(f"COPY (SELECT * EXCLUDE (text) FROM w {w_order}) TO '{ect.WINDOWS}' {opts}")

    # Denominators: every S&P call, AI or not.
    con.execute("""
      CREATE TABLE ai_by_call AS SELECT symbol, fiscal_year, fiscal_quarter,
             count(DISTINCT paragraph_number) AS n_ai_paragraphs, count(*) AS n_ai_windows
      FROM w GROUP BY ALL""")
    con.execute(f"""
      COPY (SELECT c.symbol, c.fiscal_year, c.fiscal_quarter, c.report_date, c.n_paragraphs,
                   CASE WHEN c.canonical_symbol <> c.symbol THEN c.canonical_symbol ELSE '' END AS duplicate_of,
                   coalesce(a.n_ai_paragraphs, 0) AS n_ai_paragraphs, coalesce(a.n_ai_windows, 0) AS n_ai_windows
            FROM canon c LEFT JOIN ai_by_call a USING (symbol, fiscal_year, fiscal_quarter)
            ORDER BY 1, 2, 3)
      TO '{CORPUS / 'calls.tsv'}' (HEADER, DELIMITER '\t')""")
    n = con.execute("SELECT count(*), count(*) FILTER (WHERE duplicate_of IS NULL OR duplicate_of = '') FROM read_csv('" + str(CORPUS / 'calls.tsv') +
                    "', delim='\t', header=true)").fetchone()
    print(f"ok: {n[0]} S&P calls ({n[1]} unique), {len(paras)} AI paragraphs, {len(wins)} windows")
    return cmd_verify()


# ---------------------------------------------------------------- verify
def source_paragraphs(con: duckdb.DuckDBPyConnection, keys: str) -> dict[tuple, str]:
    """{(symbol, fiscal_year, fiscal_quarter, paragraph_number): content} from the pinned source,
    for the keys in table `keys` (columns symbol, fiscal_year, fiscal_quarter, paragraph_number)."""
    src = source_path()
    if not src.exists():
        sys.exit("source parquet missing: run `uv run scripts/ec_extract.py fetch` first")
    rows = con.execute(f"""
        SELECT x.* FROM (
          SELECT s.symbol, s.fiscal_year, s.fiscal_quarter, t.paragraph_number, t.content
          FROM '{src}' s SEMI JOIN (SELECT DISTINCT symbol, fiscal_year, fiscal_quarter FROM {keys}) c
               USING (symbol, fiscal_year, fiscal_quarter),
               LATERAL (SELECT unnest(s.transcripts, recursive := true)) t) x
        SEMI JOIN {keys} k USING (symbol, fiscal_year, fiscal_quarter, paragraph_number)""").fetchall()
    out = {(r[0], r[1], r[2], r[3]): r[4] for r in rows}
    if len(out) != len(rows):
        sys.exit("source has duplicate paragraph keys")
    return out


def cmd_verify() -> int:
    """Re-slice every window from the pinned source and re-hash it: the committed tables carry
    no text, so this is the only check that they still point at the words they name. Then check
    the local bulk text tables, if built, against the committed hashes."""
    con = duckdb.connect()
    con.execute("SET threads=8")
    con.execute(f"CREATE TABLE p AS SELECT * FROM '{ect.PARAGRAPHS}'")
    con.execute(f"CREATE TABLE w AS SELECT * FROM '{ect.WINDOWS}'")
    text = source_paragraphs(con, "p")
    bad = 0
    paras = {}
    for sym, fy, fq, pn, ph in con.execute(
            "SELECT symbol, fiscal_year, fiscal_quarter, paragraph_number, paragraph_blake3 FROM p").fetchall():
        k = (sym, fy, fq, pn)
        c = text.get(k)
        if c is None or b3(c) != ph:
            bad += 1
            print(f"FAIL paragraph {k}: missing from source or hash differs")
        paras[k] = (ph, c)
    n = 0
    for wid, sym, fy, fq, pn, ph, s, e, wh in con.execute(
            "SELECT window_id, symbol, fiscal_year, fiscal_quarter, paragraph_number, paragraph_blake3, "
            "start_char, end_char, window_blake3 FROM w").fetchall():
        n += 1
        p = paras.get((sym, fy, fq, pn))
        if (p is None or p[1] is None or p[0] != ph or b3(p[1][s:e]) != wh
                or b3(f"{sym}|{fy}|{fq}|{pn}|{s}|{e}|{ph}")[:16] != wid):
            bad += 1
            print(f"FAIL window {wid}")
    print(f"{'ok' if not bad else 'FAIL'}: {len(paras)} paragraphs, {n} windows re-sliced from the pinned source "
          f"and re-hashed, {bad} bad")
    # Local text tables (gitignored): same rows as the committed tables, text matching each hash.
    if ect.PARAGRAPHS_TEXT.exists() and ect.WINDOWS_TEXT.exists():
        local_bad = con.execute(f"""
          SELECT (SELECT count(*) FROM p FULL JOIN '{ect.PARAGRAPHS_TEXT}' x
                    USING (symbol, fiscal_year, fiscal_quarter, paragraph_number)
                  WHERE x.paragraph_blake3 IS DISTINCT FROM p.paragraph_blake3)
               + (SELECT count(*) FROM w FULL JOIN '{ect.WINDOWS_TEXT}' x USING (window_id)
                  WHERE x.window_blake3 IS DISTINCT FROM w.window_blake3)""").fetchone()[0]
        for ph, c in con.execute(f"SELECT paragraph_blake3, content FROM '{ect.PARAGRAPHS_TEXT}'").fetchall():
            local_bad += b3(c) != ph
        for wh, t in con.execute(f"SELECT window_blake3, text FROM '{ect.WINDOWS_TEXT}'").fetchall():
            local_bad += b3(t) != wh
        print(f"{'ok' if not local_bad else 'FAIL'}: local text tables in {BULK.name}/, {local_bad} bad")
        bad += local_bad
    else:
        print(f"note: no local text tables in {BULK.name}/ (run `build` to write them)")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["fetch", "constituents", "build", "verify"])
    a = ap.parse_args()
    return {"fetch": cmd_fetch, "constituents": cmd_constituents, "build": cmd_build, "verify": cmd_verify}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb>=1.0", "blake3>=1.0"]
# ///
"""Corpus-level queries over the Item 1A store.

Everything here reads the anchored spans built by rf_extract.py and returns
**verbatim text with a hash**, never a summary or a score. A row that cannot be
re-sliced from its blob is not returned.

    uv run scripts/rf_query.py coverage
    uv run scripts/rf_query.py mentions "supply chain" --min-companies 20
    uv run scripts/rf_query.py phrase "rare earth"
    uv run scripts/rf_query.py risks --symbol AAPL

Coverage is printed beside every result. A phrase found in 300 filings means
nothing until it is read against the 80,592 that were not searched or that
failed to extract.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

import blake3
import duckdb

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".rfcorpus"
DB = OUT / "rf.duckdb"
BLOBS = OUT / "blobs"


def blob(h: str) -> str:
    return gzip.decompress((BLOBS / f"{h}.txt.gz").read_bytes()).decode("utf-8")


def _con():
    return duckdb.connect(str(DB), read_only=True)


def cmd_coverage(_a) -> int:
    con = _con()
    total = con.execute("SELECT count(*) FROM filings").fetchone()[0]
    n = con.execute("SELECT count(*) FROM item_1a").fetchone()[0]
    print(f"filings in scope : {total:,}")
    print(f"spans extracted  : {n:,}")
    print(f"coverage         : {n / total:.1%}")
    print("\nby method:")
    for m, c in con.execute(
            "SELECT method, count(*) FROM item_1a GROUP BY 1 ORDER BY 2 DESC").fetchall():
        print(f"  {m:22s} {c:7,}")
    print("\nby filing year:")
    for y, c in con.execute(
            "SELECT year(filing_date), count(*) FROM item_1a GROUP BY 1 ORDER BY 1").fetchall():
        print(f"  {y}  {c:,}")
    print("\ndistinct companies:", con.execute(
        "SELECT count(DISTINCT cik) FROM item_1a").fetchone()[0])
    con.close()
    return 0


def cmd_mentions(a) -> int:
    """Which companies name a phrase, and how often — never why or how much."""
    con = _con()
    rows = con.execute(
        "SELECT symbol, company_name, cik, filing_date, text_blake3 "
        "FROM item_1a WHERE method <> 'not-applicable'").fetchall()
    pat = re.compile(re.escape(a.phrase), re.IGNORECASE)
    hits: dict[str, dict] = {}
    for sym, name, cik, fdate, h in rows:
        txt = blob(h)
        n = len(pat.findall(txt))
        if n < a.min_mentions:
            continue
        d = hits.setdefault(cik, {"symbol": sym, "name": name, "cik": cik,
                                  "filings": 0, "mentions": 0, "last": None})
        d["filings"] += 1
        d["mentions"] += n
        d["last"] = max(d["last"] or "", str(fdate))
    con.close()
    out = sorted(hits.values(), key=lambda d: -d["mentions"])
    out = [d for d in out if d["filings"] >= a.min_companies] if a.min_companies else out
    print(f"scanned {len(rows):,} spans; {len(out):,} companies mention "
          f"{a.phrase!r} in >= {a.min_mentions} place(s)")
    for d in out[:a.limit]:
        print(f"  {d['symbol'] or '-':10s} {d['filings']:3d} filings/"
              f"{d['mentions']:5d} hits  last {d['last']}  {d['name'][:44]}")
    return 0


def cmd_phrase(a) -> int:
    """Every verbatim occurrence, with its filing and hash. No interpretation."""
    con = _con()
    pat = re.compile(re.escape(a.phrase), re.IGNORECASE)
    rows = con.execute(
        "SELECT symbol, filing_date, text_blake3 FROM item_1a "
        "WHERE method <> 'not-applicable'").fetchall()
    shown = 0
    for sym, fdate, h in rows:
        txt = blob(h)
        for m in pat.finditer(txt):
            if shown >= a.limit:
                break
            lo, hi = max(0, m.start() - a.context), min(len(txt), m.end() + a.context)
            print(f"\n[{sym} {fdate}]  blake3:{h[:16]}")
            print("  ..." + txt[lo:hi].replace("\n", " ") + "...")
            shown += 1
        if shown >= a.limit:
            break
    print(f"\n{shown} occurrence(s) shown; scanned {len(rows):,} spans")
    con.close()
    return 0


def cmd_risks(a) -> int:
    """The stored Item 1A for one symbol — the raw material, unread."""
    con = _con()
    rows = con.execute(
        "SELECT filing_date, method, char_count, text_blake3 FROM item_1a "
        "WHERE symbol = ? ORDER BY filing_date", [a.symbol]).fetchall()
    if not rows:
        print(f"no stored span for {a.symbol}", file=sys.stderr)
        return 1
    for fdate, method, chars, h in rows:
        print(f"{fdate}  {method:20s} {chars:>8,} chars  blake3:{h}")
    con.close()
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("coverage").set_defaults(fn=cmd_coverage)
    m = sub.add_parser("mentions")
    m.add_argument("phrase")
    m.add_argument("--min-mentions", type=int, default=1)
    m.add_argument("--min-companies", type=int, default=0)
    m.add_argument("--limit", type=int, default=30)
    m.set_defaults(fn=cmd_mentions)
    ph = sub.add_parser("phrase")
    ph.add_argument("phrase")
    ph.add_argument("--context", type=int, default=120)
    ph.add_argument("--limit", type=int, default=10)
    ph.set_defaults(fn=cmd_phrase)
    r = sub.add_parser("risks")
    r.add_argument("symbol")
    r.set_defaults(fn=cmd_risks)
    a = p.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())

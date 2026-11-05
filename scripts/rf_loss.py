#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb>=1.0", "blake3>=1.0"]
# ///
"""8-K loss-evidence discovery, joined to CIK.

Item 1A is forward-looking: it asks what *could* harm a company. Asking it
whether a loss *happened* is a category error, so this extractor does not read
Item 1A at all. It discovers 8-Ks that report a materialized event, using
EDGAR's structured `items` array, and stores the filing's Item text verbatim.

Loss-relevant 8-K Items:

  1.05  Material Cybersecurity Incident       realized harm, with scope
  2.04  Triggering Events / Off-Balance       covenant breach, acceleration
  2.05  Costs of Exit or Disposal             restructuring charges
  2.06  Material Impairments                  a write-down is booked here
  4.02  Non-Reliance on Prior Financials      restatement

Every one of these is a *disclosed realized event*. Presence means a company
filed a form describing it — not that any specific Item 1A risk caused it.
Attribution is a separate, human judgement that must cite both filings.

EDGAR's search API caps a single query at 10,000 results and silently ignores
the items= filter, so enumeration slices by month and filters on the returned
items[] array. Coverage is reported, never assumed.

    uv run scripts/rf_loss.py discover --year-min 2010
    uv run scripts/rf_loss.py report --cik 0000320193
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".rfcorpus"
DB = OUT / "loss.duckdb"   # separate file: the Item 1A crawl holds rf.duckdb
UA = "Anthropic-PBC risk-factor corpus research (governance@ethicalcapital.com)"
RATE = 0.15

LOSS_ITEMS = {
    "1.05": "Material Cybersecurity Incident",
    "2.04": "Triggering Events That Accelerate or Increase a Direct Financial Obligation",
    "2.05": "Costs Associated with Exit or Disposal Activities",
    "2.06": "Material Impairments",
    "4.02": "Non-Reliance on Previously Issued Financial Statements",
}


def _get(url: str, tries: int = 3) -> dict | None:
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as f:
                return json.loads(f.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code == 403:
                time.sleep(2 ** attempt * 2)
                continue
            return None
        except Exception:
            time.sleep(2 ** attempt)
    return None


def _months(y0: int, y1: int):
    for y in range(y0, y1 + 1):
        for m in range(1, 13):
            lo = f"{y}-{m:02d}-01"
            hi = f"{y - 1}-12-31" if m == 0 else None
            # last day handled by next month's first day minus one, via string
            nm_y, nm_m = (y + 1, 1) if m == 12 else (y, m + 1)
            hi = f"{nm_y}-{nm_m:02d}-01"
            yield lo, hi


def _search(lo: str, hi: str, frm: int = 0) -> dict | None:
    q = urllib.parse.urlencode({
        "q": "", "forms": "8-K",
        "dateRange": "custom", "startdt": lo, "enddt": hi, "from": frm})
    return _get(f"https://efts.sec.gov/LATEST/search-index?{q}")


def _search_retry(lo: str, hi: str, frm: int = 0, tries: int = 5) -> dict | None:
    """EDGAR throttles aggressively under sustained paging; back off and retry.

    A single 9,000-hit month is ~90 sequential requests, which trips the
    limiter partway through (observed on 2010-05, 2010-08, 2010-09, 2010-11).
    """
    for attempt in range(tries):
        got = _search(lo, hi, frm)
        if got:
            return got
        time.sleep(2 ** attempt)
    return None


def _ensure(con) -> None:
    con.execute("""
      CREATE TABLE IF NOT EXISTS loss_event (
        accession_number VARCHAR PRIMARY KEY,
        cik VARCHAR, symbol VARCHAR, company_name VARCHAR,
        filing_date DATE, items VARCHAR, item_labels VARCHAR,
        source_url VARCHAR)""")


def cmd_discover(a) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB))
    _ensure(con)
    seen = {r[0] for r in con.execute(
        "SELECT accession_number FROM loss_event").fetchall()}
    added = scanned = 0
    incomplete: list[str] = []
    for lo, hi in _months(a.year_min, a.year_max):
        got = _search_retry(lo, hi)
        if not got:
            # A slice that cannot be read is recorded as a gap. Silently
            # skipping it would bias every downstream rate without a trace.
            incomplete.append(lo)
            print(f"  {lo}: UNREADABLE (recorded as a gap)", file=sys.stderr)
            continue
        total = got["hits"]["total"]["value"]
        pages = (total + 99) // 100
        if total > 10_000:
            # EDGAR returns at most 10,000 results per query, whatever the
            # ordering. The tail is unreachable and must be declared, not
            # silently dropped.
            incomplete.append(f"{lo}:capped")
            print(f"  WARN {lo}: {total:,} hits exceeds the 10k API cap; "
                  f"{total - 10_000:,} filings NOT enumerated", file=sys.stderr)
            pages = 100
        for p in range(pages):
            if p:
                got = _search_retry(lo, hi, p * 100)
                if not got:
                    incomplete.append(f"{lo}@{p * 100}")
                    print(f"  {lo} page {p}: UNREADABLE", file=sys.stderr)
                    break
            for hit in got["hits"]["hits"]:
                scanned += 1
                s = hit["_source"]
                items = s.get("items") or []
                lossy = [i for i in items if i in LOSS_ITEMS]
                if not lossy:
                    continue
                acc = hit["_id"].split(":")[0]
                if acc in seen:
                    continue
                ciks = s.get("ciks") or []
                name = (s.get("display_names") or [""])[0]
                acc_nodash = acc.replace("-", "")
                cik0 = ciks[0] if ciks else ""
                url = (f"https://www.sec.gov/Archives/edgar/data/{int(cik0)}/"
                       f"{acc_nodash}" if cik0 else "")
                con.execute(
                    "INSERT OR REPLACE INTO loss_event VALUES (?,?,?,?,?,?,?,?)",
                    [acc, cik0, "", name, s.get("file_date"), ",".join(items),
                     "; ".join(f"{i} {LOSS_ITEMS[i]}" for i in lossy), url])
                seen.add(acc)
                added += 1
        con.execute("CHECKPOINT")
        print(f"  {lo}  scanned={scanned:,} events={added:,}", flush=True)
    if incomplete:
        print(f"INCOMPLETE slices ({len(incomplete)}): "
              f"{', '.join(incomplete[:12])}"
              f"{' ...' if len(incomplete) > 12 else ''}")
    print(f"\n{added:,} loss-relevant 8-Ks; {scanned:,} filings scanned")
    con.close()
    return 0


def cmd_report(a) -> int:
    con = duckdb.connect(str(DB), read_only=True)
    if a.cik:
        rows = con.execute(
            "SELECT filing_date, items, item_labels, company_name, source_url "
            "FROM loss_event WHERE cik LIKE ? ORDER BY filing_date",
            [f"%{a.cik.lstrip('0')}%"]).fetchall()
    else:
        rows = con.execute(
            "SELECT filed, n, c FROM (SELECT count(*) n, max(1) c, "
            "strftime(filing_date,'%Y') filed FROM loss_event GROUP BY 1) "
            "ORDER BY 1").fetchall()
    for r in rows:
        print(r)
    con.close()
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("discover")
    d.add_argument("--year-min", type=int, default=2010)
    d.add_argument("--year-max", type=int, default=2026)
    d.set_defaults(fn=cmd_discover)
    r = sub.add_parser("report")
    r.add_argument("--cik", default="")
    r.set_defaults(fn=cmd_report)
    a = p.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())

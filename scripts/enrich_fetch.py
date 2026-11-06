#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["blake3>=1.0"]
# ///
"""Stage 0 fetch: hash-pin every enrichment source (bert-enrichment-spec §7).

Fetch is a separate, deliberate, recorded step; nothing downstream touches
the network. The fetch date is an argument, never read from the clock.

    uv run scripts/enrich_fetch.py --fetched 2026-11-04
    uv run scripts/enrich_fetch.py verify

Writes sources/<id>.<ext> (untouched bytes) and sources/MANIFEST.tsv with
columns: id, role, fetched, url, path, bytes, blake3. `verify` re-hashes
every file against the manifest and fails on any mismatch.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

import blake3

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "sources"
UA = "Anthropic-PBC enrichment research (governance@ethicalcapital.com)"

FIXED = [
    ("anthropic-report", "case",
     "https://www-cdn.anthropic.com/a9ceec76a54d28d27affffcdab6faf7c142cd587.pdf",
     "pbc-report-2026.pdf"),
    ("anthropic-s1a1", "case",
     "https://www.sec.gov/Archives/edgar/data/2130357/000162828026068676/anthropicpbc-sx1ax1.htm",
     "s1a1.htm"),
    ("anthropic-constitution", "case",
     "https://www.anthropic.com/constitution", "constitution.html"),
]
# Resolved from EDGAR submissions at fetch time; the resolved URL is what
# lands in the manifest, so the pin is exact.
EDGAR = [
    ("peer-coreweave-s1", "peer-nonpbc", 1769628, ("S-1/A", "S-1"), "peer-coreweave-s1.htm"),
    ("comparator-lemonade-10k", "comparator-pbc", 1691421, ("10-K",), "comparator-lemonade-10k.htm"),
]


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180) as f:
        return f.read()


def edgar_latest(cik: int, forms: tuple[str, ...]) -> tuple[str, str]:
    sub = json.loads(_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))
    blocks = [sub["filings"]["recent"]]
    # Older filings (e.g. a 2025 S-1 behind a wall of Form 4s) live in
    # per-CIK shard files, not in `recent`.
    for extra in sub["filings"].get("files", []):
        blocks.append(json.loads(
            _get(f"https://data.sec.gov/submissions/{extra['name']}")))
    for block in blocks:
        for i, form in enumerate(block["form"]):
            if form in forms:
                acc = block["accessionNumber"][i].replace("-", "")
                doc = block["primaryDocument"][i]
                return f"{sub['name']} {form} {block['filingDate'][i]}", \
                       f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
    raise SystemExit(f"no {forms} found for CIK {cik}")


def cmd_fetch(a) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    jobs = [(i, r, u, p, i) for (i, r, u, p) in FIXED]
    for (i, r, cik, forms, p) in EDGAR:
        label, url = edgar_latest(cik, forms)
        print(f"resolved {i}: {label}")
        jobs.append((i, r, url, p, label))
    for (doc_id, role, url, path, _label) in jobs:
        data = _get(url)
        (OUT / path).write_bytes(data)
        digest = blake3.blake3(data).hexdigest()
        rows.append([doc_id, role, a.fetched, url, path, str(len(data)), digest])
        print(f"fetched {doc_id}: {len(data):,} bytes blake3:{digest[:16]}…")
    manifest = ["id\trole\tfetched\turl\tpath\tbytes\tblake3"]
    manifest += ["\t".join(r) for r in rows]
    (OUT / "MANIFEST.tsv").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print(f"wrote {OUT / 'MANIFEST.tsv'} ({len(rows)} sources)")
    return 0


def cmd_verify(_a) -> int:
    bad = 0
    lines = (OUT / "MANIFEST.tsv").read_text(encoding="utf-8").strip().splitlines()[1:]
    for line in lines:
        doc_id, _r, _f, _u, path, nbytes, digest = line.split("\t")
        p = OUT / path
        if not p.exists():
            print(f"MISSING {doc_id} {path}"); bad += 1; continue
        data = p.read_bytes()
        if len(data) != int(nbytes) or blake3.blake3(data).hexdigest() != digest:
            print(f"MISMATCH {doc_id} {path}"); bad += 1
    print(f"verified {len(lines)} sources; {bad} bad")
    return 1 if bad else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fetched", default="2026-11-04",
                   help="recorded fetch date (input, never the clock)")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("fetch").set_defaults(fn=cmd_fetch)
    sub.add_parser("verify").set_defaults(fn=cmd_verify)
    a = p.parse_args()
    return a.fn(a) if a.cmd else cmd_fetch(a)


if __name__ == "__main__":
    raise SystemExit(main())

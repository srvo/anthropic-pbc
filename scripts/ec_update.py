#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb==2.0.0"]
# ///
"""Continuous updates for dewey.earnings_calls.transcripts.

Upstream (defeatbeta/yahoo-finance-data on Hugging Face) republishes the
whole transcript parquet under new dataset commits; there is no upstream
delta feed. This script turns each new commit into one immutable delta
member for the Dewey store, so an update uploads megabytes, not 2.3 GB:

    uv run scripts/ec_update.py check    # upstream head vs local pin (API only)
    uv run scripts/ec_update.py update   # fetch, diff, write delta, extend registry

Delta semantics: rows keyed by (symbol, fiscal_year, fiscal_quarter).
A delta parquet holds every call that is new upstream plus every call
whose content changed since the previous snapshot. Consumers union the
base member with all delta members and keep, per key, the row from the
newest member (members are admitted in revision order; the manifest is
the order of record). The previous snapshot stays in .eccorpus/ until
the delta is admitted and verified; nothing here deletes it.

The registry step extends the earnings_calls.transcripts manifest and
stores.json in the Dark checkout (--stores-dir). Ingest stays the
governed command, printed at the end; this script never touches Dewey.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
BULK = ROOT / ".eccorpus"
ENTRY = "earnings_calls.transcripts"
HF_API = "https://huggingface.co/api/datasets/defeatbeta/yahoo-finance-data"
HF_FILE = "data/US/stock_earning_call_transcripts.parquet"
UA = {"User-Agent": "praxis-earnings-calls-updater/1.0"}


def head_revision() -> tuple[str, str]:
    req = urllib.request.Request(HF_API, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return data["sha"], data.get("lastModified", "")


def local_pin() -> tuple[str, Path] | None:
    """(revision, parquet) of the newest local snapshot, if any."""
    snaps = list(BULK.glob("stock_earning_call_transcripts.*.parquet"))
    if not snaps:
        return None
    path = max(snaps, key=lambda p: p.stat().st_mtime)  # newest download, not lexical
    return path.name.split(".")[1], path


def download(revision: str, dest: Path) -> None:
    url = f"https://huggingface.co/datasets/defeatbeta/yahoo-finance-data/resolve/{revision}/{HF_FILE}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as resp, dest.open("wb") as fh:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while chunk := resp.read(1 << 20):
            fh.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {done/total:.0%}", end="", flush=True)
    print(f"\n  wrote {dest} ({dest.stat().st_size:,} bytes)")


def delta(old: Path, new: Path, out: Path) -> dict:
    con = duckdb.connect()
    con.execute("SET preserve_insertion_order=false")
    key = "symbol, fiscal_year, fiscal_quarter"
    con.execute(f"""
        CREATE VIEW old_t AS SELECT *, hash(transcripts::VARCHAR) AS _h
        FROM read_parquet('{old}');
        CREATE VIEW new_t AS SELECT *, hash(transcripts::VARCHAR) AS _h
        FROM read_parquet('{new}');
    """)
    counts = {
        "old_calls": con.execute("SELECT count(*) FROM old_t").fetchone()[0],
        "new_calls": con.execute("SELECT count(*) FROM new_t").fetchone()[0],
    }
    con.execute(f"""
        COPY (
            SELECT new_t.symbol, new_t.fiscal_year, new_t.fiscal_quarter,
                   new_t.report_date, new_t.transcripts_id, new_t.transcripts
            FROM new_t LEFT JOIN old_t USING ({key})
            WHERE old_t.symbol IS NULL OR old_t._h <> new_t._h
            ORDER BY new_t.symbol, new_t.fiscal_year, new_t.fiscal_quarter
        ) TO '{out}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    counts["delta_calls"] = con.execute(f"SELECT count(*) FROM read_parquet('{out}')").fetchone()[0]
    counts["delta_symbols"] = con.execute(f"SELECT count(DISTINCT symbol) FROM read_parquet('{out}')").fetchone()[0]
    return counts


def extend_registry(stores_dir: Path, delta_path: Path, revision: str, modified: str) -> None:
    stores_json = stores_dir / "stores.json"
    data = json.loads(stores_json.read_text())
    entry = data["stores"][ENTRY]
    # Store dir in the registry is the corpus checkout's .eccorpus; delta
    # members live there beside the base parquet, under updates/.
    rel = f"updates/{delta_path.name}"
    dest_dir = BULK / "updates"
    dest_dir.mkdir(exist_ok=True)
    dest = dest_dir / delta_path.name
    if delta_path != dest and delta_path.exists():
        delta_path.replace(dest)
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    size = dest.stat().st_size
    manifest_path = stores_dir / entry["manifest"]
    lines = manifest_path.read_text().splitlines()
    if any(rel in ln for ln in lines):
        raise SystemExit(f"{rel} already in manifest; refusing to double-register")
    lines.append(f"{digest}\t{size}\t{rel}")
    manifest_path.write_text("\n".join(lines) + "\n")
    entry["files"] = len(lines) - 1
    entry["bytes"] = sum(int(ln.split("\t")[1]) for ln in lines[1:])
    entry["manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    entry["source_pin"] = (
        f"defeatbeta/yahoo-finance-data base @31ee0261 + delta {revision[:8]} "
        f"(upstream lastModified {modified}); base carved from standalone.eccorpus "
        "manifest 2026-11-13, member digests unchanged"
    )
    entry["source"] = (
        "defeatbeta/yahoo-finance-data table stock_earning_call_transcripts: base "
        "snapshot @31ee0261 (240,536 calls, 6,592 symbols, FY2005-2027) plus one "
        "immutable delta member per upstream commit thereafter (new + changed calls, "
        "keyed by symbol/fiscal_year/fiscal_quarter; newest member wins per key). "
        "Updated by scripts/ec_update.py."
    )
    stores_json.write_text(json.dumps(data, indent=1) + "\n")
    print(f"registry: +{rel} ({size:,} bytes) -> {manifest_path.name}; files={entry['files']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["check", "update"])
    ap.add_argument("--stores-dir", type=Path,
                    default=Path.home() / "dev/dark-monocloud/anthropic-pbc/stores")
    args = ap.parse_args()

    revision, modified = head_revision()
    pin = local_pin()
    print(f"upstream head: {revision[:8]} (lastModified {modified})")
    print(f"local pin:     {pin[0][:8] if pin else 'none'}")
    if args.cmd == "check":
        print("update available" if not pin or pin[0] != revision[:8] else "up to date")
        return 0
    if pin and pin[0] == revision[:8]:
        print("up to date; nothing to do")
        return 0
    if pin is None:
        raise SystemExit("no local snapshot in .eccorpus/; restore the base member from Dewey first")

    new_path = BULK / f"stock_earning_call_transcripts.{revision[:8]}.parquet"
    if not new_path.exists():
        download(revision, new_path)
    delta_path = BULK / f"delta-{revision[:8]}.parquet"
    counts = delta(pin[1], new_path, delta_path)
    print(json.dumps(counts, indent=1))
    extend_registry(args.stores_dir, delta_path, revision, modified)
    print("\nnext (governed ingest + verify):")
    print("  cd ~/dev/dark-monocloud && bws run -- mise run dewey:ingest -- ingest \\")
    print(f"    --stores anthropic-pbc/stores/stores.json --entry {ENTRY} \\")
    print("    --root standalone=$HOME/dev/anthropic-pbc --run-dir /tmp/dewey-runs/earnings-update")
    print("then the same with dewey:verify. Keep the previous snapshot until verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

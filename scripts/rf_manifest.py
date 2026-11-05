#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb==2.0.0", "pyyaml==6.0.3"]
# ///
"""Generate and verify risk-factor pins AND metadata from retained local records.

    uv run scripts/rf_manifest.py write
    uv run scripts/rf_manifest.py check
    uv run scripts/rf_manifest.py coverage

Authored methods/rights and recorded pin parameters: corpus/risk-factors/metadata.source.yml.
Both outputs are deterministic; check compares their complete bytes without writing.
This audits record metadata, not blob bytes, acquisition completeness or source rights.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import duckdb
import yaml

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus/risk-factors"
MANIFEST = CORPUS / "MANIFEST.tsv"
METADATA = CORPUS / "MANIFEST.meta.yml"
SOURCE = CORPUS / "metadata.source.yml"
RF_DB = ROOT / ".rfcorpus/rf.duckdb"
LOSS_DB = ROOT / ".rfcorpus/loss.duckdb"
FIELDS = ["id", "role", "pinned", "url", "path", "bytes", "sha256", "revision", "note"]
GENERATOR_VERSION = "rf-manifest-v2"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def records_sha(rows: list) -> str:
    return sha(
        json.dumps(
            rows, ensure_ascii=False, default=str, separators=(",", ":")
        ).encode()
    )


def load_source() -> tuple[dict, dict, bytes]:
    raw = SOURCE.read_bytes()
    source = yaml.safe_load(raw)
    if not isinstance(source, dict) or set(source) != {"pin", "metadata"}:
        raise ValueError("authored source must contain pin and metadata mappings")
    pin, meta = source["pin"], source["metadata"]
    if not isinstance(pin, dict) or set(pin) != {
        "date",
        "index_repo",
        "index_revision",
        "index_file",
    }:
        raise ValueError("incomplete or unknown pin parameters")
    if not all(isinstance(v, str) and v for v in pin.values()):
        raise ValueError("pin parameters must be nonempty strings")
    datetime.date.fromisoformat(pin["date"])
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", pin["index_revision"]):
        raise ValueError("index revision must be a full Git object id")
    if not isinstance(meta, dict):
        raise TypeError("authored metadata must be a mapping")
    reserved = {
        "description",
        "coverage",
        "date_accessed",
        "version_producer",
        "provenance",
        "files",
    }
    if reserved.intersection(meta):
        raise ValueError("authored source overrides generated fields")
    if list(meta["tables"]["corpus/risk-factors/MANIFEST.tsv"]["columns"]) != FIELDS:
        raise ValueError("authored column definitions disagree with manifest schema")
    return pin, meta, raw


def collect() -> dict:
    # Read each store in one transaction. No fetch, clock, host or blob reads.
    with duckdb.connect(str(RF_DB), read_only=True) as con:
        con.begin()
        filings = con.execute(
            "SELECT accession_number, d_filing FROM filings ORDER BY accession_number, d_filing"
        ).fetchall()
        spans = con.execute(
            "SELECT accession_number, text_blake3, cik, word_count, method "
            "FROM item_1a ORDER BY accession_number"
        ).fetchall()
        con.commit()
    with duckdb.connect(str(LOSS_DB), read_only=True) as con:
        events = con.execute(
            "SELECT accession_number, items, cik, filing_date FROM loss_event ORDER BY accession_number"
        ).fetchall()
    if any(not a or not d for a, d in filings):
        raise ValueError("filing accession/date missing")
    if len({r[0] for r in spans}) != len(spans) or len({r[0] for r in events}) != len(
        events
    ):
        raise ValueError("duplicate corpus accession")
    attempted = {a for a, _ in filings}
    for acc, digest, _, words, method in spans:
        if acc not in attempted:
            raise ValueError("stored span absent from attempted filings")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("missing or invalid stored text BLAKE3")
        if words is None or words < 0 or not method:
            raise ValueError("missing or invalid span statistics")
    if any(not acc or not items for acc, items, _, _ in events):
        raise ValueError("loss-event accession/items missing")
    ih = hashlib.sha256(b"risk-factor-item-1a-v1\n")
    for acc, digest, *_ in spans:
        ih.update(f"{acc}\t{digest}\n".encode())
    lh = hashlib.sha256(b"risk-factor-loss-events-v1\n")
    for acc, items, *_ in events:
        lh.update(f"{acc}\t{items}\n".encode())
    na = sum(r[4] == "not-applicable" for r in spans)
    dates = [str(r[1]) for r in filings]
    event_dates = [str(r[3]) for r in events if r[3] is not None]
    return {
        "item_sha256": ih.hexdigest(),
        "loss_sha256": lh.hexdigest(),
        "inputs_sha256": {
            "filings": records_sha(filings),
            "item_1a": records_sha(spans),
            "loss_event": records_sha(events),
        },
        "coverage": {
            "filings_attempted": len(filings),
            "spans_stored": len(spans),
            "distinct_texts": len({r[1] for r in spans}),
            "not_applicable": na,
            "substantive_spans": len(spans) - na,
            "companies": len({r[2] for r in spans if r[2] is not None}),
            "words": sum(r[3] for r in spans),
            "filing_date_min": min(dates, default=None),
            "filing_date_max": max(dates, default=None),
            "stored_percent": round(100 * len(spans) / len(filings), 1)
            if filings
            else None,
            "substantive_percent": round(100 * (len(spans) - na) / len(filings), 1)
            if filings
            else None,
            "loss_events": len(events),
            "loss_companies": len({r[2] for r in events if r[2] is not None}),
            "loss_filing_date_min": min(event_dates, default=None),
            "loss_filing_date_max": max(event_dates, default=None),
            "loss_discovery_completeness": "unknown: attempted-slice receipts not retained",
        },
    }


def expected_outputs() -> dict[Path, bytes]:
    pin, meta, authored = load_source()
    data = collect()
    c = data["coverage"]
    out = io.StringIO(newline="")
    writer = csv.writer(out, delimiter="\t", lineterminator="\n")
    writer.writerow(FIELDS)
    writer.writerows(
        [
            [
                "item_1a",
                "corpus",
                pin["date"],
                "https://www.sec.gov/search-filings",
                "",
                "",
                data["item_sha256"],
                "",
                (
                    f"{c['spans_stored']} spans; {c['distinct_texts']} distinct texts; "
                    f"{c['filings_attempted']} filings in scope ({c['filing_date_min']}..{c['filing_date_max']}); "
                    f"{c['companies']} companies; {c['words']} words; {c['not_applicable']} not-applicable"
                ),
            ],
            [
                "loss_events",
                "corpus",
                pin["date"],
                "https://www.sec.gov/edgar/searchedgar/fulltextsearch",
                "",
                "",
                data["loss_sha256"],
                "",
                (
                    f"{c['loss_events']} retained 8-K loss-relevant events; "
                    "EDGAR structured-items discovery; enumeration completeness unknown"
                ),
            ],
            [
                "edgar_index",
                "upstream",
                pin["date"],
                f"https://huggingface.co/datasets/{pin['index_repo']}",
                pin["index_file"],
                "",
                "",
                pin["index_revision"],
                "Filing index only; no filing text",
            ],
        ]
    )
    manifest = out.getvalue().encode()
    meta.update(
        {
            "description": f"Retained Item 1A records: {c['spans_stored']:,} spans from "
            f"{c['filings_attempted']:,} attempted filings, {c['substantive_spans']:,} substantive and "
            f"{c['not_applicable']:,} not-applicable; {c['words']:,} words. "
            f"Retained loss index: {c['loss_events']:,} events from {c['loss_companies']:,} companies. "
            "Rates and dates are recorded in coverage; loss enumeration completeness is unknown.",
            "coverage": c,
            "date_accessed": pin["date"],
            "version_producer": {
                "item_1a_sha256": data["item_sha256"],
                "loss_events_sha256": data["loss_sha256"],
                "index_revision": pin["index_revision"],
            },
            "files": "corpus/risk-factors/MANIFEST.tsv",
            "provenance": {
                "actor": f"script:{GENERATOR_VERSION}",
                "generator": "scripts/rf_manifest.py",
                "generator_sha256": sha(Path(__file__).read_bytes()),
                "prompt": "not_applicable",
                "parameters": pin,
                "authored_source_sha256": sha(authored),
                "record_inputs_sha256": data["inputs_sha256"],
                "manifest_sha256": sha(manifest),
                "scope": "Record metadata only; no blob or acquisition-completeness verification.",
            },
        }
    )
    metadata = (
        "# GENERATED by scripts/rf_manifest.py write; do not edit.\n"
        "# Authored inputs: corpus/risk-factors/metadata.source.yml\n"
        + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=88)
    ).encode()
    return {MANIFEST: manifest, METADATA: metadata}


def cmd_write(_a) -> int:
    outputs = (
        expected_outputs()
    )  # Fail before touching either output on invalid inputs.
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        print(f"wrote {path.name} sha256={sha(content)}")
    return 0


def cmd_check(_a) -> int:
    bad = 0
    for path, content in expected_outputs().items():
        if not path.exists() or path.read_bytes() != content:
            print(
                f"DRIFT {path.name}: missing or differs from deterministic rebuild",
                file=sys.stderr,
            )
            bad += 1
    print(
        f"checked both generated outputs; {bad} drifted (records only, not blob verification)"
    )
    return 1 if bad else 0


def cmd_coverage(_a) -> int:
    print(yaml.safe_dump(collect()["coverage"], sort_keys=False), end="")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, fn in (
        ("write", cmd_write),
        ("check", cmd_check),
        ("coverage", cmd_coverage),
    ):
        sub.add_parser(name).set_defaults(fn=fn)
    args = parser.parse_args()
    try:
        return args.fn(args)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        yaml.YAMLError,
        duckdb.Error,
    ) as exc:
        print(f"Cannot verify/generate risk-factor records: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

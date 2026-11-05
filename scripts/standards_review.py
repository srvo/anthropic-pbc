#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""Bounded standards/Brain audit. Findings are observations, never approvals or repairs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def check_units(units: list[dict], contract: dict) -> list[dict]:
    """Identity/version/coverage checks only: no automated semantic endorsement."""
    findings = []
    seen = set()
    for unit in units:
        key = unit.get("id")
        if not key or key in seen:
            findings.append({"unit": key, "code": "missing-or-duplicate-id"})
        seen.add(key)
        if any(k not in unit for k in contract["canonical_fields"]):
            findings.append({"unit": key, "code": "canonical-fields-missing"})
            continue
        if unit["kind"] not in ("question", "observation", "inference", "recommendation"):
            findings.append({"unit": key, "code": "unknown-assertion-kind"})
        statement = unit["statement"]
        if not isinstance(statement, str) or not statement.strip() or len(re.split(r"\n\s*\n", statement.strip())) != 1:
            findings.append({"unit": key, "code": "not-one-paragraph"})
        bound = {k: unit[k] for k in contract["canonical_fields"]}
        fingerprint = digest(canonical(bound))
        kinds = set()
        for view in unit.get("representations", []):
            kind = view.get("kind")
            if kind not in contract["representation_kinds"]:
                findings.append({"unit": key, "code": "unknown-representation-kind"})
            else:
                kinds.add(kind)
            if view.get("unit_id") != key or view.get("unit_sha256") != fingerprint:
                findings.append({"unit": key, "code": "representation-version-drift"})
        if "prose" not in kinds or len(kinds) < contract["minimum_representation_kinds"]:
            findings.append({"unit": key, "code": "representation-coverage-gap"})
        # A structural pass is never evidence of one semantic purpose or equivalence.
        review = unit.get("semantic_review", {})
        if not (review.get("status") == "accepted" and review.get("reviewer")
                and review.get("unit_sha256") == fingerprint and review.get("source_ref")):
            findings.append({"unit": key, "code": "semantic-review-pending-or-stale"})
    return findings


def probe_report_cli(praxis: Path) -> dict:
    cli = praxis / "report_writer/praxis_cli.py"
    if not cli.is_file():
        return {"id": "composable-report-runtime", "status": "unknown", "detail": "Shared report CLI unavailable"}
    text = "---\ntitle: Fixture\nauthor: Fixture\ndate: 2000-01-01\ntemplate: research\npresentation: praxis\npublisher: praxis\n---\n# Fixture\n\n## Question\n\nA question.\n\n## Evidence and limits\n\nAn explicitly scoped fixture.\n"
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / "fixture.md"
        source.write_text(text)
        code = "import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);from praxis_cli import check_report;check_report(Path(sys.argv[2]))"
        result = subprocess.run([sys.executable, "-c", code, str(cli.parent), str(source)], capture_output=True, text=True, timeout=30)
    return {"id": "composable-report-runtime", "status": "pass" if result.returncode == 0 else "fail",
            "detail": "Context-specific composition accepted" if result.returncode == 0 else result.stderr[-1600:]}


def review(root: Path, praxis: Path, *, brain: bool, units: Path | None = None) -> dict:
    checks, inputs, opportunities = [], [], []
    registry_path = root / "docs/standards.json"
    registry = json.loads(registry_path.read_text())
    inputs.append({"uri": "repo:docs/standards.json", "sha256": digest(registry_path.read_bytes())})
    authorities = set()
    for entry in registry["standards"]:
        key = entry["id"]
        if key in authorities:
            checks.append({"id": key, "status": "fail", "detail": "Duplicate standard identity"})
        authorities.add(key)
        base = praxis if entry["repository"] == "praxis" else root
        source = base / entry["path"]
        present = source.is_file()
        checks.append({"id": key, "status": "pass" if present else "unknown",
                       "detail": f"{entry['role']}: {entry['path']}"})
        if present:
            inputs.append({"uri": f"{entry['repository']}:{entry['path']}", "sha256": digest(source.read_bytes())})
    checks.append(probe_report_cli(praxis))
    contract_path = praxis / "design/argument-units.json"
    if units is None or not units.is_file() or not contract_path.is_file():
        checks.append({"id": "argument-representation-coverage", "status": "unknown",
                       "detail": "No versioned argument-unit register supplied; prose atomicity and alternate-view coverage are unassessed"})
    else:
        findings = check_units(json.loads(units.read_text()), json.loads(contract_path.read_text()))
        checks.append({"id": "argument-representation-coverage", "status": "fail" if findings else "pass", "findings": findings})
        inputs.extend({"uri": "file:" + str(p), "sha256": digest(p.read_bytes())} for p in (units, contract_path))
    if brain:
        for label, args in (("brain-freshness", ["status", "--fail-on", "release", "--json"]),
                            ("brain-integrity", ["doctor", "--json"])):
            try:
                result = subprocess.run(["entire", "brain", *args], cwd=root, capture_output=True, text=True, timeout=45)
                payload = json.loads(result.stdout)
                checks.append({"id": label, "status": "pass" if result.returncode == 0 else "fail", "report": payload,
                               "assurance": "Index/anchor health only, not semantic correctness"})
            except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
                checks.append({"id": label, "status": "unknown", "detail": type(exc).__name__})
    for check in checks:
        if check["status"] != "pass":
            opportunities.append({"id": "standards:" + check["id"], "kind": "reconciliation",
                                  "target": check["id"], "reason": check.get("detail", "Recorded diagnostic finding"),
                                  "review_state": "proposed", "automatic_change": False})
    return {"schema_version": 1, "actor": "script:standards-review-v1", "prompt": "not_applicable",
            "scope": "Declared source presence, runtime composition probe, representation bindings and optional local Brain health",
            "inputs": inputs, "checks": checks, "opportunities": opportunities,
            "status": "findings" if opportunities else "succeeded",
            "limitations": ["Not an exhaustive semantic contradiction detector", "No source or review state is repaired", "Anchor verification is not factual verification"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--praxis", type=Path, default=ROOT.parent / "praxis")
    parser.add_argument("--brain", action="store_true")
    parser.add_argument("--units", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = review(args.repo.resolve(), args.praxis.resolve(), brain=args.brain, units=args.units)
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    else:
        print(payload, end="")
    return 1 if result["status"] == "findings" else 0


if __name__ == "__main__":
    raise SystemExit(main())

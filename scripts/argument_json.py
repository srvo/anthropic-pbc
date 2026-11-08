#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["blake3==1.0.11"]
# ///
"""Emit argument.json: the paper's argument as a machine-readable graph, for the edit plane.

    uv run scripts/argument_json.py emit     # write argument.json
    uv run scripts/argument_json.py check    # fail if argument.json is stale
    uv run scripts/argument_json.py show     # print a summary to stdout

The notebook at docs/notebooks/argument-edit-plane.py reads the emitted file and
asks Sloane where the argument is incomplete. This script is the only thing that
writes it; the notebook never writes to this repository.

## What it reads

`claims/anthropic-contrapunctus.tsv` (docs/descartes-spec.md §8,
`label rests_on witness statement path quote`). Argument rows are the ones the
file marks as such: rows whose `path` and `quote` are both `-` and whose label is
not a quotation label (Q...). Those are §0's chain, `docs/editorial-standard.md`
("The argument lives in the DAG").

## What it computes, and what it does not

`rests_on` is read, never inferred: the file already says what each claim needs.
Two derived values are reported, both plainly structural and both stated as such:

- **unsupported**: an argument row with `rests_on` of `-` and no quotation label
  resting on it. The standard says such a row "stays in the file and fails", so it
  is reported as failing here rather than dropped.
- **because-ness**: the number of claims that transitively rest on a claim
  (docs/editorial-standard.md), counting through to R0. This is a *proposal*: the
  standard puts this computation in Descartes, in Rust, as a command beside
  `check`, and that command does not exist yet (Descartes @ ef99575). Until it
  does, this script is a stand-in and says so in the output's `provenance`.

No clock, host or random value enters the output: a rebuild is byte-identical.
Each input file is named by its BLAKE3 digest (`inputs_blake3`). The commit the
artifact lands in is deliberately not recorded: the artifact is itself committed,
so a commit recorded here would name its own parent.

## Status

Every argument row in the file is `STATUS: proposal` (its own comment, line 175):
the choice of rows and of `rests_on` is model judgment the check cannot verify,
and stands only once Sloane overrides it editorially. The emitted JSON carries
that status so the notebook can show which premises are already accepted and
which are still proposals.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import blake3

ROOT = Path(__file__).resolve().parent.parent
CLAIMS = ROOT / "claims" / "anthropic-contrapunctus.tsv"
REVIEW = ROOT / "claims" / "anthropic-contrapunctus.review.tsv"
PAPER = ROOT / "docs" / "anthropic-contrapunctus.md"
OUT = ROOT / "argument.json"

THESIS = "T0"
REMEDY = "R0"


def _rows(path: Path) -> list[list[str]]:
    """Data rows of a TSV, comments and blanks dropped. Tabs inside a field stay."""
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cells = line.split("\t")
        while len(cells) < 6:
            cells.append("")
        out.append(cells)
    return out


def _split_labels(cell: str) -> list[str]:
    cell = cell.strip()
    if cell in ("", "-"):
        return []
    return [part.strip() for part in cell.split(",") if part.strip()]


def _is_quotation_label(label: str) -> bool:
    return label.startswith("Q")


def load_claims() -> dict[str, dict]:
    """Every row, by label. Quotation rows and argument rows are tagged by kind."""
    claims: dict[str, dict] = {}
    for label, rests_on, witness, statement, path, quote in _rows(CLAIMS):
        claims[label] = {
            "label": label,
            "kind": "quotation" if _is_quotation_label(label) else "argument",
            "rests_on": _split_labels(rests_on),
            "witness": witness.strip(),
            "statement": statement.strip(),
            "path": path.strip(),
            "quote": quote.strip(),
            "has_evidence": path.strip() not in ("", "-") and quote.strip() not in ("", "-"),
        }
    return claims


def load_review_status() -> dict[str, dict]:
    """label -> the atomic review's row: verdict, reason, and whether it was already applied.

    A verdict of `requote` or `context` is the reviewer's *proposal* (the file's own
    header: "Every row is an LLM proposal (status proposed) until Sloane accepts it"),
    and a row whose decision column records Sloane's acceptance has already been fixed
    in the paper. So a verdict is reported as an open advisory, never as a structural
    failure: this script does not read the paper to see whether the fix landed.
    """
    status: dict[str, dict] = {}
    for cells in _rows(REVIEW):
        label, verdict = cells[0].strip(), cells[1].strip()
        if not label or not verdict:
            continue
        decision = cells[6].strip() if len(cells) > 6 else ""
        reason = cells[4].strip() if len(cells) > 4 else ""
        status[label] = {
            "verdict": verdict,
            "applied": decision.lower().startswith("applied"),
            "decision": decision,
            "reason": reason,
        }
    return status


def _dependents(claims: dict[str, dict]) -> dict[str, list[str]]:
    """reverse edges: label -> the labels that name it in rests_on."""
    out: dict[str, list[str]] = {label: [] for label in claims}
    for label, claim in claims.items():
        for parent in claim["rests_on"]:
            out.setdefault(parent, []).append(label)
    for label in out:
        out[label].sort()
    return out


def _reachable(claims: dict[str, dict], start: str, seen: set[str] | None = None) -> set[str]:
    """Everything `start` transitively rests on."""
    seen = set() if seen is None else seen
    for parent in claims.get(start, {}).get("rests_on", []):
        if parent not in seen:
            seen.add(parent)
            _reachable(claims, parent, seen)
    return seen


def because_ness(claims: dict[str, dict]) -> dict[str, int]:
    """Claims that transitively rest on each claim, through to the remedy R0.

    The standard's end point is the thesis; the remedy sits on the thesis, and a
    claim the thesis does not reach scores zero for the main argument. A claim the
    remedy does not reach therefore scores zero.
    """
    reverse = _dependents(claims)
    scores: dict[str, int] = {}
    for label in claims:
        # walk up the dependents to see whether R0 is reached at all
        seen: set[str] = set()
        stack = [label]
        reaches = False
        while stack:
            node = stack.pop()
            for child in reverse.get(node, []):
                if child in seen:
                    continue
                seen.add(child)
                if child == REMEDY:
                    reaches = True
                stack.append(child)
        scores[label] = len(seen) if reaches else 0
    return scores


def _failures(claims: dict[str, dict]) -> dict[str, list[str]]:
    """Why each claim fails structurally, by the standard's rule only.

    `docs/editorial-standard.md`: "A premise with nothing under it stays in the file
    and fails." A premise has something under it when it names evidence or another
    premise in `rests_on`, or when a quotation row rests on it. Everything else here
    is the graph's shape: a dangling label is a failure, and a premise inherits the
    failures of what it needs. Whether a *quotation* is faithful is the atomic
    review's business, not this script's.
    """
    out: dict[str, list[str]] = {}

    def reasons(label: str, stack: tuple[str, ...] = ()) -> list[str]:
        if label in out:
            return out[label]
        if label in stack:
            return []  # a cycle is reported by Descartes, not guessed at here
        claim = claims[label]
        found: list[str] = []
        if claim["kind"] == "quotation":
            if not claim["has_evidence"]:
                found.append(f"quotation {label}: no pinned path and quote")
        else:
            if not claim["rests_on"]:
                found.append(f"{label} rests on nothing: the premise is unsupported")
            for parent in claim["rests_on"]:
                if parent not in claims:
                    found.append(f"{label} rests on {parent}, which is not a row")
                    continue
                for reason in reasons(parent, stack + (label,)):
                    # Name the claim the failure came through, so a reader of the
                    # thesis's reasons sees which premise under it broke.
                    found.append(reason if reason.startswith(f"{label} ") else f"{label} ← {reason}")
        out[label] = found
        return found

    for label, claim in claims.items():
        if claim["kind"] == "argument":
            reasons(label)
    return out


def _advisories(claims: dict[str, dict], review: dict[str, dict]) -> dict[str, list[dict]]:
    """Review proposals still open under a claim, reported apart from structural failure.

    A row whose decision column records Sloane's acceptance (`applied ...`) is dropped:
    the fix was made on her word, and this script does not re-read the paper to check.
    """
    out: dict[str, list[dict]] = {}
    for label, claim in claims.items():
        if claim["kind"] != "argument":
            continue
        found: list[dict] = []
        for parent in claim["rests_on"]:
            row = review.get(parent)
            if row and row["verdict"] != "verified" and not row["applied"]:
                found.append(
                    {
                        "label": parent,
                        "verdict": row["verdict"],
                        "reason": row["reason"],
                    }
                )
        out[label] = found
    return out


def _section(statement: str) -> str:
    """The paper section a claim sits in, from its statement's leading '§n:'."""
    head = statement.split(":", 1)[0].strip()
    return head if head.startswith("§") else ""


def _input_digests() -> dict[str, str]:
    """BLAKE3 of each input file, so a reader can tell which bytes produced this.

    A git commit is deliberately *not* recorded: this file is itself committed, so
    the commit it lands in cannot be known when it is written, and recording the
    parent's would make the artifact disagree with its own tree. The input digests
    are what actually identify the argument, and they are stable.
    """
    digests: dict[str, str] = {}
    for path in (CLAIMS, REVIEW):
        if path.exists():
            digests[str(path.relative_to(ROOT))] = "blake3:" + blake3.blake3(path.read_bytes()).hexdigest()
    return digests


def build() -> dict:
    claims = load_claims()
    review = load_review_status()
    reverse = _dependents(claims)
    scores = because_ness(claims)
    failures = _failures(claims)
    advisories = _advisories(claims, review)

    premises = []
    for label, claim in claims.items():
        if claim["kind"] != "argument":
            continue
        parents = claim["rests_on"]
        evidence = [p for p in parents if claims.get(p, {}).get("kind") == "quotation"]
        sub_premises = [p for p in parents if claims.get(p, {}).get("kind") == "argument"]
        missing = [p for p in parents if p not in claims]
        # "Unsupported" is the standard's own case: the premise names nothing that
        # stands under it, so it fails however many claims rest on it in turn.
        unsupported = not parents
        premises.append(
            {
                "label": label,
                "statement": claim["statement"],
                "section": _section(claim["statement"]),
                "rests_on": parents,
                "rests_on_evidence": evidence,
                "rests_on_premises": sub_premises,
                "rests_on_missing": missing,
                "supported_by": sorted(reverse.get(label, [])),
                "because_ness": scores.get(label, 0),
                "unsupported": unsupported,
                "fails": bool(failures.get(label)),
                "failure_reasons": failures.get(label, []),
                "open_reviews": advisories.get(label, []),
                "role": (
                    "thesis" if label == THESIS else "remedy" if label == REMEDY else "premise"
                ),
                "evidence_count": len(evidence),
                # The quotations themselves, so the notebook can show evidence at
                # the quotation level rather than only naming a label. Text is
                # copied exactly as the claims file holds it; nothing is summarised.
                "evidence": [
                    {
                        "label": q,
                        "quote": claims[q]["quote"],
                        "path": claims[q]["path"],
                        "review": (review.get(q) or {}).get("verdict"),
                        "review_applied": (review.get(q) or {}).get("applied", False),
                    }
                    for q in evidence
                ],
            }
        )

    unsupported_labels = [p["label"] for p in premises if p["unsupported"]]
    thesis = next((p for p in premises if p["label"] == THESIS), None)

    return {
        "schema": "anthropic-pbc/argument/v1",
        "about": (
            "The paper's argument as a graph of claims, for the edit plane in "
            "docs/notebooks/argument-edit-plane.py. Emitted by scripts/argument_json.py; "
            "do not edit by hand."
        ),
        "source": {
            "claims": "claims/anthropic-contrapunctus.tsv",
            "review": "claims/anthropic-contrapunctus.review.tsv",
            "paper": str(PAPER.relative_to(ROOT)),
            "inputs_blake3": _input_digests(),
            "format": "label rests_on witness statement path quote (docs/descartes-spec.md §8)",
        },
        "provenance": {
            "because_ness": (
                "proposal: computed here because Descartes has no `because` command yet "
                "(docs/editorial-standard.md puts it in Rust, beside check)"
            ),
            "status": "proposal",
            "status_note": (
                "Every argument row is model judgment the check cannot verify, and stands "
                "only once Sloane overrides it editorially (claims file, STATUS: proposal)."
            ),
        },
        "counts": {
            "premises": len(premises),
            "arguments": sum(len(p["rests_on"]) for p in premises),
            "unsupported_premises": len(unsupported_labels),
            "open_reviews": sum(len(p["open_reviews"]) for p in premises),
            "failing": sum(1 for p in premises if p["fails"]),
            "quotations": sum(1 for c in claims.values() if c["kind"] == "quotation"),
        },
        "unsupported_premises": unsupported_labels,
        "thesis": thesis,
        "premises": premises,
        "prompt_kinds": PROMPT_KINDS,
    }


# The four ways Sloane said the argument can fail, as the notebook offers them.
# Kept here so the artifact a reader fetches and the notebook that reads it agree
# on the vocabulary; the notebook adds the prose for each.
PROMPT_KINDS = [
    {
        "id": "incomplete",
        "title": "The argument does not get there",
        "question": "Which step does the argument need that it does not have?",
        "labels": ["needs-premise"],
    },
    {
        "id": "under_weighted",
        "title": "A premise carries more than it can",
        "question": "Which premise is doing work no evidence under it supports?",
        "labels": ["premise-weight"],
    },
    {
        "id": "examination",
        "title": "A premise needs more examination",
        "question": "Which premise is stated too confidently for what is known?",
        "labels": ["premise-scrutiny"],
    },
    {
        "id": "counter",
        "title": "There is a case the argument does not answer",
        "question": "What is the strongest case in which the argument fails?",
        "labels": ["counterexample"],
    },
]


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "emit"
    doc = build()
    text = json.dumps(doc, indent=2, ensure_ascii=False, sort_keys=False) + "\n"

    if cmd == "emit":
        OUT.write_text(text, encoding="utf-8")
        c = doc["counts"]
        print(
            f"wrote {OUT.relative_to(ROOT)}: {c['premises']} premises, "
            f"{c['unsupported_premises']} unsupported, {c['failing']} failing"
        )
        return 0
    if cmd == "check":
        if not OUT.exists():
            print(f"{OUT.name} is missing; run `uv run scripts/argument_json.py emit`", file=sys.stderr)
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"{OUT.name} is stale; run `uv run scripts/argument_json.py emit`", file=sys.stderr)
            return 1
        print(f"{OUT.name} is current")
        return 0
    if cmd == "show":
        for p in doc["premises"]:
            flag = "FAILS" if p["fails"] else "stands"
            print(f"{p['label']:<6} {p['role']:<7} bn={p['because_ness']:<3} {flag:<6} {p['statement'][:70]}")
        return 0
    print(f"unknown command {cmd!r}; use emit, check or show", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

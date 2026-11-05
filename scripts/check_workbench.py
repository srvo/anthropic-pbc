# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Validate the workbench primitives (argument/parties.tsv, coverage.tsv, quantities.tsv, sides.tsv).

    python3 scripts/check_workbench.py

Checks: known labels; valid kind, state and basis values; full party x theme coverage grid, each
non-missing cell citing cards in that theme; observed values appear verbatim in their pinned quote;
applied rows carry a range and no value (unless normative); implied formulas use only defined
quantities, list them in rests_on, and form no cycle. Rules live in workbench.check.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import workbench as wb  # noqa: E402


def main() -> int:
    w = wb.check(wb.load())
    for e in w.deck.errors:
        print("FAIL\tdeck: " + e)
    for e in w.errors:
        print("FAIL\t" + e)
    by_basis: dict[str, int] = {}
    for q in w.quantities:
        by_basis[q["basis"]] = by_basis.get(q["basis"], 0) + 1
    states: dict[str, int] = {}
    for r in w.coverage:
        states[r["state"]] = states.get(r["state"], 0) + 1
    n = len(w.errors) + len(w.deck.errors)
    print(f"summary\t{len(w.parties)} parties\tcoverage {dict(sorted(states.items()))}\t"
          f"quantities {dict(sorted(by_basis.items()))}\t{n} problems")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())

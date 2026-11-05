# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Validate the argument cards (argument/*.tsv) against the claims file.

    uv run scripts/check_cards.py                 # structural check + circle check
    uv run scripts/check_cards.py descartes --bin PATH/TO/descartes
                                                  # run Descartes over claims + cards, record its output
    uv run scripts/check_cards.py circles --write # recompute the circle column of sequence.tsv

Circles (descartes docs/circles.md): a Q-label that Descartes reports ok is circle 1
(one instrument: the recipe's text tool plus the byte-exact quote match); a failing
Q-label or a pending source is circle 0. A card is the minimum of what it rests on,
capped at 3 (LLM-written statement); 4 needs a person's sign-off, which no card has.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAIMS = Path("claims/anthropic-contrapunctus.tsv")
ARG = Path("argument")
ROLES = {"premise", "inference", "objection", "reply", "conclusion", "lens", "budget"}
STATUSES = {"draft", "checked"}
MAX_WORDS = 40
LLM_CAP = 3


def read_tsv(path: Path, header: bool = True) -> list[dict[str, str]] | list[list[str]]:
    rows = [l.split("\t") for l in path.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
    if not header:
        return rows
    head, *body = rows
    return [dict(zip(head, r + [""] * (len(head) - len(r)))) for r in body]


@dataclass
class Deck:
    q_labels: set[str]
    cards: dict[str, list[str]]  # label -> rests_on
    statements: dict[str, str]
    sequence: list[dict[str, str]]
    themes: list[dict[str, str]]
    pending: set[str]
    descartes_ok: set[str] | None = None
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def load(root: Path = ROOT) -> Deck:
    q = {r[0] for r in read_tsv(root / CLAIMS, header=False)}
    cards: dict[str, list[str]] = {}
    statements: dict[str, str] = {}
    errors = []
    for r in read_tsv(root / ARG / "cards.tsv", header=False):
        if len(r) != 6:
            errors.append(f"cards.tsv: {r[0]}: expected 6 columns, got {len(r)}")
            continue
        label, rests, _witness, statement, _path, _quote = r
        if label in cards:
            errors.append(f"cards.tsv: {label}: duplicate label")
        cards[label] = [] if rests == "-" else [x.strip() for x in rests.split(",") if x.strip()]
        statements[label] = statement
    ok_path = root / ARG / "descartes-check.txt"
    ok = None
    if ok_path.exists():
        ok = {l.split("\t")[1] for l in ok_path.read_text(encoding="utf-8").splitlines() if l.startswith("ok\t")}
    d = Deck(q, cards, statements, read_tsv(root / ARG / "sequence.tsv"), read_tsv(root / ARG / "themes.tsv"),
             {r["id"] for r in read_tsv(root / ARG / "pending-sources.tsv")}, ok)
    d.errors.extend(errors)
    return d


def lens_of(label: str, themes: list[dict[str, str]]) -> tuple[str, str] | None:
    """L-<theme>-<lens>-NN -> (theme, lens), matched against themes.tsv (ids contain hyphens)."""
    if not label.startswith("L-"):
        return None
    for t in themes:
        for lens in t["lenses"].split(","):
            if lens != "-" and label.startswith(f"L-{t['theme']}-{lens}-") and label.rsplit("-", 1)[1].isdigit():
                return t["theme"], lens
    return ("?", "?")


def find_cycles(cards: dict[str, list[str]]) -> list[list[str]]:
    state: dict[str, int] = {}
    cycles = []

    def visit(n: str, path: list[str]) -> None:
        state[n] = 1
        for m in cards.get(n, []):
            if m not in cards:
                continue
            if state.get(m) == 1:
                cycles.append(path[path.index(m):] + [m] if m in path else [n, m])
            elif m not in state:
                visit(m, path + [m])
        state[n] = 2

    for n in sorted(cards):
        if n not in state:
            visit(n, [n])
    return cycles


def circles(d: Deck) -> dict[str, int]:
    memo: dict[str, int] = {}

    def of(x: str, seen: frozenset = frozenset()) -> int:
        if x in memo:
            return memo[x]
        if x in d.q_labels:
            return 1 if (d.descartes_ok is not None and x in d.descartes_ok) else 0
        if x not in d.cards or x in seen:
            return 0
        deps = d.cards[x]
        v = min((of(y, seen | {x}) for y in deps), default=0)
        memo[x] = min(v, LLM_CAP)
        return memo[x]

    return {c: of(c) for c in d.cards}


def check(d: Deck) -> Deck:
    known = d.q_labels | set(d.cards) | d.pending
    for c, deps in d.cards.items():
        if not deps:
            d.errors.append(f"{c}: rests on nothing")
        for x in deps:
            if x not in known:
                d.errors.append(f"{c}: rests on {x}, which is not a Q-label, card or pending source")
        n = len(d.statements[c].split())
        if n > MAX_WORDS:
            d.errors.append(f"{c}: statement has {n} words (max {MAX_WORDS})")
    for cyc in find_cycles(d.cards):
        d.errors.append("cycle: " + " -> ".join(cyc))

    seq_cards = [r["card"] for r in d.sequence]
    for c in sorted(set(d.cards) - set(seq_cards)):
        d.errors.append(f"{c}: not in sequence.tsv")
    for c in sorted(set(seq_cards) - set(d.cards)):
        d.errors.append(f"sequence.tsv: {c} is not a card")
    for c in sorted({c for c in seq_cards if seq_cards.count(c) > 1}):
        d.errors.append(f"sequence.tsv: {c} appears more than once")
    orders = [r["order"] for r in d.sequence]
    if any(not o.isdigit() for o in orders) or len(set(orders)) != len(orders):
        d.errors.append("sequence.tsv: order must be unique integers")

    theme_ids = {t["theme"]: t for t in d.themes}
    for t in d.themes:
        lenses = [x for x in t["lenses"].split(",") if x != "-"]
        if t["default_lens"] != "-" and t["default_lens"] not in lenses:
            d.errors.append(f"themes.tsv: {t['theme']}: default lens {t['default_lens']} is not one of its lenses")
        for lens in lenses:
            if not any(c.startswith(f"L-{t['theme']}-{lens}-") for c in d.cards):
                d.errors.append(f"themes.tsv: {t['theme']}: lens {lens} has no cards")
    for r in d.sequence:
        c = r["card"]
        if r["theme"] not in theme_ids:
            d.errors.append(f"{c}: theme {r['theme']} is not in themes.tsv")
        if r["role"] not in ROLES:
            d.errors.append(f"{c}: role {r['role']} is not one of {sorted(ROLES)}")
        if r["status"] not in STATUSES:
            d.errors.append(f"{c}: status {r['status']} is not one of {sorted(STATUSES)}")
        if len(r["title"].split()) > 8:
            d.errors.append(f"{c}: title has more than 8 words")
        if not r["slot"]:
            d.errors.append(f"{c}: empty slot")
        lt = lens_of(c, d.themes)
        if lt == ("?", "?"):
            d.errors.append(f"{c}: lens card does not match a lens in themes.tsv")
        elif lt and lt[0] != r["theme"]:
            d.errors.append(f"{c}: lens card filed under theme {r['theme']}, label says {lt[0]}")
        if r["status"] == "checked" and any(x in d.pending for x in d.cards.get(c, [])):
            d.errors.append(f"{c}: checked, but rests on a pending source")

    slots: dict[str, list[str]] = {}
    for r in d.sequence:
        slots.setdefault(r["slot"], []).append(r["card"])
    for s, cs in slots.items():
        if len(cs) > 1:
            d.notes.append(f"alternatives: slot {s}: {', '.join(cs)} (default {cs[0]})")

    if d.descartes_ok is None:
        d.notes.append("no argument/descartes-check.txt: every Q-label counts as circle 0; run the descartes subcommand")
    want = circles(d)
    for r in d.sequence:
        c = r["card"]
        if c in want and r.get("circle", "") != str(want[c]):
            d.errors.append(f"{c}: circle {r.get('circle')!r}, computed {want[c]} (run circles --write)")
    return d


def write_circles(root: Path = ROOT) -> int:
    d = load(root)
    want = circles(d)
    path = root / ARG / "sequence.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    head = lines[0].split("\t")
    i = head.index("circle")
    out = [lines[0]]
    for l in lines[1:]:
        cols = l.split("\t")
        cols[i] = str(want.get(cols[head.index("card")], 0))
        out.append("\t".join(cols))
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return 0


def run_descartes(binary: Path, root: Path = ROOT) -> int:
    """Concatenate the claims file and the cards into argument/combined.tsv (gitignored) and
    record Descartes's unedited output (stdout then stderr) in argument/descartes-check.txt."""
    combined = ARG / "combined.tsv"
    text = (root / CLAIMS).read_text(encoding="utf-8") + (root / ARG / "cards.tsv").read_text(encoding="utf-8")
    (root / combined).write_text(text, encoding="utf-8")
    p = subprocess.run([str(binary), "check", str(combined)], cwd=root, capture_output=True, text=True, check=False)
    (root / ARG / "descartes-check.txt").write_text(p.stdout + p.stderr, encoding="utf-8")
    summary = [l for l in p.stdout.splitlines() if l.startswith("summary")]
    print("\n".join(summary) or "no summary line", f"(exit {p.returncode})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("check")
    dp = sub.add_parser("descartes")
    dp.add_argument("--bin", type=Path, required=True)
    cp = sub.add_parser("circles")
    cp.add_argument("--write", action="store_true", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "descartes":
        return run_descartes(a.bin.resolve())
    if a.cmd == "circles":
        return write_circles()
    d = check(load())
    for n in d.notes:
        print("note\t" + n)
    for e in d.errors:
        print("FAIL\t" + e)
    dist: dict[int, int] = {}
    for v in circles(d).values():
        dist[v] = dist.get(v, 0) + 1
    print(f"summary\t{len(d.cards)} cards\t{len(d.themes)} themes\t"
          + f"circles {dict(sorted(dist.items()))}\t{len(d.errors)} problems")
    return 1 if d.errors else 0


if __name__ == "__main__":
    sys.exit(main())

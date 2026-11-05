#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Hermetic tests for check_cards.py: each builds a tiny deck in a temporary repository."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_cards as cc  # noqa: E402

W = "llm:test"


def deck(root: Path, cards, seq, themes=None, pending=(), claims=("Q1", "Q2"), ok=None):
    (root / "claims").mkdir()
    (root / "argument").mkdir()
    (root / "claims/anthropic-contrapunctus.tsv").write_text(
        "".join(f"{q}\t-\t{W}\tstatement\tsrc.txt\tquote\n" for q in claims), encoding="utf-8")
    (root / "argument/cards.tsv").write_text(
        "".join(f"{l}\t{r}\t{W}\t{s}\t-\t-\n" for l, r, s in cards), encoding="utf-8")
    (root / "argument/sequence.tsv").write_text(
        "order\tcard\ttheme\trole\tslot\ttitle\tstatus\tcircle\n"
        + "".join("\t".join(map(str, r)) + "\n" for r in seq), encoding="utf-8")
    themes = themes or [("t", "Why?", "-", "-")]
    (root / "argument/themes.tsv").write_text(
        "theme\tquestion\tlenses\tdefault_lens\n" + "".join("\t".join(t) + "\n" for t in themes), encoding="utf-8")
    (root / "argument/pending-sources.tsv").write_text(
        "id\tkind\turl\tneeded_for\tnote\n" + "".join(f"{p}\tunpinned\t-\t-\t-\n" for p in pending), encoding="utf-8")
    if ok is not None:
        (root / "argument/descartes-check.txt").write_text("".join(f"ok\t{q}\tx\n" for q in ok), encoding="utf-8")
    return cc.check(cc.load(root))


class CheckCards(unittest.TestCase):
    def run_deck(self, *a, **k):
        with tempfile.TemporaryDirectory() as t:
            return deck(Path(t), *a, **k)

    def test_clean_deck_passes_and_computes_circles(self):
        d = self.run_deck([("A1", "Q1", "one"), ("A2", "A1,Q2", "two")],
                          [(10, "A1", "t", "premise", "s1", "One", "draft", 1),
                           (20, "A2", "t", "conclusion", "s2", "Two", "draft", 0)], ok=["Q1"])
        self.assertEqual(d.errors, [])
        self.assertEqual(cc.circles(d), {"A1": 1, "A2": 0})  # Q2 not ok -> circle 0, minimum climbs

    def test_unresolved_label(self):
        d = self.run_deck([("A1", "Q9", "one")], [(10, "A1", "t", "premise", "s1", "One", "draft", 0)])
        self.assertTrue(any("Q9" in e for e in d.errors))

    def test_pending_source_resolves_but_blocks_checked(self):
        d = self.run_deck([("A1", "P-x", "one")], [(10, "A1", "t", "premise", "s1", "One", "checked", 0)],
                          pending=["P-x"])
        self.assertEqual([e for e in d.errors if "not a Q-label" in e], [])
        self.assertTrue(any("pending source" in e for e in d.errors))

    def test_cycle_detected(self):
        d = self.run_deck([("A1", "A2", "one"), ("A2", "A1", "two")],
                          [(10, "A1", "t", "premise", "s1", "One", "draft", 0),
                           (20, "A2", "t", "premise", "s2", "Two", "draft", 0)])
        self.assertTrue(any(e.startswith("cycle") for e in d.errors))

    def test_card_missing_from_sequence(self):
        d = self.run_deck([("A1", "Q1", "one"), ("A2", "Q1", "two")],
                          [(10, "A1", "t", "premise", "s1", "One", "draft", 0)])
        self.assertTrue(any("A2: not in sequence" in e for e in d.errors))

    def test_long_statement(self):
        d = self.run_deck([("A1", "Q1", " ".join(["word"] * 41))],
                          [(10, "A1", "t", "premise", "s1", "One", "draft", 0)])
        self.assertTrue(any("41 words" in e for e in d.errors))

    def test_lens_must_exist_and_have_cards(self):
        themes = [("planet", "Tolerable?", "boundaries,basin", "boundaries")]
        d = self.run_deck([("L-planet-boundaries-01", "Q1", "def")],
                          [(10, "L-planet-boundaries-01", "planet", "lens", "s1", "Def", "draft", 0)],
                          themes=themes)
        self.assertTrue(any("lens basin has no cards" in e for e in d.errors))
        d = self.run_deck([("L-planet-nope-01", "Q1", "def")],
                          [(10, "L-planet-nope-01", "planet", "lens", "s1", "Def", "draft", 0)],
                          themes=[("planet", "Tolerable?", "boundaries", "missing")])
        self.assertTrue(any("does not match a lens" in e for e in d.errors))
        self.assertTrue(any("default lens missing" in e for e in d.errors))

    def test_slot_alternatives_flagged(self):
        d = self.run_deck([("A1", "Q1", "one"), ("A2", "Q1", "two")],
                          [(10, "A1", "t", "budget", "alloc", "One", "draft", 0),
                           (20, "A2", "t", "budget", "alloc", "Two", "draft", 0)])
        self.assertEqual(d.errors, [])
        self.assertTrue(any("slot alloc: A1, A2 (default A1)" in n for n in d.notes))

    def test_stale_circle_flagged(self):
        d = self.run_deck([("A1", "Q1", "one")], [(10, "A1", "t", "premise", "s1", "One", "draft", 0)], ok=["Q1"])
        self.assertTrue(any("computed 1" in e for e in d.errors))

    def test_bad_role(self):
        d = self.run_deck([("A1", "Q1", "one")], [(10, "A1", "t", "musing", "s1", "One", "draft", 0)])
        self.assertTrue(any("role musing" in e for e in d.errors))


if __name__ == "__main__":
    unittest.main()

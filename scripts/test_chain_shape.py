#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Hermetic tests for chain_shape.py link classification, reusing the tiny-deck builder."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chain_shape as cs  # noqa: E402
from test_check_cards import deck  # noqa: E402


def kinds(cards, seq, ok):
    with tempfile.TemporaryDirectory() as t:
        d = deck(Path(t), cards, seq, ok=ok)
        r = cs.runs(d)[0]
        return [lk.kind for lk in r.links], [lk.proven for lk in r.links], r


class ChainShape(unittest.TestCase):
    def test_four_link_kinds(self):
        k, p, r = kinds(
            [("A1", "Q1", "a"), ("A2", "Q2", "b"), ("A3", "A1,A2", "c"), ("A4", "Q1", "d"), ("A5", "Q1", "e")],
            [(10, "A1", "t", "premise", "s1", "A", "draft", 1), (20, "A2", "t", "premise", "s2", "B", "draft", 0),
             (30, "A3", "t", "conclusion", "s3", "C", "draft", 0), (40, "A4", "t", "objection", "s4", "D", "draft", 1),
             (50, "A5", "t", "premise", "s5", "E", "draft", 1)],
            ok=["Q1"])
        # A1 -> A2: A3 later uses A1 (and). A2 -> A3: A3 rests on A2 (therefore).
        # A3 -> A4: objection (but). A4 -> A5: nothing uses A4 (and then).
        self.assertEqual(k, [cs.AND, cs.THEREFORE, cs.BUT, cs.AND_THEN])
        # Q2 fails, so A2 and A3 are circle 0: every link touching them is a gap in the proven lane.
        self.assertEqual(p, [False, False, False, True])
        self.assertEqual(r.shape(), "■ & ■ ∴ ■ but ■ … ■")
        self.assertEqual(r.shape(True), "■ · □ · □ · ■ … ■")

    def test_transitive_support_counts_as_therefore(self):
        k, _, _ = kinds([("A1", "Q1", "a"), ("X", "A1", "hidden"), ("A2", "X", "b")],
                        [(10, "A1", "t", "premise", "s1", "A", "draft", 1),
                         (20, "A2", "t", "conclusion", "s2", "B", "draft", 1)], ok=["Q1"])
        self.assertEqual(k, [cs.THEREFORE])

    def test_slot_alternatives_collapse_to_default(self):
        _, _, r = kinds([("A1", "Q1", "a"), ("A2", "Q1", "alt"), ("A3", "A2", "c")],
                        [(10, "A1", "t", "premise", "s1", "A", "draft", 1),
                         (11, "A2", "t", "premise", "s1", "A-alt", "draft", 1),
                         (20, "A3", "t", "conclusion", "s2", "C", "draft", 1)], ok=["Q1"])
        self.assertEqual([b.card for b in r.beats], ["A1", "A3"])
        self.assertEqual(r.beats[0].alternatives, ["A2"])
        self.assertEqual(r.links[0].kind, cs.THEREFORE)  # A3 rests on the alternative, which aliases to A1


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Hermetic tests for workbench.py: parties, coverage, quantities, barriers and the survivorship maths.
Each test builds a tiny deck in a temporary repository with test_check_cards.deck."""
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import workbench as wb  # noqa: E402
from test_check_cards import deck  # noqa: E402

QHEAD = "id\tname\tvalue\tunit\tlow\thigh\tbasis\trests_on\tnote\tstart\n"
CARDS = [("A1", "Q1", "one"), ("A2", "A1,Q2", "two")]
SEQ = [(10, "A1", "t", "premise", "s1", "One", "draft", 1), (20, "A2", "t", "conclusion", "s2", "Two", "draft", 0)]


def bench(root: Path, quantities=(), parties=(), coverage=None, sides=(), quotes=None, pending=()):
    deck(root, CARDS, SEQ, ok=["Q1"], pending=pending)
    if quotes:  # rewrite the claims file with real quotes
        (root / "claims/anthropic-contrapunctus.tsv").write_text(
            "".join(f"{q}\t-\tllm:test\ts\tsrc.txt\t{text}\n" for q, text in quotes.items()), encoding="utf-8")
    (root / "argument/quantities.tsv").write_text(QHEAD + "".join("\t".join(r) + "\n" for r in quantities), encoding="utf-8")
    (root / "argument/parties.tsv").write_text(
        "id\tname\tkind\tstanding\trests_on\n" + "".join("\t".join(r) + "\n" for r in parties), encoding="utf-8")
    if coverage is None:
        coverage = [(p[0], "t", "missing", "-", "-") for p in parties]
    (root / "argument/coverage.tsv").write_text(
        "party\ttheme\tstate\tcards\tnote\n" + "".join("\t".join(r) + "\n" for r in coverage), encoding="utf-8")
    (root / "argument/sides.tsv").write_text(
        "card\tside\treason\n" + "".join("\t".join(r) + "\n" for r in sides), encoding="utf-8")
    return wb.check(wb.load(root))


def obs(i, value, rests="Q1"):
    return (i, i, value, "u", "-", "-", "observed", rests, "-", "-")


def app(i, lo="0", hi="1", start="mid", rests="-", value="-", note="-"):
    return (i, i, value, "u", lo, hi, "applied", rests, note, start)


def imp(i, formula, rests):
    return (i, i, "=" + formula, "u", "-", "-", "implied", rests, "-", "-")


class Workbench(unittest.TestCase):
    def run_bench(self, **k):
        with tempfile.TemporaryDirectory() as t:
            w = bench(Path(t), **k)
            return w, wb.evaluate(w.quantities), wb.basis_of(w)

    def test_observed_value_must_appear_in_quote(self):
        q = {"Q1": "approximately $895.4 billion of spend", "Q2": "more than 33,000 flaws"}
        w, _, _ = self.run_bench(quantities=[obs("a", "895.4"), obs("b", "33000", "Q2")], quotes=q)
        self.assertEqual(w.errors, [])
        w, _, _ = self.run_bench(quantities=[obs("a", "500")], quotes=q)
        self.assertTrue(any("does not appear in the quote" in e for e in w.errors))
        w, _, _ = self.run_bench(quantities=[obs("a", "95.4")], quotes=q)  # a fragment of 895.4 is not a match
        self.assertTrue(any("does not appear" in e for e in w.errors))

    def test_observed_without_value_needs_pending_source(self):
        w, v, b = self.run_bench(quantities=[obs("a", "-", "P-x")], pending=["P-x"])
        self.assertEqual(w.errors, [])
        self.assertIsNone(v["a"])
        self.assertEqual(b["a"]["pending"], ["P-x"])
        w, _, _ = self.run_bench(quantities=[obs("a", "-")])
        self.assertTrue(any("no pending source" in e for e in w.errors))

    def test_applied_has_range_and_no_value_unless_normative(self):
        w, v, _ = self.run_bench(quantities=[app("h", "0", "0.2"), app("l", "0", "0.5", start="low"),
                                             app("n", value="0.1", note="normative: a line"), ])
        self.assertEqual(w.errors, [])
        self.assertAlmostEqual(v["h"], 0.1)
        self.assertEqual(v["l"], 0)
        self.assertEqual(v["n"], 0.1)
        w, _, _ = self.run_bench(quantities=[app("x", value="0.3")])
        self.assertTrue(any("normative" in e for e in w.errors))
        w, _, _ = self.run_bench(quantities=[app("x", "1", "0")])
        self.assertTrue(any("low must be below high" in e for e in w.errors))

    def test_implied_formula_inherits_weakest_basis(self):
        q = {"Q1": "uses 415 TWh", "Q2": "-"}
        rows = [obs("e", "415"), app("i", "0", "1000"), imp("m", "e*i/1000", "e,i"), imp("r", "e/e", "e")]
        w, v, b = self.run_bench(quantities=rows, quotes=q)
        self.assertEqual(w.errors, [])
        self.assertAlmostEqual(v["m"], 415 * 500 / 1000)
        self.assertEqual(b["m"]["effective"], "applied")
        self.assertEqual(b["r"]["effective"], "observed")
        self.assertEqual(wb.implied_order(w.quantities), ["m", "r"])

    def test_implied_formula_checks(self):
        w, _, _ = self.run_bench(quantities=[app("a"), imp("b", "a*zz", "a,zz")])
        self.assertTrue(any("zz, which is not a quantity" in e for e in w.errors))
        w, _, _ = self.run_bench(quantities=[app("a"), imp("b", "a*2", "-")])
        self.assertTrue(any("exactly the formula's inputs" in e for e in w.errors))
        w, _, _ = self.run_bench(quantities=[imp("b", "c+1", "c"), imp("c", "b+1", "b")])
        self.assertTrue(any("cycle" in e for e in w.errors))
        w, _, _ = self.run_bench(quantities=[app("a"), imp("b", "__import__('os')", "-")])
        self.assertTrue(any("bad formula" in e for e in w.errors))

    def test_formula_js_matches_python(self):
        self.assertEqual(wb.formula_js("max(a-b,0)*c**2/4"),
                         '((Math.max((v["a"] - v["b"]), 0) * Math.pow(v["c"], 2)) / 4)')

    def test_parties_and_coverage(self):
        parties = [("p1", "One", "enforcer", "can sue", "A1"), ("p2", "Two", "affected", "none established", "-")]
        cov = [("p1", "t", "voiced", "A1", "own words"), ("p2", "t", "missing", "-", "-")]
        w, _, _ = self.run_bench(parties=parties, coverage=cov)
        self.assertEqual(w.errors, [])
        self.assertEqual(wb.best_state(w), {"p1": "voiced", "p2": "missing"})
        bad = [("p1", "nowhere", "?", "can sue", "Z9")]
        w, _, _ = self.run_bench(parties=bad, coverage=[("p1", "t", "heard", "-", "-"), ("p9", "t", "missing", "A1", "-")])
        msgs = " ".join(w.errors)
        for needle in ("kind '?'", "rests on Z9", "state 'heard'", "unknown party p9", "missing but cites"):
            self.assertIn(needle, msgs)
        w, _, _ = self.run_bench(parties=parties, coverage=[("p1", "t", "identified", "-", "-")])
        self.assertTrue(any("needs at least one card" in e for e in w.errors))
        self.assertTrue(any("p2 x t: no row" in e for e in w.errors))

    def test_barriers_rank_by_links_unlocked(self):
        parties = [("p2", "Two", "affected", "none established", "-")]
        with tempfile.TemporaryDirectory() as t:
            w = bench(Path(t), quantities=[app("h")], parties=parties)
            bs = wb.barriers(w)
        top = bs[0]
        self.assertEqual((top.kind, top.item, top.links, top.lifts), ("failing quote", "Q2", 1, 1))
        kinds = [b.kind for b in bs]
        self.assertIn("unsupported standing", kinds)
        self.assertIn("unsourced assumption", kinds)

    def test_sides(self):
        with tempfile.TemporaryDirectory() as t:
            w = bench(Path(t), sides=[("A1", "defence", "their case")])
            s = wb.side_weights(w)[0]
        self.assertEqual((s["defence"]["written"], s["defence"]["proven"]), (1, 1))
        self.assertEqual((s["complaint"]["written"], s["complaint"]["proven"]), (1, 0))

    def test_survivorship(self):
        self.assertAlmostEqual(wb.survival(0.1, 50), 0.9 ** 50)
        h = wb.hazard_for(0.9, 50)
        self.assertAlmostEqual(wb.survival(h, 50), 0.9)
        self.assertAlmostEqual(wb.lever_hazard(0.1, [0.5, 0.5]), 0.025)
        self.assertTrue(math.isclose(wb.survival(0, 50), 1))


if __name__ == "__main__":
    unittest.main()

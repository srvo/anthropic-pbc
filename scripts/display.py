"""The one place a number becomes text in a built edition.

Rules (docs/report-build.md, "Display controls"):
  - Inputs are exact: int counts or fractions.Fraction. A float raises
    TypeError, because a float has already been rounded once (binary) and
    often twice (a rounded table column). Percentages are computed from counts.
  - One rounding rule: round half up, from the exact value, at the stated
    number of places. Python's format() rounds binary floats half-even, so
    12.5 can print as "12"; here it is always "13".
  - Every value shown is registered with its provenance (source file, how it
    was computed, numerator and denominator), so the build can prove that every
    numeral in the output traces to a registered value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, localcontext
import struct
from fractions import Fraction


def _exact(x) -> Fraction:
    if isinstance(x, bool) or isinstance(x, float):
        raise TypeError(f"display takes exact ints or Fractions, never {type(x).__name__}: {x!r}")
    if isinstance(x, (int, Fraction)):
        return Fraction(x)
    raise TypeError(f"display takes exact ints or Fractions, not {type(x).__name__}")


def round_half_up(x, places: int) -> str:
    f = _exact(x)
    with localcontext() as ctx:
        ctx.prec = 60
        d = Decimal(f.numerator) / Decimal(f.denominator)
        q = d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    s = format(q, "f")
    return "0" + s[2:] if s.startswith("-0") and set(s[2:]) <= set("0.") else s


def pct(n: int, d: int, places: int = 1) -> str:
    """n/d as a percentage, half up, without a % sign."""
    if not isinstance(n, int) or not isinstance(d, int) or isinstance(n, bool) or isinstance(d, bool):
        raise TypeError("pct takes integer counts")
    if d <= 0:
        raise ValueError(f"pct denominator must be positive, got {d}")
    if not 0 <= n <= d:
        raise ValueError(f"pct numerator {n} outside 0..{d}")
    return round_half_up(Fraction(100 * n, d), places)


def ratio(n, d, places: int) -> str:
    """n/d as a proportion (0-1 or any exact ratio), half up. n and d are ints or Fractions."""
    n, d = _exact(n), _exact(d)
    if d == 0:
        raise ValueError("ratio denominator is zero")
    return round_half_up(n / d, places)


def kappa(n: int, pos_a: int, pos_b: int, agree: int) -> Fraction | None:
    """Cohen's kappa for two binary raters, exactly, from counts: n units, pos_a and pos_b
    positives per rater, agree = units where they agree. None when chance agreement is 1."""
    for v in (n, pos_a, pos_b, agree):
        if not isinstance(v, int) or isinstance(v, bool):
            raise TypeError("kappa takes integer counts")
    if n <= 0:
        raise ValueError("kappa needs n > 0")
    po = Fraction(agree, n)
    pa, pb = Fraction(pos_a, n), Fraction(pos_b, n)
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else (po - pe) / (1 - pe)


def _as_f32(x: float) -> float:
    return struct.unpack("<f", struct.pack("<f", x))[0]


def shortest_f32(x: float) -> str:
    """The shortest decimal that reads back as the same float32 (what numpy prints for a float32).
    x must hold a float32 value exactly, as it does when read from a FLOAT column."""
    if _as_f32(x) != x:
        raise ValueError(f"{x!r} is not a float32 value")
    return next(s for s in (f"{x:.{k}g}" for k in range(1, 10)) if _as_f32(float(s)) == x)


def score(x: float, places: int, *, float32: bool = False) -> str:
    """A model probability, the one float display accepts. Model scores are measurements,
    not counts; they are shown half up from their shortest decimal repr. A score stored as
    float32 (the witnesses' p_entail) is rounded from its float32 shortest repr, not from
    the longer repr of the same value widened to a double."""
    if not isinstance(x, float):
        raise TypeError("score takes the model's float probability")
    if not 0.0 <= x <= 1.0:
        raise ValueError(f"score {x} outside 0..1")
    r = shortest_f32(x) if float32 else repr(x)
    return format(Decimal(r).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP), "f")


def cell(v) -> str:
    """A table cell. Only ints, strings (already formatted here) and None pass: a float or
    Fraction reaching a table means a number skipped the formatting rules."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return v
    raise TypeError(f"table cell must be int, str or None, not {type(v).__name__}: {v!r}")


def count(n: int) -> str:
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("count takes an int")
    return f"{n:,}"


@dataclass
class Registry:
    """Every displayed value, with where it came from."""
    values: dict[str, dict] = field(default_factory=dict)

    def put(self, key: str, text: str, *, source: str, how: str, n: int | None = None, d: int | None = None) -> str:
        if key in self.values and self.values[key]["text"] != text:
            raise ValueError(f"binding {key} registered twice with different text")
        rec = {"text": text, "source": source, "how": how}
        if n is not None:
            rec["n"] = n
        if d is not None:
            rec["d"] = d
        self.values[key] = rec
        return text

    def pct(self, key: str, n: int, d: int, places: int, *, source: str, how: str) -> str:
        return self.put(key, pct(n, d, places), source=source, how=how, n=n, d=d)

    def count(self, key: str, n: int, *, source: str, how: str) -> str:
        return self.put(key, count(n), source=source, how=how, n=n)

    def copy(self, key: str, src: str, *, how: str = "") -> str:
        """A second name for a registered value. It carries the source's provenance, n and d."""
        v = self.values[src]
        out = self.put(key, v["text"], source=v["source"], how=f"= {src}" + (f" ({how})" if how else ""),
                       n=v.get("n"), d=v.get("d"))
        if "parts" in v:
            self.values[key]["parts"] = v["parts"]
        return out

    def texts(self) -> set[str]:
        return {v["text"] for v in self.values.values()}


def selftest() -> None:
    cases = [((1, 8, 0), "13"), ((504, 833, 0), "61"), ((1, 2000, 1), "0.1"), ((348, 1645, 1), "21.2"),
             ((0, 5, 1), "0.0"), ((5, 5, 0), "100"), ((1, 3, 2), "33.33"), ((2, 3, 0), "67")]
    for (n, d, p), want in cases:
        got = pct(n, d, p)
        assert got == want, (n, d, p, got, want)
    for bad in (0.5, True):
        try:
            round_half_up(bad, 1)
        except TypeError:
            pass
        else:
            raise AssertionError(f"accepted {bad!r}")
    assert round_half_up(Fraction(-1, 1000), 1) == "0.0"
    assert count(17013) == "17,013"
    assert ratio(1, 8, 2) == "0.13" and ratio(Fraction(3, 2), 3, 1) == "0.5"
    assert kappa(10, 5, 5, 10) == 1 and kappa(4, 4, 4, 4) is None
    assert round_half_up(kappa(10, 5, 5, 0), 3) == "-1.000"
    assert score(0.12345, 4) == "0.1235" and score(1.0, 2) == "1.00"
    assert score(_as_f32(0.38595), 4, float32=True) == "0.3860"   # widened repr 0.38594999... would give 0.3859
    for bad in (0.1, Fraction(1, 2)):
        try:
            cell(bad)
        except TypeError:
            pass
        else:
            raise AssertionError(f"cell accepted {bad!r}")

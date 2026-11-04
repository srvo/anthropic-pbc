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

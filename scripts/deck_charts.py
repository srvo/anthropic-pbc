#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "matplotlib==3.10.7",
# ]
# ///
"""Charts for DECK.md that no corpus report draws yet. Reads committed tables only.

  deck/cve-ai-credit.svg     CVEs published per month, and CVEs whose CNA credits
                             name an AI system (Claude highlighted). corpus/cve/.

Two measures of different scale are drawn as two panels, never a dual axis.
Deterministic: fixed svg.hashsalt, no Date metadata.

    uv run scripts/deck_charts.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "deck"
CVE = ROOT / "corpus" / "cve" / "monthly-ai.tsv"

# Same palette as the corpus reports (dataviz reference palette, light mode).
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
S1, S2, MUTED = "#2a78d6", "#eb6834", "#a8a69f"


def rows(p: Path) -> list[dict]:
    with p.open() as f:
        return list(csv.DictReader((l for l in f if not l.startswith("#")), delimiter="\t"))


def setup():
    import matplotlib
    matplotlib.use("svg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"svg.hashsalt": "deck", "font.family": "DejaVu Sans", "font.size": 10,
                         "axes.edgecolor": INK2, "axes.labelcolor": INK2, "xtick.color": INK2,
                         "ytick.color": INK2})
    return matplotlib, plt


def style(ax) -> None:
    ax.set_facecolor(SURFACE)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)


def cve(matplotlib, plt) -> None:
    r = [x for x in rows(CVE) if x["month"] >= "2023-01"]
    months = [x["month"] for x in r]
    xs = range(len(months))
    pub = [int(x["n_published"]) for x in r]
    ai = [int(x["n_ai_credited"]) for x in r]
    claude = [int(x["n_credit_claude"]) for x in r]
    other = [a - c for a, c in zip(ai, claude)]
    ticks = [i for i, m in enumerate(months) if m.endswith("-01")]
    labels = [months[i][:4] for i in ticks]

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6.2), facecolor=SURFACE, sharex=True,
                                 gridspec_kw={"hspace": 0.45})
    style(a1)
    a1.bar(xs, pub, color=S1, width=0.78)
    a1.annotate(f"{pub[-1]:,}", (xs[-1], pub[-1]), xytext=(0, 4), textcoords="offset points",
                ha="center", color=INK, fontsize=9, fontweight="bold")
    a1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    a1.set_title("CVEs published per month", loc="left", color=INK, fontsize=11, fontweight="bold")

    style(a2)
    a2.bar(xs, claude, color=S2, width=0.78, label="Credit names Claude")
    a2.bar(xs, other, bottom=claude, color=MUTED, width=0.78, label="Credit names another AI system or term")
    a2.annotate(f"{ai[-1]} ({claude[-1]} Claude)", (xs[-1], ai[-1]), xytext=(-4, 4),
                textcoords="offset points", ha="right", color=INK, fontsize=9, fontweight="bold")
    a2.set_title("CVEs whose credits name an AI system, per month", loc="left", color=INK,
                 fontsize=11, fontweight="bold")
    a2.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=INK)
    a2.set_xticks(ticks, labels)
    fig.suptitle("Vulnerability disclosures, and the share credited to AI", x=0.01, ha="left",
                 color=INK, fontsize=13, fontweight="bold")
    fig.text(0.01, 0.01, f"Source: CVEProject/cvelistV5 baseline 2026-11-04 (corpus/cve), {months[0]} to {months[-1]}.\n"
             "Credit = the CNA credits field only, matched to named AI systems. Method credit: Epoch AI (CC BY).",
             color=INK2, fontsize=7)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.12)
    fig.savefig(OUT / "cve-ai-credit.svg", facecolor=SURFACE, metadata={"Date": None, "Creator": None})
    plt.close(fig)


def main() -> int:
    OUT.mkdir(exist_ok=True)
    matplotlib, plt = setup()
    cve(matplotlib, plt)
    print("wrote deck/cve-ai-credit.svg")
    return 0


if __name__ == "__main__":
    sys.exit(main())

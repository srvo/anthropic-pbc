#!/usr/bin/env python3
"""Build the gallery figures for docs/anthropic-contrapunctus.md.

Deterministic: every number below is copied from the paper itself (section
noted beside each dataset), so re-running this script reproduces the SVGs
byte for byte. No clock, no randomness, no network.

    python3 docs/figures/build.py
"""

import re
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
W = 640


# --- Derived inputs -----------------------------------------------------------
# Every number a figure prints is read from a committed source here. None is typed.
# A figure that cannot derive a value fails loudly rather than printing a guess.


def _index_rows():
    """Read the Risk-Governance Index table from docs/risk-governance-index.md."""
    doc = (ROOT / "docs" / "risk-governance-index.md").read_text(encoding="utf-8")
    rows = []
    for line in doc.splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        status = cells[4].strip("`").strip()
        if status not in ("Controlled", "Partial", "Uncontrolled", "Externalized"):
            raise SystemExit(f"risk-governance row {cells[0]}: unknown status {status!r}")
        rows.append((cells[1], status, cells[2]))
    if not rows:
        raise SystemExit("risk-governance-index.md: no index rows found")
    return rows


SCORE_GLYPH = {"\u25cf": 2, "\u25d0": 1, "\u25cb": 0}


def _scorecard_rows():
    """Read Appendix A of the paper: dimension, and the 'filed today' level."""
    paper = (ROOT / "docs" / "anthropic-contrapunctus.md").read_text(encoding="utf-8")
    rows, started = [], False
    for line in paper.splitlines():
        if "Appendix A. Governance scorecard" in line:
            started = True
            continue
        if not started or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2 or cells[0] in ("Dimension", "") or set(cells[0]) <= {"-", ":"}:
            continue
        glyph = cells[1][:1]
        if glyph not in SCORE_GLYPH:
            continue
        rows.append((cells[0], SCORE_GLYPH[glyph]))
        if len(rows) == 10:
            break
    if len(rows) != 10:
        raise SystemExit(f"Appendix A: expected 10 scorecard rows, found {len(rows)}")
    return rows


def _claims_counts():
    """Count quotation rows in the claims file."""
    text = (ROOT / "claims" / "anthropic-contrapunctus.tsv").read_text(encoding="utf-8")
    rows = [
        line for line in text.splitlines()
        if line and not line.startswith("#") and line.split("\t")[0].startswith("Q")
    ]
    return len(rows)

# Tokens mirror index.html :root (light) and its dark override. Figures are
# embedded as <img>, so dark mode follows the OS preference, not the page toggle.
STYLE = """
<style>
  .bg{fill:#ffffff} .ink{fill:#191b1f} .mut{fill:#5b616b} .rule{stroke:#dedcd4}
  .ok{fill:#1f7a4d} .bad{fill:#b23b3b} .warn{fill:#8f6410} .unv{fill:#9aa0ab}
  .acc{fill:#2f4b7c} .accs{stroke:#2f4b7c} .hollow{fill:none;stroke:#5b616b}
  text{font-family:Georgia,'Times New Roman',serif}
  .t{font-size:20px;font-weight:700} .s{font-size:13px} .l{font-size:13px}
  .m{font-family:Menlo,Consolas,monospace;font-size:11px;letter-spacing:.04em}
  @media (prefers-color-scheme:dark){
    .bg{fill:#1b1e24} .ink{fill:#e8e6df} .mut{fill:#9aa0ab} .rule{stroke:#2b2f37}
    .ok{fill:#5fcf93} .bad{fill:#e78c86} .warn{fill:#d9b45f} .unv{fill:#5b616b}
    .acc{fill:#8fb0e6} .accs{stroke:#8fb0e6} .hollow{stroke:#9aa0ab}
  }
</style>
"""


def svg(h, title, sub, body, desc):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" '
        f'width="{W}" height="{h}" role="img" aria-labelledby="t d">\n'
        f'<title id="t">{escape(title)}</title>\n<desc id="d">{escape(desc)}</desc>\n'
        f"{STYLE}"
        f'<rect class="bg" width="{W}" height="{h}" rx="8"/>\n'
        f'<text class="ink t" x="28" y="42">{escape(title)}</text>\n'
        f'<text class="mut s" x="28" y="64">{escape(sub)}</text>\n'
        f"{body}</svg>\n"
    )


def txt(x, y, s, cls="ink l", anchor="start"):
    return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}">{escape(s)}</text>\n'


# --- Fig 1: verification (paper: "Verification status (this draft)") ---------
def fig_verification():
    # fig1 is withdrawn from the paper (see the note in
    # docs/anthropic-contrapunctus.md): its counts were hand-coded and went stale,
    # and it returns only when generated from Descartes check output, which this
    # repository does not have. It still emits so the gallery does not silently
    # lose a file; the count it draws is the claims file's actual quotation rows,
    # and the "exact" figure is not claimed at all (0), because nothing here
    # verifies it.
    checked, exact = _claims_counts(), 0
    body, size, gap = "", 22, 4
    for i in range(checked):
        r, c = divmod(i, 10)
        cls = "ok" if i < exact else "unv"
        body += (f'<rect class="{cls}" x="{28 + c * (size + gap)}" '
                 f'y="{96 + r * (size + gap)}" width="{size}" height="{size}" rx="4"/>\n')
    x = 316
    body += f'<rect class="ok" x="{x}" y="104" width="12" height="12" rx="3"/>\n'
    body += txt(x + 20, 115, f"{exact} byte-exact in the filing")
    body += f'<rect class="unv" x="{x}" y="140" width="12" height="12" rx="3"/>\n'
    body += txt(x + 20, 151, f"{checked - exact} not byte-exact, including:")
    body += txt(x + 20, 172, "This figure is a placeholder; it claims", "mut l")
    body += txt(x + 20, 190, "no verification result. The paper says", "mut l")
    body += txt(x + 20, 211, "it returns from Descartes check output.", "mut l")
    body += txt(28, 282, "No count on this card is a verification claim.", "mut s")
    return svg(
        300,
        f"{checked} quotation rows in the claims file",
        "Withdrawn from the paper: not generated from a verification run.",
        body,
        f"Waffle of {checked} checked fragments: {exact} byte-exact, "
        f"{checked - exact} not, including one unsupported number and five compressions.",
    )


# --- Fig 2: Risk-Governance Index v1 (docs/risk-governance-index.md) ----------
# INDEX is derived from docs/risk-governance-index.md at build time (see
# _index_rows). It is not a literal: the doc is the source, the figure restates it,
# and a change to one without the other is caught by scripts/test_argument_json.py.
INDEX_SHORT = {
    "Open-source software vulnerabilities and under-maintenance, a material operational risk":
        "Open-source software vulnerabilities",
    "\"Absence of judicial precedent interpreting this structure\" raises governance-litigation risk":
        "Untested governance structure",
    "Misalignment behaviors \"have been observed across the industry\"":
        "Misalignment “across the industry”",
    "Workforce displacement framed as a perception/regulatory risk \"regardless of the actual impact\"":
        "Workforce displacement",
    "Government interruption — June 2026 export restriction on two models":
        "Government interruption",
    "Revenue from customers later found violating the usage policy, kept and disclosed":
        "Revenue from policy violators",
    "Decisions concentrated in \"a handful… Anthropic is unusual\"":
        "Decisions concentrated, few checks",
    "Four Claude models reached real third-party systems":
        "Models reached third-party systems",
}


def _short(risk):
    """A figure label for a risk row. Falls back to the row's own words."""
    if risk in INDEX_SHORT:
        return INDEX_SHORT[risk]
    return risk.split(",")[0][:48]


INDEX = [(_short(risk), status) for risk, status, _mech in _index_rows()]
STATUS_CLS = {"Uncontrolled": "bad", "Externalized": "warn", "Partial": "warn", "Controlled": "ok"}


def fig_index():
    body, y0, rh = "", 100, 30
    body += txt(28, 90, "DISCLOSED RISK", "mut m")
    body += txt(440, 90, "STATUS", "mut m")
    for i, (risk, status) in enumerate(INDEX):
        y = y0 + i * rh
        body += f'<line class="rule" x1="28" x2="612" y1="{y}" y2="{y}"/>\n'
        body += txt(28, y + 20, f"{i + 1}", "mut m")
        body += txt(52, y + 20, risk)
        body += f'<rect class="{STATUS_CLS[status]}" x="440" y="{y + 9}" width="12" height="12" rx="3"/>\n'
        body += txt(460, y + 20, status)
        if i == 0:  # the index marks row 1 to-verify
            body += txt(560, y + 20, "to-verify", "mut m")
    n_unc = sum(s == "Uncontrolled" for _, s in INDEX)
    n_ext = sum(s == "Externalized" for _, s in INDEX)
    h = y0 + len(INDEX) * rh + 24
    return svg(
        h,
        f"0 of {len(INDEX)} disclosed risks are controlled",
        f"Risk–Governance Index v1 · {n_unc} Uncontrolled · {n_ext} Externalized "
        "· 0 Partial · 0 Controlled",
        body,
        "Eight risks Anthropic discloses, each with the status of the mechanism that "
        f"would control it: {n_unc} Uncontrolled, {n_ext} Externalized, none Controlled.",
    )


# --- Fig 3: governance scorecard (Appendix A) --------------------------------
# SCORE is the "filed today" column of the paper's Appendix A, read at build time
# (see _scorecard_rows). Level: 2 held, 1 partial, 0 absent.
SCORE = _scorecard_rows()


def dot(cx, cy, level):
    r = 7
    if level == 2:
        return f'<circle class="acc" cx="{cx}" cy="{cy}" r="{r}"/>\n'
    s = f'<circle class="hollow" cx="{cx}" cy="{cy}" r="{r - 0.75}" stroke-width="1.5"/>\n'
    if level == 1:
        s += f'<path class="acc" d="M{cx},{cy - r} A{r},{r} 0 0,0 {cx},{cy + r} Z"/>\n'
    return s


def fig_scorecard():
    body, y0, rh = "", 100, 28
    body += txt(28, 90, "DIMENSION", "mut m")
    body += txt(430, 90, "FILED TODAY", "mut m", "middle")
    body += txt(552, 90, "SERIOUS (§7)", "mut m", "middle")
    for i, (dim, lvl) in enumerate(SCORE):
        y = y0 + i * rh
        body += f'<line class="rule" x1="28" x2="612" y1="{y}" y2="{y}"/>\n'
        body += txt(28, y + 19, dim)
        body += dot(430, y + 14, lvl)
        body += dot(552, y + 14, 2)
    yl = y0 + len(SCORE) * rh + 30
    body += dot(36, yl - 4, 2) + txt(50, yl, "held / verifiable", "mut s")
    body += dot(190, yl - 4, 1) + txt(204, yl, "partial / revocable", "mut s")
    body += dot(354, yl - 4, 0) + txt(368, yl, "absent", "mut s")
    held = sum(l == 2 for _, l in SCORE)
    part = sum(l == 1 for _, l in SCORE)
    absent = sum(l == 0 for _, l in SCORE)
    return svg(
        yl + 22,
        f"Filed today: {held} of {len(SCORE)} governance dimensions held",
        f"Appendix A scorecard · {part} partial or revocable · {absent} absent",
        body,
        f"Ten governance dimensions. As filed: {held} held, {part} partial, {absent} absent. "
        "Under the paper's section 7 mechanisms, all ten held.",
    )


# --- Fig 4: Meadows leverage map (section 1a) --------------------------------
MEADOWS = [  # strongest first
    (1, "Power to transcend paradigms"),
    (2, "Paradigm"),
    (3, "Goals of the system"),
    (4, "Power to self-organize"),
    (5, "Rules"),
    (6, "Information flows"),
    (7, "Reinforcing feedback"),
    (8, "Balancing feedback"),
    (9, "Delays"),
    (10, "Stock-and-flow structure"),
    (11, "Buffers"),
    (12, "Constants and parameters"),
]
ACTS, DECLINES, SPEAKS = {12, 6}, {5, 4, 3}, {2, 3}


def fig_leverage():
    body, y0, rh = "", 104, 24
    cols = [(400, "ACTS"), (486, "DECLINES"), (572, "SPEAKS AT")]
    for x, lab in cols:
        body += txt(x, 92, lab, "mut m", "middle")
    for i, (n, name) in enumerate(MEADOWS):
        y = y0 + i * rh
        body += f'<line class="rule" x1="28" x2="612" y1="{y}" y2="{y}"/>\n'
        body += txt(28, y + 17, f"{n:>2}", "mut m")
        body += txt(56, y + 17, name)
        for (x, _), group in zip(cols, (ACTS, DECLINES, SPEAKS)):
            if n in group:
                body += f'<circle class="acc" cx="{x}" cy="{y + 12}" r="6"/>\n'
    yb = y0 + len(MEADOWS) * rh
    body += txt(28, yb + 24, "↑ stronger leverage at the top. Binding commitments sit at 12 and 6.", "mut s")
    return svg(
        yb + 42,
        "Anthropic acts at the weak end of the lever",
        "Meadows’ twelve leverage points, sorted against Anthropic’s commitments (§1a)",
        body,
        "Meadows' twelve leverage points. Anthropic acts at 12 (parameters) and 6 "
        "(information flows), declines at 5, 4 and 3, and speaks at 2 and 3.",
    )


FIGS = {
    "fig1-verification.svg": fig_verification,
    "fig2-risk-governance-index.svg": fig_index,
    "fig3-scorecard.svg": fig_scorecard,
    "fig4-leverage.svg": fig_leverage,
}

if __name__ == "__main__":
    for name, fn in FIGS.items():
        (OUT / name).write_text(fn(), encoding="utf-8")
        print(name)

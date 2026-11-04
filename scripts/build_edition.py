#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "blake3==1.0.11",
#   "duckdb==2.0.0",
#   "matplotlib==3.10.7",
# ]
# ///
"""Build DECK.md as an edition of one source commit and one risk codebook.

    uv run scripts/build_edition.py --codebook v0.2-draft          # write DECK.md, deck/*.svg, deck/STAMP.json
    uv run scripts/build_edition.py --codebook v0.2-draft --check  # exit 1 if a rebuild would change anything

The build is the review step: it writes into the working tree and never commits.
Review `git diff`, then commit the edition yourself.

Preconditions (fail closed):
  - every dag.yml step is `ok` (Praxis dag.py status);
  - every input is committed and unmodified.

Display controls (docs/report-build.md; every one fails the build):
  1. Exact inputs. Every number shown is computed from integer counts by
     scripts/display.py: no float, and no rounded table column, is ever shown.
  2. One rounding rule: half up, from the exact fraction.
  3. One source per number. Every chart in the deck is drawn here, from the
     same registered values as the captions, so chart and caption cannot disagree.
  4. Provenance. Every displayed value is registered with its source file,
     computation, numerator and denominator, and written to the stamp.
  5. No unbound numerals. The template may contain no digits outside {{...}}
     (front matter excepted). Every numeral in the built DECK.md, and in every
     chart's text (axis tick labels excepted), must be a registered value.
  6. Quotes. Text in double quotes in the template must be a single quote
     binding, and every quote binding must occur verbatim in edition v0.
  7. Nothing clipped. Every text element of a matplotlib chart lies inside the
     figure. Every SVG parses as XML.
  8. One codebook. Every risk chart and number uses the --codebook given.
Positive = DeBERTa and ModernBERT both >= 0.5, everywhere.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from fractions import Fraction
from html import escape
from pathlib import Path

import blake3
import duckdb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import display  # noqa: E402

TEMPLATE = ROOT / "deck" / "deck.template.md"
OUT_DIR = ROOT / "deck"
EC = ROOT / "corpus" / "earnings-calls"
PAPER, PAPER_V0 = "docs/anthropic-contrapunctus.md", "1afb042"
DAG_TOOL = ROOT.parent / "praxis" / "datasets" / "dag.py"
FIRST_YEAR, CUTOFF_YEAR, TTM_MONTHS = 2013, 2023, 12
RISK_WORD = r"(?i)\brisk(s|y|ier|iest)?\b"
THRESHOLD = Fraction(1, 2)

CODEBOOKS = {
    "v0.2-draft": {
        "file": "corpus/codebooks/codebook-v0.2-draft.tsv",
        "ec_scores": "proposals/earnings-calls/codebook-v0.2-draft",
        "dialogue": "proposals/cross-source/codebook-v0.2-draft/report/dialogue-space.tsv",
        "status": " (DRAFT: wording awaits review)",
    },
}
QUESTIONS = {"codebook": "v0.1", "file": "corpus/earnings-calls/codebook-questions-v0.1.tsv",
             "ttm": "proposals/earnings-calls/codebook-questions-v0.1/report/ttm.tsv"}
CVE = "corpus/cve/monthly-ai.tsv"
QUOTES = {  # binding -> exact text in edition v0 (markdown emphasis and line breaks removed before matching)
    "q_toothless": "Anthropic's charter is legally real and legally toothless.",
    "q_365b": "§365(b) gives directors no duty to any person on account of a public-benefit interest",
    "q_33k": "33,000+",
}
STATIC_TOKENS = {"500"}   # "S&P 500" is a name, not a quantity
DIALOGUE_SOURCES = [("executives", "Executives (calls)"), ("analysts", "Analyst questions"),
                    ("hn_anthropic", "HN: Anthropic"), ("hn_security", "HN: AI security"), ("wikipedia", "Wikipedia")]
LABELS = {"regulation": "Regulation", "cyber": "Cybersecurity", "privacy": "Data privacy",
          "accuracy": "Accuracy / hallucination", "bias": "Bias / fairness", "labor": "Jobs / labor",
          "disruption": "Disruption of the business", "capex": "Overspending / capex return",
          "energy": "Energy / power", "supply": "Chip & supply constraints", "ip": "Intellectual property",
          "safety_ethics": "Safety / ethics / misuse"}
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
S1, S2, MUTED = "#2a78d6", "#eb6834", "#a8a69f"
META = {"Date": None, "Creator": None}

NUM = re.compile(r"\b(?=[0-9a-f]*[a-f])(?=[0-9a-f]*\d)[0-9a-f]{7,40}\b"   # commit ids
                 r"|\d{4}-\d{2}-\d{2}|\d{4}-\d{2}"                         # dates, months
                 r"|v\d+(?:\.\d+)+(?:-draft)?"                             # versions
                 r"|§\d+\([a-z]\)"                                         # statute sections
                 r"|\d[\d,]*(?:\.\d+)?\+?")                                # numbers


def tokens(s: str) -> set[str]:
    return {m.group(0).rstrip(",") for m in NUM.finditer(s)}


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def b3(p: Path) -> str:
    return blake3.blake3(p.read_bytes()).hexdigest()


def table(path: str) -> tuple[list[str], list[dict]]:
    with (ROOT / path).open() as f:
        lines = f.read().splitlines()
    comments = [l for l in lines if l.startswith("#")]
    return comments, list(csv.DictReader([l for l in lines if not l.startswith("#")], delimiter="\t"))


class Build:
    def __init__(self, codebook: str) -> None:
        self.codebook, self.cb = codebook, CODEBOOKS[codebook]
        self.reg = display.Registry()
        self.errs: list[str] = []
        self.outs: dict[str, bytes] = {}

    # ------------------------------------------------------------ preconditions
    def inputs(self) -> list[str]:
        return [self.cb["file"], self.cb["ec_scores"], self.cb["dialogue"], QUESTIONS["file"], QUESTIONS["ttm"], CVE,
                "corpus/earnings-calls/calls.tsv", "corpus/earnings-calls/ai-windows.parquet",
                "deck/deck.template.md", "scripts/build_edition.py", "scripts/display.py",
                "scripts/ec_question_report.py", "dag.lock.tsv"]

    def preflight(self) -> bool:
        r = subprocess.run(["uv", "run", "--quiet", str(DAG_TOOL), "status"], cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            self.errs.append("dag.py status is not all ok:\n" + "\n".join(
                l for l in r.stdout.splitlines() if not l.startswith("ok")))
        for p in self.inputs():
            if not git("ls-files", "--", p).strip():
                self.errs.append(f"input not committed: {p}")
        dirty = git("status", "--porcelain", "--", *self.inputs()).strip()
        if dirty:
            self.errs.append("inputs modified since the last commit:\n" + dirty)
        return not self.errs

    # ------------------------------------------------------------ checks
    def allowed(self) -> set[str]:
        out = set(STATIC_TOKENS)
        for t in self.reg.texts():
            out |= tokens(t)
        return out

    def check_text(self, where: str, s: str) -> None:
        bad = sorted(tokens(s) - self.allowed())
        if bad:
            self.errs.append(f"{where}: unregistered numerals {bad} in {s[:90]!r}")

    def save_fig(self, fig, name: str) -> None:
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_agg import FigureCanvasAgg   # SVG canvas cannot measure text
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        r = canvas.get_renderer()
        box = fig.bbox
        ticks = set()
        for ax in fig.axes:
            ticks |= set(ax.get_xticklabels()) | set(ax.get_yticklabels())
        for t in fig.findobj(matplotlib.text.Text):
            s = t.get_text()
            if not t.get_visible() or not s.strip():
                continue
            bb = t.get_window_extent(r)
            if bb.x0 < box.x0 - 0.5 or bb.y0 < box.y0 - 0.5 or bb.x1 > box.x1 + 0.5 or bb.y1 > box.y1 + 0.5:
                self.errs.append(f"{name}: text clipped at the figure edge: {s[:60]!r}")
            if t not in ticks:
                self.check_text(name, s)
        path = OUT_DIR / name
        fig.savefig(path, facecolor=SURFACE, metadata=META)
        plt.close(fig)
        ET.fromstring(path.read_bytes())
        self.outs[f"deck/{name}"] = path.read_bytes()

    def save_svg(self, svg: str, name: str) -> None:
        root = ET.fromstring(svg)
        for el in root.iter():
            if el.tag.split("}")[-1] in ("text", "title", "desc") and el.text:
                self.check_text(name, el.text)
        path = OUT_DIR / name
        path.write_text(svg)
        self.outs[f"deck/{name}"] = path.read_bytes()

    # ------------------------------------------------------------ values
    def register_static(self, head: str) -> None:
        R = self.reg
        R.put("codebook", self.codebook, source=self.cb["file"], how="--codebook")
        R.put("codebook_status", self.cb["status"], source="build_edition.CODEBOOKS", how="status of the codebook")
        R.put("question_codebook", QUESTIONS["codebook"], source=QUESTIONS["file"], how="question-intent codebook")
        R.put("source_commit", head[:12], source="git", how="HEAD at build time")
        R.put("paper_v0", PAPER_V0, source="git", how="edition v0 commit of the paper")
        R.put("paper_edition", "v0", source=f"{PAPER}@{PAPER_V0}", how="edition name of the hand-written paper")
        R.put("threshold", display.round_half_up(THRESHOLD, 1), source="build_edition.THRESHOLD", how="both witnesses >= this")
        R.put("ttm_months", str(TTM_MONTHS), source="build_edition.TTM_MONTHS", how="trailing window, months")
        R.put("ec_cutoff_year", str(CUTOFF_YEAR), source="build_edition.CUTOFF_YEAR", how="comparison year")
        new = {r["status"].split()[0] for r in table(self.cb["file"])[1] if r["status"].startswith("v0.2")}
        for i, v in enumerate(sorted(new)):
            R.put(f"new_tag_{i}", v, source=self.cb["file"], how="status column of hypotheses new in this codebook")
        text = re.sub(r"\s+", " ", git("show", f"{PAPER_V0}:{PAPER}").replace("**", "").replace("*", ""))
        for k, q in QUOTES.items():
            if q not in text:
                self.errs.append(f"quote {k} not found verbatim in {PAPER}@{PAPER_V0}: {q!r}")
            R.put(k, q, source=f"{PAPER}@{PAPER_V0}", how="verbatim quote (emphasis and line breaks removed)")

    # ------------------------------------------------------------ earnings calls
    def earnings(self) -> None:
        R, cb = self.reg, self.cb
        scores = ROOT / cb["ec_scores"]
        con = duckdb.connect()
        as_of = str(con.execute(f"SELECT max(report_date) FROM read_csv('{EC / 'calls.tsv'}')").fetchone()[0])
        R.put("as_of", as_of, source="corpus/earnings-calls/calls.tsv", how="max(report_date)")

        def flags(h: str) -> str:
            return (f"SELECT d.window_id FROM '{scores / 'deberta.parquet'}' d JOIN '{scores / 'modernbert.parquet'}' m "
                    f"USING (window_id, hypothesis_id) WHERE d.hypothesis_id = '{h}' "
                    f"AND d.p_entail >= {float(THRESHOLD)} AND m.p_entail >= {float(THRESHOLD)}")
        cbrows = table(cb["file"])[1]
        types = [r["id"] for r in cbrows if r["group"] == "risk_type"]
        new = {r["id"] for r in cbrows if r["status"].startswith("v0.2")}
        con.execute(f"""CREATE TABLE calls AS SELECT symbol, fiscal_year, fiscal_quarter, report_date
            FROM read_csv('{EC / "calls.tsv"}')
            WHERE (duplicate_of IS NULL OR duplicate_of = '') AND n_paragraphs > 2 AND report_date <= DATE '{as_of}'""")
        con.execute(f"""CREATE TABLE w AS SELECT window_id, symbol, fiscal_year, fiscal_quarter,
                report_date::DATE AS report_date, regexp_matches(text, '{RISK_WORD}') AS lex,
                window_id IN ({flags('ai_risk')}) AS ai_risk
            FROM '{EC / "ai-windows.parquet"}'""")
        con.execute("""CREATE TABLE cw AS SELECT c.*, bool_or(w.lex) AS lex, bool_or(w.ai_risk) AS nli
            FROM calls c LEFT JOIN w USING (symbol, fiscal_year, fiscal_quarter) GROUP BY ALL""")
        series = con.execute(f"""SELECT year(report_date)::INT, count(*)::INT,
                (count(*) FILTER (WHERE lex))::INT, (count(*) FILTER (WHERE nli))::INT
            FROM cw WHERE year(report_date) >= {FIRST_YEAR} GROUP BY 1 ORDER BY 1""").fetchall()
        src = f"corpus/earnings-calls/{{calls.tsv,ai-windows.parquet}} + {cb['ec_scores']}"
        for y, n, lex, nli in series:
            R.pct(f"ec_lex_{y}", lex, n, 1, source=src, how=f"{y}: calls with a 'risk' word in an AI window / calls")
            R.pct(f"ec_nli_{y}", nli, n, 1, source=src, how=f"{y}: calls with an ai_risk window (both witnesses) / calls")
        last = series[-1]
        R.put("ec_year_last", str(last[0]), source=src, how="last calendar year in the series")
        R.put("ec_pct_witness_last", R.values[f"ec_nli_{last[0]}"]["text"], source=src, how="= ec_nli_<last year>")
        pre = max((r for r in series if r[0] < CUTOFF_YEAR), key=lambda r: Fraction(r[3], r[1]))
        R.put("ec_pre2023_max", R.values[f"ec_nli_{pre[0]}"]["text"], source=src,
              how=f"max over years < {CUTOFF_YEAR} of ec_nli_<year> (attained {pre[0]})")

        since = f"DATE '{as_of}' - INTERVAL {TTM_MONTHS} MONTH"
        con.execute(f"CREATE TABLE ttm AS SELECT * FROM w WHERE report_date > {since} AND report_date <= DATE '{as_of}' AND ai_risk")
        ranking = []
        for t in types:
            firms = con.execute(f"SELECT count(DISTINCT symbol)::INT FROM ttm WHERE window_id IN ({flags(t)})").fetchone()[0]
            lab = LABELS.get(t, t) + (" *" if t in new else "")
            ranking.append((t, lab, firms))
            R.count(f"ec_rank_{t}", firms, source=src, how=f"firms with a window both ai_risk and {t}, trailing window")
        ranking.sort(key=lambda r: (-r[2], r[0]))
        R.count("ec_ttm_risk_firms", con.execute("SELECT count(DISTINCT symbol)::INT FROM ttm").fetchone()[0],
                source=src, how="firms with >= 1 ai_risk window, trailing window")
        R.put("ec_top3", ", ".join(f"{LABELS.get(r[0], r[0])} ({R.values[f'ec_rank_{r[0]}']['text']})" for r in ranking[:3]),
              source=src, how="top three of the ranking")
        self.plot_series(series)
        self.plot_ranking(ranking)

    def mpl(self):
        import matplotlib
        matplotlib.use("svg")
        import matplotlib.pyplot as plt
        plt.rcParams.update({"svg.hashsalt": "edition", "font.family": "DejaVu Sans", "font.size": 10,
                             "axes.edgecolor": INK2, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
        return matplotlib, plt

    @staticmethod
    def style(ax) -> None:
        ax.set_facecolor(SURFACE)
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(length=0)

    def plot_series(self, series) -> None:
        R = self.reg
        matplotlib, plt = self.mpl()
        fig, ax = plt.subplots(figsize=(8, 4.4), facecolor=SURFACE)
        self.style(ax)
        years = [r[0] for r in series]
        for key, col, color, name in (("lex", 2, S1, 'Mentions "risk" next to AI (no model)'),
                                      ("nli", 3, S2, f"Both models: AI framed as a risk ({self.codebook})")):
            ys = [float(Fraction(100 * r[col], r[1])) for r in series]   # positions only; labels are registered text
            ax.plot(years, ys, color=color, lw=2, marker="o", ms=4.5, mec=SURFACE, mew=1.5, label=name)
            ax.annotate(R.values[f"ec_{key}_{years[-1]}"]["text"] + "%", (years[-1], ys[-1]), xytext=(8, 0),
                        textcoords="offset points", va="center", color=INK, fontsize=10, fontweight="bold")
        ax.set_xticks(years, [str(y) if y != years[-1] else f"{y}\n(to {R.values['as_of']['text'][5:]})" for y in years],
                      fontsize=9)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        ax.set_ylim(0, None)
        ax.set_xlim(years[0] - 0.5, years[-1] + 1.2)
        ax.set_title("Share of S&P 500 earnings calls where AI is discussed as a risk", loc="left",
                     color=INK, fontsize=12, fontweight="bold", pad=22)
        ax.text(0, 1.02, "Calls per calendar year; denominator: every unique, non-stub S&P 500 call in the corpus",
                transform=ax.transAxes, color=INK2, fontsize=9)
        ax.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=INK)
        fig.text(0.01, 0.01, f"Source: defeatbeta/yahoo-finance-data transcripts (ODC-BY). Model line: risk codebook "
                 f"{self.codebook}; witness proposal, not hand-verified.", color=INK2, fontsize=7.5)
        fig.tight_layout(rect=(0, 0.03, 1, 1))
        self.save_fig(fig, "ai-risk-by-year.svg")

    def plot_ranking(self, ranking) -> None:
        R = self.reg
        matplotlib, plt = self.mpl()
        shown = [r for r in ranking if r[2] > 0][::-1]
        fig, ax = plt.subplots(figsize=(8, 0.36 * len(shown) + 1.6), facecolor=SURFACE)
        ax.set_facecolor(SURFACE)
        ax.barh([r[1] for r in shown], [r[2] for r in shown], color=S1, height=0.62)
        for i, r in enumerate(shown):
            ax.text(r[2] + 0.4, i, R.values[f"ec_rank_{r[0]}"]["text"], va="center", color=INK, fontsize=9)
        for s in ("top", "right", "bottom"):
            ax.spines[s].set_visible(False)
        ax.set_xticks([])
        ax.tick_params(length=0, labelsize=9.5, labelcolor=INK)
        ax.set_title(f"AI risks raised on S&P 500 calls, {TTM_MONTHS} months to {R.values['as_of']['text']}",
                     loc="left", color=INK, fontsize=12, fontweight="bold", pad=30)
        ax.text(0, 1.01, f"Number of companies; both models must propose the window.\nRisk codebook {self.codebook}; "
                f"* = new in {R.values['new_tag_0']['text']}.", transform=ax.transAxes, color=INK2, fontsize=8.5)
        fig.tight_layout()
        self.save_fig(fig, "risk-ranking-ttm.svg")

    # ------------------------------------------------------------ analyst questions
    def questions(self) -> None:
        R = self.reg
        comments, rows = table(QUESTIONS["ttm"])
        m = re.fullmatch(r"# (\d+) months to (\d{4}-\d{2}-\d{2}): (\d+) AI questions from .*", comments[0])
        if not m or int(m.group(1)) != TTM_MONTHS or m.group(2) != R.values["as_of"]["text"]:
            self.errs.append(f"{QUESTIONS['ttm']}: header does not state {TTM_MONTHS} months to the same as-of: {comments[:1]}")
            return
        n_q = int(m.group(3))
        R.count("q_n", n_q, source=QUESTIONS["ttm"], how="AI questions in the trailing window (header)")
        import ec_question_report as qr
        out = []
        for r in rows:
            k = int(r["questions"])
            p = R.pct(f"q_{r['intent'][2:]}_pct", k, n_q, 1, source=QUESTIONS["ttm"], how=f"questions with {r['intent']} / q_n")
            R.count(f"q_{r['intent'][2:]}_n", k, source=QUESTIONS["ttm"], how=f"questions with {r['intent']}")
            out.append((r["intent"], k, Fraction(100 * k, n_q), p))
        matplotlib, plt = self.mpl()
        group = {h: ("oversight" if h in qr.OVERSIGHT else "commercial" if h in qr.COMMERCIAL + ["q_spend"] else "other")
                 for h, *_ in out}
        color = {"commercial": S1, "oversight": S2, "other": MUTED}
        shown = out[::-1]
        fig, ax = plt.subplots(figsize=(8, 0.42 * len(shown) + 1.7), facecolor=SURFACE)
        ax.set_facecolor(SURFACE)
        ax.barh([qr.LABELS[h] for h, *_ in shown], [float(p) for _, _, p, _ in shown],
                color=[color[group[h]] for h, *_ in shown], height=0.62)
        for i, (h, k, p, txt) in enumerate(shown):
            ax.text(float(p) + 0.3, i, f"{txt}%  ({display.count(k)})", va="center", color=INK, fontsize=9)
        for s in ("top", "right", "bottom"):
            ax.spines[s].set_visible(False)
        ax.spines["left"].set_color(INK2)
        ax.set_xticks([])
        ax.tick_params(length=0, labelsize=9.5, labelcolor=INK)
        from matplotlib.patches import Patch
        ax.legend(handles=[Patch(color=S1, label="Selling it / spending on it"), Patch(color=S2, label="Governing its risks"),
                           Patch(color=MUTED, label="Other")], loc="lower right", frameon=False, fontsize=9, labelcolor=INK)
        ax.set_title("What analysts ask S&P 500 companies about AI", loc="left", color=INK, fontsize=12,
                     fontweight="bold", pad=20)
        ax.text(0, 1.01, f"Share of {R.values['q_n']['text']} analyst questions on AI, {TTM_MONTHS} months to "
                f"{R.values['as_of']['text']}", transform=ax.transAxes, color=INK2, fontsize=9)
        fig.text(0.01, 0.01, f"A question can count under several topics. Both NLI models must agree; not hand-verified.\n"
                 f"Question codebook {QUESTIONS['codebook']}. Source: defeatbeta/yahoo-finance-data (ODC-BY).",
                 color=INK2, fontsize=7)
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        self.save_fig(fig, "intent-ttm.svg")

    # ------------------------------------------------------------ cross-source dialogue space
    def dialogue(self) -> None:
        R, cb = self.reg, self.cb
        _, rows = table(cb["dialogue"])
        base = next(r for r in rows if r["risk_type"] == "ai_risk_units")
        bases = {k: int(base[f"{k}_n"]) for k, _ in DIALOGUE_SOURCES}
        types = [r for r in rows if r["risk_type"] != "ai_risk_units"]
        for k, _ in DIALOGUE_SOURCES:
            R.count(f"ds_base_{k}", bases[k], source=cb["dialogue"], how=f"{k} AI-risk units")
        for r in types:
            for k, _ in DIALOGUE_SOURCES:
                n = int(r[f"{k}_n"])
                R.pct(f"ds_{k}_{r['risk_type']}", n, bases[k], 0, source=cb["dialogue"], how=f"{k}: {r['risk_type']} / AI-risk units")
                R.pct(f"ds1_{k}_{r['risk_type']}", n, bases[k], 1, source=cb["dialogue"], how="same, one decimal (tooltip)")
                R.count(f"dsn_{k}_{r['risk_type']}", n, source=cb["dialogue"], how=f"{k}: {r['risk_type']} units")
        for key, (src, t) in {"ds_exec_safety": ("executives", "safety_ethics"), "ds_hn_safety": ("hn_anthropic", "safety_ethics"),
                              "ds_wp_safety": ("wikipedia", "safety_ethics"), "ds_sec_cyber": ("hn_security", "cyber")}.items():
            R.put(key, R.values[f"ds_{src}_{t}"]["text"], source=cb["dialogue"], how=f"= ds_{src}_{t}")
        rows_sorted = sorted(types, key=lambda r: (-max(Fraction(int(r[f'{k}_n']), bases[k]) for k, _ in DIALOGUE_SOURCES),
                                                   r["risk_type"]))
        cw, rh, left, top = 128, 24, 210, 108
        W, H = left + cw * len(DIALOGUE_SOURCES) + 24, top + rh * len(rows_sorted) + 64

        def fill(n: int, d: int) -> str:
            t = min(Fraction(100 * n, d) / 50, Fraction(1))
            lo, hi = (236, 243, 249), (16, 70, 120)
            return "#%02x%02x%02x" % tuple(int(display.round_half_up(a + (b - a) * t, 0)) for a, b in zip(lo, hi))
        new = {r["risk_type"] for r in rows if r.get("new_in_v0.2") == "yes"}
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="system-ui,-apple-system,sans-serif" role="img">',
             '<style>text{fill:#1b1b1b}.m{fill:#5f6368}</style>', f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>',
             '<text x="16" y="30" font-size="18" font-weight="600">Who talks about which AI risks</text>',
             f'<text x="16" y="52" font-size="12" class="m">Share of each source\'s AI-risk passages naming each type. '
             f'Risk codebook {escape(self.codebook)}; * = new in {R.values["new_tag_0"]["text"]}.</text>']
        for j, (k, label) in enumerate(DIALOGUE_SOURCES):
            x = left + j * cw + cw / 2
            o.append(f'<text x="{x}" y="{top - 24}" font-size="12" font-weight="600" text-anchor="middle">{escape(label)}</text>')
            o.append(f'<text x="{x}" y="{top - 9}" font-size="11" class="m" text-anchor="middle">n = {R.values[f"ds_base_{k}"]["text"]}</text>')
        for i, r in enumerate(rows_sorted):
            t = r["risk_type"]
            y = top + i * rh
            o.append(f'<text x="{left - 8}" y="{y + rh / 2 + 4}" font-size="12" text-anchor="end">{escape(t)}{" *" if t in new else ""}</text>')
            for j, (k, label) in enumerate(DIALOGUE_SOURCES):
                n, d = int(r[f"{k}_n"]), bases[k]
                ink = "#ffffff" if Fraction(100 * n, d) >= 25 else "#1b1b1b"
                o.append(f'<g><title>{escape(label)}: {escape(t)} {R.values[f"ds1_{k}_{t}"]["text"]}% '
                         f'({R.values[f"dsn_{k}_{t}"]["text"]} of {R.values[f"ds_base_{k}"]["text"]})</title>'
                         f'<rect x="{left + j * cw + 1}" y="{y + 1}" width="{cw - 2}" height="{rh - 2}" rx="2" fill="{fill(n, d)}"/>'
                         f'<text x="{left + j * cw + cw / 2}" y="{y + rh / 2 + 4}" font-size="11" text-anchor="middle" '
                         f'style="fill:{ink}">{R.values[f"ds_{k}_{t}"]["text"]}</text></g>')
        o.append(f'<text x="16" y="{H - 30}" font-size="11" class="m">n = passages both NLI witnesses score ≥ '
                 f'{R.values["threshold"]["text"]} on ai_risk; a cell needs both on the type too. A passage can name several types.</text>')
        o.append(f'<text x="16" y="{H - 14}" font-size="11" class="m">Windows as in {escape(cb["dialogue"])}. '
                 'Witness proposals, no gold set.</text>')
        o.append("</svg>")
        self.save_svg("\n".join(o) + "\n", "dialogue-space.svg")

    # ------------------------------------------------------------ CVE
    def cve(self) -> None:
        R = self.reg
        _, rows = table(CVE)
        R.count("cve_claude_total", sum(int(r["n_credit_claude"]) for r in rows), source=CVE, how="sum n_credit_claude, all months")
        R.count("cve_ai_total", sum(int(r["n_ai_credited"]) for r in rows), source=CVE, how="sum n_ai_credited, all months")
        R.put("cve_first", rows[0]["month"], source=CVE, how="first month")
        R.put("cve_last", rows[-1]["month"], source=CVE, how="last month")
        r = [x for x in rows if x["month"] >= "2023-01"]
        R.put("cve_chart_first", r[0]["month"], source=CVE, how="first month charted")
        months = [x["month"] for x in r]
        pub = [int(x["n_published"]) for x in r]
        ai = [int(x["n_ai_credited"]) for x in r]
        claude = [int(x["n_credit_claude"]) for x in r]
        R.count("cve_last_pub", pub[-1], source=CVE, how="n_published, last month")
        R.count("cve_last_ai", ai[-1], source=CVE, how="n_ai_credited, last month")
        R.count("cve_last_claude", claude[-1], source=CVE, how="n_credit_claude, last month")
        matplotlib, plt = self.mpl()
        xs = range(len(months))
        ticks = [i for i, m in enumerate(months) if m.endswith("-01")]
        fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6.2), facecolor=SURFACE, sharex=True, gridspec_kw={"hspace": 0.45})
        self.style(a1)
        a1.bar(xs, pub, color=S1, width=0.78)
        a1.annotate(R.values["cve_last_pub"]["text"], (xs[-1], pub[-1]), xytext=(-2, 4), textcoords="offset points",
                    ha="right", color=INK, fontsize=9, fontweight="bold")
        a1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        a1.set_title("CVEs published per month", loc="left", color=INK, fontsize=11, fontweight="bold")
        self.style(a2)
        a2.bar(xs, claude, color=S2, width=0.78, label="Credit names Claude")
        a2.bar(xs, [a - c for a, c in zip(ai, claude)], bottom=claude, color=MUTED, width=0.78,
               label="Credit names another AI system or term")
        a2.annotate(f"{R.values['cve_last_ai']['text']} ({R.values['cve_last_claude']['text']} Claude)", (xs[-1], ai[-1]),
                    xytext=(-4, 4), textcoords="offset points", ha="right", color=INK, fontsize=9, fontweight="bold")
        a2.set_title("CVEs whose credits name an AI system, per month", loc="left", color=INK, fontsize=11, fontweight="bold")
        a2.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=INK)
        a2.set_xticks(ticks, [months[i][:4] for i in ticks])
        fig.suptitle("Vulnerability disclosures, and the share credited to AI", x=0.01, ha="left",
                     color=INK, fontsize=13, fontweight="bold")
        fig.text(0.01, 0.01, f"Source: CVEProject/cvelistV5 baseline {R.values['as_of']['text']} (corpus/cve), "
                 f"{R.values['cve_chart_first']['text']} to {R.values['cve_last']['text']}.\n"
                 "Credit = the CNA credits field only, matched to named AI systems. Method credit: Epoch AI (CC BY).",
                 color=INK2, fontsize=7)
        fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.12)
        self.save_fig(fig, "cve-ai-credit.svg")

    # ------------------------------------------------------------ deck
    def render(self, head: str) -> None:
        tpl = TEMPLATE.read_text()
        fm_end = tpl.index("\n---\n", 4) + 5
        first = tpl[:fm_end].count("\n") + 1
        for i, line in enumerate(tpl[fm_end:].splitlines(), first):
            bare = re.sub(r"\{\{\w+\}\}", "", re.sub(r"<!--.*?-->", "", line))
            bare = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", bare)   # image directives (w:900) are layout, not data
            bad = sorted(tokens(bare) - STATIC_TOKENS)
            if bad:
                self.errs.append(f"deck.template.md:{i}: hand-typed numerals {bad}")
            for q in re.findall(r'"([^"]*)"', re.sub(r"<[^>]+>", "", line)):
                if not re.fullmatch(r"\{\{q_\w+\}\}", q):
                    self.errs.append(f"deck.template.md:{i}: quoted text must be one quote binding: \"{q}\"")
        self.reg.put("generated_notice", f"<!-- GENERATED by scripts/build_edition.py --codebook {self.codebook} from {head}. "
                     "Edit deck/deck.template.md, not this file. -->", source="build", how="notice")
        vals = {k: v["text"] for k, v in self.reg.values.items()}
        missing = sorted(set(re.findall(r"\{\{(\w+)\}\}", tpl)) - set(vals))
        self.errs += [f"unresolved binding {{{{{m}}}}}" for m in missing]
        md = re.sub(r"\{\{(\w+)\}\}", lambda m: vals.get(m.group(1), m.group(0)), tpl)
        out_body = re.sub(r"<!--.*?-->", "", md[md.index("\n---\n", 4) + 5:], flags=re.S)
        out_body = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", out_body)
        self.check_text("DECK.md", out_body)
        self.outs["DECK.md"] = md.encode()

    def run(self) -> tuple[dict[str, bytes], list[str]]:
        display.selftest()
        if not self.preflight():
            return {}, self.errs
        head = git("rev-parse", "HEAD").strip()
        OUT_DIR.mkdir(exist_ok=True)
        self.register_static(head)
        self.earnings()
        self.questions()
        self.dialogue()
        self.cve()
        self.render(head)
        stamp = {
            "edition_of": head,
            "codebook": {"risk": self.codebook, "risk_file": self.cb["file"], "risk_blake3": b3(ROOT / self.cb["file"]),
                         "question_intents": QUESTIONS["file"]},
            "rule": f"positive = DeBERTa and ModernBERT both >= {self.reg.values['threshold']['text']}",
            "rounding": "half up from the exact fraction of integer counts (scripts/display.py)",
            "dag_lock_blake3": b3(ROOT / "dag.lock.tsv"),
            "paper_v0": f"{PAPER}@{PAPER_V0}",
            "tools": {"python": "duckdb==2.0.0 matplotlib==3.10.7 blake3==1.0.11",
                      "render": "npx @marp-team/marp-cli@4.1.2 DECK.md --pptx --allow-local-files"},
            "values": {k: v for k, v in sorted(self.reg.values.items()) if k != "generated_notice"},
            "inputs": {p: b3(ROOT / p) for p in sorted(self.inputs()) if (ROOT / p).is_file()},
            "outputs": {k: blake3.blake3(v).hexdigest() for k, v in sorted(self.outs.items())},
        }
        self.outs["deck/STAMP.json"] = (json.dumps(stamp, indent=2, ensure_ascii=False) + "\n").encode()
        return self.outs, self.errs


OUTPUTS = ["DECK.md", "deck/STAMP.json", "deck/ai-risk-by-year.svg", "deck/risk-ranking-ttm.svg",
           "deck/intent-ttm.svg", "deck/dialogue-space.svg", "deck/cve-ai-credit.svg"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--codebook", required=True, choices=sorted(CODEBOOKS))
    ap.add_argument("--check", action="store_true", help="rebuild and compare; leave the tree unchanged")
    a = ap.parse_args()
    before = {p: (ROOT / p).read_bytes() for p in OUTPUTS if (ROOT / p).exists()}

    def restore() -> None:
        for p in OUTPUTS:
            if p in before:
                (ROOT / p).write_bytes(before[p])
            elif (ROOT / p).exists():
                (ROOT / p).unlink()
    outs, errs = Build(a.codebook).run()
    if errs:
        restore()
        print("build failed:\n  " + "\n  ".join(errs), file=sys.stderr)
        return 1
    if a.check:
        diff = sorted(p for p in OUTPUTS if before.get(p) != outs.get(p))
        restore()
        print("edition is current" if not diff else "edition would change: " + ", ".join(diff))
        return 1 if diff else 0
    for p, v in outs.items():
        (ROOT / p).write_bytes(v)
    print(f"built edition of {json.loads(outs['deck/STAMP.json'])['edition_of'][:12]} with risk codebook "
          f"{a.codebook}. Review `git diff`, then commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

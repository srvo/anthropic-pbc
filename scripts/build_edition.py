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
  5. No unbound numerals, checked by identity. The template may contain no
     digits outside {{...}}. Every numeral in a built DECK.md line must come
     from a binding used on that template line; every numeral in a chart
     string must come from the bindings that string was built from (say()).
     Checked channels: body, HTML comments (presenter notes), image alt text,
     front-matter title/description/header/footer, SVG text/tspan/tail/
     comments/aria-label, and fixed tick labels (scale ticks excepted).
  6. Quotes. Quoted text in the template (straight or curly, double or single
     quotes, markdown or HTML blockquotes) must be a single quote binding, and
     every quote binding must occur verbatim in edition v0. A quote from the
     paper's claims table also binds the status the paper gives it. A binding
     that copies another (Registry.copy) carries its n and d.
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
import ec_text as ect  # noqa: E402  (window text is local: .eccorpus/, joined on window_id)

TEMPLATE = ROOT / "deck" / "deck.template.md"
OUT_DIR = ROOT / "deck"
EC = ROOT / "corpus" / "earnings-calls"
PAPER, PAPER_V0 = "docs/anthropic-contrapunctus.md", "1afb042"
DAG_TOOL = ROOT.parent / "praxis" / "datasets" / "dag.py"
FIRST_YEAR, CUTOFF_YEAR, TTM_MONTHS = 2013, 2023, 12
RISK_WORD = r"(?i)\brisk(s|y|ier|iest)?\b"
THRESHOLD = Fraction(1, 2)
# Who speaks for the firm: the corpus's speaker-role heuristic (docs/earnings-call-ai-corpus.md section 4).
# Analysts' questions and the operator are not the firm's words.
COMPANY_SPEAKERS = "role = 'issuer_heuristic'"

CODEBOOKS = {
    "v0.2-draft": {
        "file": "corpus/codebooks/codebook-v0.2-draft.tsv",
        "ec_scores": "proposals/earnings-calls/codebook-v0.2-draft",
        "dialogue": "proposals/cross-source/codebook-v0.2-draft/report/dialogue-space.tsv",
        "status": " (DRAFT: wording awaits review)",
    },
}
QUESTIONS = {"codebook": "v0.1", "file": "corpus/earnings-calls/codebook-questions-v0.1.tsv",
             "ttm": "proposals/earnings-calls/codebook-questions-v0.1/report/ttm.tsv",
             "scores": "proposals/earnings-calls/codebook-questions-v0.1",
             "units": "corpus/earnings-calls/ai-questions.parquet"}
CVE, CVE_MANIFEST = "corpus/cve/monthly-ai.tsv", "corpus/cve/MANIFEST.tsv"
QUOTES = {  # binding -> exact text in edition v0 (markdown emphasis and line breaks removed before matching)
    "q_toothless": "Anthropic's charter is legally real and legally toothless.",
    "q_365b": "§365(b) gives directors no duty to any person on account of a public-benefit interest",
    "q_33k": ">33,000 critical- and high-severity flaws",
}
QUOTE_STATUS = {"q_33k"}   # quotes from the paper's claims table: also bind the status the paper gives them
QUOTED = re.compile(r'"([^"\n]*)"|\u201c([^\u201d\n]*)\u201d'           # straight and curly double quotes
                    r"|(?<!\w)['\u2018]([^'\u2019\n]+?)['\u2019](?!\w)")    # single quotes; apostrophes sit inside words
QUOTE_BINDING = re.compile(r"\{\{q_\w+\}\}")
STATIC_NAMES = re.compile(r"S&P 500|CVEProject/cvelistV5")   # names, not quantities: removed before numerals are read
FM_CHECKED = re.compile(r"^(title|description|header|footer|author|keywords|lang)\s*:")   # front-matter text that ships
MARP_ALT_KEYWORD = re.compile(r"[\d.]+%|(?:w|h|width|height):\S+")   # alt tokens Marp consumes
MARP_SIZE = re.compile(r"(?<!\S)(?:w|h|width|height):\d+(?:px|%)?(?!\S)")   # image-size keywords in alt text: layout
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
                 r"|[-\u2212]?\d[\d,]*(?:\.\d+)?\+?")                       # numbers, minus sign kept


def tokens(s: str) -> set[str]:
    return {m.group(0).rstrip(",") for m in NUM.finditer(STATIC_NAMES.sub("", s))}


def keys_in(s: str) -> list[str]:
    return re.findall(r"\{\{(\w+)\}\}", s)


def git(*a: str, cwd: Path = ROOT) -> str:
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=True).stdout


def source_commit(paths: list[str], cwd: Path = ROOT) -> str:
    """The last commit that touched any build input. Not HEAD: committing the edition's own
    outputs moves HEAD but changes no input, so the edition stays an edition of the same
    source commit and `--check` still passes after the edition is committed."""
    return git("log", "-1", "--format=%H", "--", *paths, cwd=cwd).strip()


def b3(p: Path) -> str:
    return blake3.blake3(p.read_bytes()).hexdigest()


def table(path: str) -> tuple[list[str], list[dict]]:
    with (ROOT / path).open() as f:
        lines = f.read().splitlines()
    comments = [l for l in lines if l.startswith("#")]
    return comments, list(csv.DictReader([l for l in lines if not l.startswith("#")], delimiter="\t"))


def cve_baseline(manifest: Path) -> str:
    """The CVE snapshot's own date: the `pinned` column of the manifest's baseline row."""
    with manifest.open() as f:
        rows = [r for r in csv.DictReader(f, delimiter="\t") if r["id"] == "baseline"]
    if len(rows) != 1 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", rows[0].get("pinned") or ""):
        raise ValueError(f"{manifest}: need exactly one baseline row with a pinned date")
    return rows[0]["pinned"]


class Build:
    def __init__(self, codebook: str) -> None:
        self.codebook, self.cb = codebook, CODEBOOKS[codebook]
        self.reg = display.Registry()
        self.errs: list[str] = []
        self.outs: dict[str, bytes] = {}
        self.bound: dict[str, set[str]] = {}   # chart string -> the binding keys it was built from

    # ------------------------------------------------------------ preconditions
    def inputs(self) -> list[str]:
        return [self.cb["file"], self.cb["ec_scores"], self.cb["dialogue"], QUESTIONS["file"], QUESTIONS["ttm"], CVE,
                QUESTIONS["scores"], QUESTIONS["units"],
                "corpus/earnings-calls/calls.tsv", "corpus/earnings-calls/ai-windows.parquet",
                "deck/deck.template.md", "scripts/build_edition.py", "scripts/display.py",
                "scripts/ec_question_report.py", "dag.lock.tsv", CVE_MANIFEST]

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
    def allowed(self, keys) -> set[str]:
        """Numerals the given bindings supply. A composite binding supplies only its parts'."""
        out: set[str] = set()
        for k in keys:
            v = self.reg.values.get(k)
            if v is None:
                self.errs.append(f"unknown binding {k}")
            else:
                out |= self.allowed(v["parts"]) if "parts" in v else tokens(v["text"])
        return out

    def say(self, fmt: str) -> str:
        """Chart text from bindings: '{key}' placeholders are filled with registered text, and
        every numeral in the result is later checked against those keys only."""
        keys = re.findall(r"\{(\w+)\}", fmt)
        s = fmt.format(**{k: self.reg.values[k]["text"] for k in keys})
        self.bound.setdefault(s, set()).update(keys)
        return s

    def compose(self, key: str, fmt: str, *, source: str, how: str) -> str:
        """Register a value built from other bindings; its numerals must all come from them."""
        if key.startswith("alt_"):
            # Marp reads a bare "12.2%" in image alt text as a size keyword and drops it.
            fmt = fmt.replace("}%", "} per cent")
        s = self.say(fmt)
        if key.startswith("alt_") and (bad := [t for t in s.split() if MARP_ALT_KEYWORD.fullmatch(t)]):
            self.errs.append(f"binding {key}: Marp would drop {bad} from the alt text")
        parts = sorted(self.bound[s])
        self.reg.put(key, s, source=source, how=how)
        self.reg.values[key]["parts"] = parts
        self.check_text(f"binding {key}", s, parts)
        return s

    def check_text(self, where: str, s: str, keys=None) -> None:
        """Every numeral in s must come from the bindings s was built from, not from any binding."""
        keys = self.bound.get(s, set()) if keys is None else keys
        bad = sorted(tokens(s) - self.allowed(keys))
        if bad:
            self.errs.append(f"{where}: numerals {bad} not supplied by its bindings {sorted(keys)} in {s[:90]!r}")

    def save_fig(self, fig, name: str) -> None:
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_agg import FigureCanvasAgg   # SVG canvas cannot measure text
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        r = canvas.get_renderer()
        box = fig.bbox
        scale = set()   # tick labels a formatter computes from the axis scale are layout, not data
        for ax in fig.axes:
            for axis, labels in ((ax.xaxis, ax.get_xticklabels()), (ax.yaxis, ax.get_yticklabels())):
                if isinstance(axis.get_major_formatter(), (matplotlib.ticker.FuncFormatter, matplotlib.ticker.ScalarFormatter)):
                    scale |= set(labels)
        for t in fig.findobj(matplotlib.text.Text):
            s = t.get_text()
            if not t.get_visible() or not s.strip():
                continue
            bb = t.get_window_extent(r)
            if bb.x0 < box.x0 - 0.5 or bb.y0 < box.y0 - 0.5 or bb.x1 > box.x1 + 0.5 or bb.y1 > box.y1 + 0.5:
                self.errs.append(f"{name}: text clipped at the figure edge: {s[:60]!r}")
            if t not in scale:
                self.check_text(name, s)
        path = OUT_DIR / name
        fig.savefig(path, facecolor=SURFACE, metadata=META)
        plt.close(fig)
        ET.fromstring(path.read_bytes())
        self.outs[f"deck/{name}"] = path.read_bytes()

    def save_svg(self, svg: str, name: str) -> None:
        """Every text channel of a hand-built SVG: element text (text, tspan, title, desc, ...),
        tail text, comments, and the aria-label, aria-description and title attributes."""
        root = ET.fromstring(svg, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))
        for el in root.iter():
            if el.tag == "style" or str(el.tag).endswith("}style"):   # CSS is layout; its tail is still text
                texts = (el.tail,)
            else:
                texts = (el.text, el.tail, el.get("aria-label"), el.get("aria-description"), el.get("title"))
            for s in texts:
                if s and s.strip():
                    self.check_text(name, s.strip() if s.strip() in self.bound else s)
        path = OUT_DIR / name
        path.write_text(svg)
        self.outs[f"deck/{name}"] = path.read_bytes()

    # ------------------------------------------------------------ values
    def register_static(self, head: str) -> None:
        R = self.reg
        R.put("codebook", self.codebook, source=self.cb["file"], how="--codebook")
        R.put("codebook_status", self.cb["status"], source="build_edition.CODEBOOKS", how="status of the codebook")
        R.put("question_codebook", QUESTIONS["codebook"], source=QUESTIONS["file"], how="question-intent codebook")
        R.put("source_commit", head[:12], source="git", how="last commit touching any build input")
        R.put("paper_v0", PAPER_V0, source="git", how="edition v0 commit of the paper")
        R.put("paper_edition", "v0", source=f"{PAPER}@{PAPER_V0}", how="edition name of the hand-written paper")
        R.put("threshold", display.round_half_up(THRESHOLD, 1), source="build_edition.THRESHOLD", how="both witnesses >= this")
        R.put("ttm_months", str(TTM_MONTHS), source="build_edition.TTM_MONTHS", how="trailing window, months")
        R.put("ec_cutoff_year", str(CUTOFF_YEAR), source="build_edition.CUTOFF_YEAR", how="comparison year")
        new = {r["status"].split()[0] for r in table(self.cb["file"])[1] if r["status"].startswith("v0.2")}
        for i, v in enumerate(sorted(new)):
            R.put(f"new_tag_{i}", v, source=self.cb["file"], how="status column of hypotheses new in this codebook")
        raw = git("show", f"{PAPER_V0}:{PAPER}")
        text = re.sub(r"\s+", " ", raw.replace("**", "").replace("*", ""))
        for k, q in QUOTES.items():
            if q not in text:
                self.errs.append(f"quote {k} not found verbatim in {PAPER}@{PAPER_V0}: {q!r}")
            R.put(k, q, source=f"{PAPER}@{PAPER_V0}", how="verbatim quote (emphasis and line breaks removed)")
            if k in QUOTE_STATUS:
                row = [l for l in raw.splitlines() if l.startswith("|") and q in l.replace("**", "")]
                status = row[0].split("|")[2].strip() if len(row) == 1 else ""
                if not status:
                    self.errs.append(f"quote {k}: no single claims-table row with a status in {PAPER}@{PAPER_V0}")
                R.put(f"{k}_status", status, source=f"{PAPER}@{PAPER_V0}",
                      how=f"status column of the claims-table row quoting {k}")

    # ------------------------------------------------------------ earnings calls
    def earnings(self) -> None:
        R, cb = self.reg, self.cb
        scores = ROOT / cb["ec_scores"]
        con = duckdb.connect()
        as_of = str(con.execute(f"SELECT max(report_date) FROM read_csv('{EC / 'calls.tsv'}')").fetchone()[0])
        R.put("as_of", as_of, source="corpus/earnings-calls/calls.tsv", how="max(report_date)")
        R.put("as_of_md", as_of[5:], source="corpus/earnings-calls/calls.tsv", how="month and day of as_of (chart tick)")

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
                report_date::DATE AS report_date, role, regexp_matches(text, '{RISK_WORD}') AS lex,
                window_id IN ({flags('ai_risk')}) AS ai_risk
            FROM {ect.windows_sql()}""")
        con.execute("""CREATE TABLE cw AS SELECT c.*, bool_or(w.lex) AS lex, bool_or(w.ai_risk) AS nli
            FROM calls c LEFT JOIN w USING (symbol, fiscal_year, fiscal_quarter) GROUP BY ALL""")
        series = con.execute(f"""SELECT year(report_date)::INT, count(*)::INT,
                (count(*) FILTER (WHERE lex))::INT, (count(*) FILTER (WHERE nli))::INT
            FROM cw WHERE year(report_date) >= {FIRST_YEAR} GROUP BY 1 ORDER BY 1""").fetchall()
        src = f"corpus/earnings-calls/{{calls.tsv,ai-windows.parquet}} + {cb['ec_scores']}"
        for y, n, lex, nli in series:
            R.put(f"year_{y}", str(y), source=src, how="calendar year in the series (chart tick)")
            R.pct(f"ec_lex_{y}", lex, n, 1, source=src, how=f"{y}: calls with a 'risk' word in an AI window / calls")
            R.pct(f"ec_nli_{y}", nli, n, 1, source=src, how=f"{y}: calls with an ai_risk window (both witnesses) / calls")
        last = series[-1]
        R.put("ec_year_last", str(last[0]), source=src, how="last calendar year in the series")
        R.copy("ec_pct_witness_last", f"ec_nli_{last[0]}", how="last year")
        pre = max((r for r in series if r[0] < CUTOFF_YEAR), key=lambda r: Fraction(r[3], r[1]))
        R.copy("ec_pre2023_max", f"ec_nli_{pre[0]}", how=f"max over years < {CUTOFF_YEAR} of ec_nli_<year>")

        # The call rate counts a call once any AI window is flagged, so it rises with the number of AI windows
        # alone. The per-window rate, same codebook and rule, separates framing from volume.
        per_window = {y: (n, k) for y, n, k in con.execute(f"""SELECT year(c.report_date)::INT, count(*)::INT,
                (count(*) FILTER (WHERE w.ai_risk))::INT FROM w JOIN calls c USING (symbol, fiscal_year, fiscal_quarter)
            WHERE year(c.report_date) >= {FIRST_YEAR} GROUP BY 1""").fetchall()}
        calls_n = {y: n for y, n, *_ in series}
        for y, (n, k) in sorted(per_window.items()):
            R.pct(f"ec_win_{y}", k, n, 1, source=src, how=f"{y}: AI windows flagged ai_risk (both witnesses) / AI windows")
            R.put(f"ec_wpc_{y}", display.ratio(n, calls_n[y], 1), source=src, how=f"{y}: AI windows / calls",
                  n=n, d=calls_n[y])
        base = CUTOFF_YEAR - 1
        if base not in per_window or last[0] not in per_window:
            self.errs.append(f"per-window rate undefined in {base} or {last[0]}: no AI windows")
        else:
            R.put("ec_win_base_year", str(base), source="build_edition.CUTOFF_YEAR", how="last year before the cutoff")
            for tag, y in (("base", base), ("last", last[0])):
                R.copy(f"ec_win_{tag}", f"ec_win_{y}", how=f"{tag} year")
                R.copy(f"ec_wpc_{tag}", f"ec_wpc_{y}", how=f"{tag} year")
        self.per_window = per_window

        since = f"DATE '{as_of}' - INTERVAL {TTM_MONTHS} MONTH"
        con.execute(f"""CREATE TABLE ttm AS SELECT * FROM w WHERE report_date > {since} AND report_date <= DATE '{as_of}'
            AND ai_risk AND {COMPANY_SPEAKERS}""")
        ranking = []
        for t in types:
            firms = con.execute(f"SELECT count(DISTINCT symbol)::INT FROM ttm WHERE window_id IN ({flags(t)})").fetchone()[0]
            lab = LABELS.get(t, t) + (" *" if t in new else "")
            ranking.append((t, lab, firms))
            R.count(f"ec_rank_{t}", firms, source=src,
                    how=f"firms with a company-speaker window both ai_risk and {t}, trailing window")
        ranking.sort(key=lambda r: (-r[2], r[0]))
        R.count("ec_ttm_risk_firms", con.execute("SELECT count(DISTINCT symbol)::INT FROM ttm").fetchone()[0],
                source=src, how="firms with >= 1 company-speaker ai_risk window, trailing window")
        self.compose("ec_top3", ", ".join(f"{LABELS.get(r[0], r[0])} ({{ec_rank_{r[0]}}})" for r in ranking[:3]),
                     source=src, how="top three of the ranking")
        first, y_last = series[0][0], last[0]
        self.compose("alt_series", (
            f"Line chart, {{year_{first}}} to {{ec_year_last}}: share of S&P 500 earnings calls where both models frame AI "
            f"as a risk, {{ec_nli_{y_last}}}% in {{ec_year_last}} against at most {{ec_pre2023_max}}% in any year before "
            f"{{ec_cutoff_year}}; calls with a risk word next to AI, {{ec_lex_{y_last}}}% in {{ec_year_last}}; share of AI "
            f"passages framed as a risk, {{ec_win_base}}% in {{ec_win_base_year}} and {{ec_win_last}}% in {{ec_year_last}}."),
            source=src, how="alt text of ai-risk-by-year.svg, from the chart's bindings")
        self.compose("alt_ranking", (
            "Bar chart: number of companies whose own speakers raised each AI risk on S&P 500 calls, {ttm_months} months "
            "to {as_of}: " + "; ".join(f"{LABELS.get(t, t)} {{ec_rank_{t}}}" for t, _, n in ranking if n > 0) + "."),
            source=src, how="alt text of risk-ranking-ttm.svg, from the chart's bindings")
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
                                      ("nli", 3, S2, self.say("Both models: AI framed as a risk ({codebook})"))):
            ys = [float(Fraction(100 * r[col], r[1])) for r in series]   # positions only; labels are registered text
            ax.plot(years, ys, color=color, lw=2, marker="o", ms=4.5, mec=SURFACE, mew=1.5, label=name)
            ax.annotate(self.say("{" + f"ec_{key}_{years[-1]}" + "}%"), (years[-1], ys[-1]), xytext=(8, 0),
                        textcoords="offset points", va="center", color=INK, fontsize=10, fontweight="bold")
        wy = [y for y in years if y in self.per_window]
        ws = [float(Fraction(100 * self.per_window[y][1], self.per_window[y][0])) for y in wy]
        ax.plot(wy, ws, color=S2, lw=1.6, ls="--", marker="o", ms=3.5, mec=SURFACE, mew=1,
                label="Per AI passage, same rule: share of AI passages framed as a risk")
        ax.annotate(self.say("{" + f"ec_win_{wy[-1]}" + "}%"), (wy[-1], ws[-1]), xytext=(8, -4),
                    textcoords="offset points", va="center", color=INK, fontsize=9)
        ax.set_xticks(years, [self.say("{" + f"year_{y}" + "}" + ("\n(to {as_of_md})" if y == years[-1] else ""))
                              for y in years], fontsize=9)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        ax.set_ylim(0, None)
        ax.set_xlim(years[0] - 0.5, years[-1] + 1.2)
        ax.set_title("Share of S&P 500 earnings calls where AI is discussed as a risk", loc="left",
                     color=INK, fontsize=12, fontweight="bold", pad=22)
        ax.text(0, 1.02, "Calls per calendar year; denominator: every unique, non-stub S&P 500 call in the corpus",
                transform=ax.transAxes, color=INK2, fontsize=9)
        ax.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=INK)
        fig.text(0.01, 0.01, self.say("Source: defeatbeta/yahoo-finance-data transcripts (ODC-BY). Model lines: risk codebook "
                 "{codebook}; witness proposals, not hand-verified.\nEarly per-passage points rest on few passages."),
                 color=INK2, fontsize=7.5)
        fig.tight_layout(rect=(0, 0.05, 1, 1))
        self.save_fig(fig, "ai-risk-by-year.svg")

    def plot_ranking(self, ranking) -> None:
        R = self.reg
        matplotlib, plt = self.mpl()
        shown = [r for r in ranking if r[2] > 0][::-1]
        fig, ax = plt.subplots(figsize=(8, 0.36 * len(shown) + 1.6), facecolor=SURFACE)
        ax.set_facecolor(SURFACE)
        ax.barh([r[1] for r in shown], [r[2] for r in shown], color=S1, height=0.62)
        for i, r in enumerate(shown):
            ax.text(r[2] + 0.4, i, self.say("{" + f"ec_rank_{r[0]}" + "}"), va="center", color=INK, fontsize=9)
        for s in ("top", "right", "bottom"):
            ax.spines[s].set_visible(False)
        ax.set_xticks([])
        ax.tick_params(length=0, labelsize=9.5, labelcolor=INK)
        ax.set_title(self.say("AI risks raised by company speakers on S&P 500 calls,\n{ttm_months} months to {as_of}"),
                     loc="left", color=INK, fontsize=12, fontweight="bold", pad=30)
        ax.text(0, 1.01, self.say("Number of companies whose own speakers raised it (analysts excluded; role is a name "
                "heuristic);\nboth models must propose the window. Risk codebook {codebook}; "
                "* = new in {new_tag_0}."), transform=ax.transAxes, color=INK2, fontsize=8.5)
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
        group = {h: ("oversight" if h in qr.OVERSIGHT else "commercial" if h in qr.COMMERCIAL + ["q_spend"] else "other")
                 for h, *_ in out}
        # Group totals for the caption and legend: distinct questions carrying any intent of the group (a question
        # with two commercial intents counts once), from the same question-level scores, window and rule as ttm.tsv.
        sc, as_of = ROOT / QUESTIONS["scores"], R.values["as_of"]["text"]
        con = duckdb.connect()
        con.execute(f"""CREATE TABLE q AS SELECT question_id FROM '{ROOT / QUESTIONS["units"]}'
            WHERE report_date > CAST(DATE '{as_of}' - INTERVAL {TTM_MONTHS} MONTH AS VARCHAR) AND report_date <= '{as_of}'""")
        con.execute(f"""CREATE TABLE s AS SELECT d.question_id, d.hypothesis_id AS h FROM '{sc / 'deberta.parquet'}' d
            JOIN '{sc / 'modernbert.parquet'}' m USING (question_id, hypothesis_id)
            WHERE d.p_entail >= {float(THRESHOLD)} AND m.p_entail >= {float(THRESHOLD)} AND question_id IN (SELECT question_id FROM q)""")
        n_units = con.execute("SELECT count(*)::INT FROM q").fetchone()[0]
        if n_units != n_q:
            self.errs.append(f"{QUESTIONS['units']}: {n_units} AI questions in the window, but {QUESTIONS['ttm']} says {n_q}")
        src = f"{QUESTIONS['units']} + {QUESTIONS['scores']}"
        for g in ("commercial", "oversight"):
            hs = ", ".join(f"'{h}'" for h in sorted(h for h in group if group[h] == g))
            k = con.execute(f"SELECT count(DISTINCT question_id)::INT FROM s WHERE h IN ({hs})").fetchone()[0]
            R.pct(f"q_{g}_pct", k, n_q, 1, source=src, how=f"questions with any {g} intent ({hs}) / q_n")
            R.count(f"q_{g}_n", k, source=src, how=f"questions with any {g} intent ({hs})")
        matplotlib, plt = self.mpl()
        color = {"commercial": S1, "oversight": S2, "other": MUTED}
        shown = out[::-1]
        fig, ax = plt.subplots(figsize=(8, 0.42 * len(shown) + 1.7), facecolor=SURFACE)
        ax.set_facecolor(SURFACE)
        ax.barh([qr.LABELS[h] for h, *_ in shown], [float(p) for _, _, p, _ in shown],
                color=[color[group[h]] for h, *_ in shown], height=0.62)
        for i, (h, k, p, txt) in enumerate(shown):
            ax.text(float(p) + 0.3, i, self.say("{" + f"q_{h[2:]}_pct" + "}%  ({" + f"q_{h[2:]}_n" + "})"),
                    va="center", color=INK, fontsize=9)
        for s in ("top", "right", "bottom"):
            ax.spines[s].set_visible(False)
        ax.spines["left"].set_color(INK2)
        ax.set_xticks([])
        ax.tick_params(length=0, labelsize=9.5, labelcolor=INK)
        from matplotlib.patches import Patch
        ax.legend(handles=[Patch(color=S1, label=self.say("Selling it / spending on it: {q_commercial_pct}% of questions")),
                           Patch(color=S2, label=self.say("Governing its risks: {q_oversight_pct}% of questions")),
                           Patch(color=MUTED, label="Other")], loc="lower right", frameon=False, fontsize=9, labelcolor=INK)
        ax.set_title("What analysts ask S&P 500 companies about AI", loc="left", color=INK, fontsize=12,
                     fontweight="bold", pad=20)
        ax.text(0, 1.01, self.say("Share of {q_n} analyst questions on AI, {ttm_months} months to {as_of}"),
                transform=ax.transAxes, color=INK2, fontsize=9)
        fig.text(0.01, 0.01, self.say("A question can count under several topics. Both NLI models must agree; not hand-verified.\n"
                 "Question codebook {question_codebook}. Source: defeatbeta/yahoo-finance-data (ODC-BY)."),
                 color=INK2, fontsize=7)
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        self.save_fig(fig, "intent-ttm.svg")
        self.compose("alt_intent", (
            "Bar chart: share of {q_n} analyst questions on AI by topic, {ttm_months} months to {as_of}: "
            + "; ".join(f"{qr.LABELS[h]} {{q_{h[2:]}_pct}}%" for h, *_ in out)
            + ". Commercial topics together {q_commercial_pct}%, oversight topics together {q_oversight_pct}%."),
            source=QUESTIONS["ttm"], how="alt text of intent-ttm.svg, from the chart's bindings")

    # ------------------------------------------------------------ cross-source dialogue space
    def dialogue(self) -> None:
        R, cb = self.reg, self.cb
        comments, rows = table(cb["dialogue"])
        # The sources cover different periods; v02_map.py records each one as "# window <source>: <text>".
        windows = dict(re.fullmatch(r"# window (\w+): (.+)", c).groups() for c in comments if c.startswith("# window "))
        for k, _ in DIALOGUE_SOURCES:
            if k not in windows:
                self.errs.append(f"{cb['dialogue']}: no '# window {k}:' line")
                return
            R.put(f"ds_window_{k}", windows[k], source=cb["dialogue"], how=f"window of source {k} (v02_map.py)")
        for group, (a, b) in {"calls": ("executives", "analysts"), "hn": ("hn_anthropic", "hn_security")}.items():
            if windows[a] != windows[b]:
                self.errs.append(f"{cb['dialogue']}: {a} and {b} windows differ, but the caption names one {group} window")
            R.copy(f"ds_window_{group}", f"ds_window_{a}", how=f"same as ds_window_{b}")
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
            R.copy(key, f"ds_{src}_{t}")
        rows_sorted = sorted(types, key=lambda r: (-max(Fraction(int(r[f'{k}_n']), bases[k]) for k, _ in DIALOGUE_SOURCES),
                                                   r["risk_type"]))
        cw, rh, left, top = 128, 24, 210, 108
        W, H = left + cw * len(DIALOGUE_SOURCES) + 24, top + rh * len(rows_sorted) + 80

        def fill(n: int, d: int) -> str:
            t = min(Fraction(100 * n, d) / 50, Fraction(1))
            lo, hi = (236, 243, 249), (16, 70, 120)
            return "#%02x%02x%02x" % tuple(int(display.round_half_up(a + (b - a) * t, 0)) for a, b in zip(lo, hi))
        new = {r["risk_type"] for r in rows if r.get("new_in_v0.2") == "yes"}
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="system-ui,-apple-system,sans-serif" role="img">',
             '<style>text{fill:#1b1b1b}.m{fill:#5f6368}</style>', f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>',
             '<text x="16" y="30" font-size="18" font-weight="600">Who talks about which AI risks</text>',
             '<text x="16" y="52" font-size="12" class="m">' + escape(quote=False, s=self.say(
                 "Share of each source's AI-risk passages naming each type. Risk codebook {codebook}; * = new in {new_tag_0}."))
             + '</text>']
        for j, (k, label) in enumerate(DIALOGUE_SOURCES):
            x = left + j * cw + cw / 2
            o.append(f'<text x="{x}" y="{top - 24}" font-size="12" font-weight="600" text-anchor="middle">{escape(label)}</text>')
            o.append(f'<text x="{x}" y="{top - 9}" font-size="11" class="m" text-anchor="middle">'
                     + escape(self.say("n = {" + f"ds_base_{k}" + "}"), quote=False) + '</text>')
        for i, r in enumerate(rows_sorted):
            t = r["risk_type"]
            y = top + i * rh
            o.append(f'<text x="{left - 8}" y="{y + rh / 2 + 4}" font-size="12" text-anchor="end">{escape(t)}{" *" if t in new else ""}</text>')
            for j, (k, label) in enumerate(DIALOGUE_SOURCES):
                n, d = int(r[f"{k}_n"]), bases[k]
                ink = "#ffffff" if Fraction(100 * n, d) >= 25 else "#1b1b1b"
                tip = self.say(f"{label}: {t} " + "{" + f"ds1_{k}_{t}" + "}% ({" + f"dsn_{k}_{t}" + "} of {" + f"ds_base_{k}" + "})")
                o.append(f'<g><title>{escape(tip, quote=False)}</title>'
                         f'<rect x="{left + j * cw + 1}" y="{y + 1}" width="{cw - 2}" height="{rh - 2}" rx="2" fill="{fill(n, d)}"/>'
                         f'<text x="{left + j * cw + cw / 2}" y="{y + rh / 2 + 4}" font-size="11" text-anchor="middle" '
                         f'style="fill:{ink}">' + escape(self.say("{" + f"ds_{k}_{t}" + "}"), quote=False) + '</text></g>')
        o.append(f'<text x="16" y="{H - 46}" font-size="11" class="m">' + escape(quote=False, s=self.say(
            "n = passages both NLI witnesses score ≥ {threshold} on ai_risk; a cell needs both on the type too. "
            "A passage can name several types.")) + '</text>')
        o.append(f'<text x="16" y="{H - 30}" font-size="11" class="m">' + escape(quote=False, s=self.say(
            "Different windows: {ds_window_calls}; HN {ds_window_hn};")) + '</text>')
        o.append(f'<text x="16" y="{H - 14}" font-size="11" class="m">' + escape(quote=False, s=self.say(
            "Wikipedia {ds_window_wikipedia}. Levels compare across sources only in rough order. "
            "Witness proposals, no gold set.")) + '</text>')
        o.append("</svg>")
        self.save_svg("\n".join(o) + "\n", "dialogue-space.svg")
        top3 = {k: sorted(types, key=lambda r: (-int(r[f"{k}_n"]), r["risk_type"]))[:3] for k, _ in DIALOGUE_SOURCES}
        self.compose("alt_dialogue", (
            "Heatmap: share of each source's AI-risk passages naming each risk type. Largest three per source: "
            + "; ".join(f"{label} (n = {{ds_base_{k}}}): "
                        + ", ".join(f"{r['risk_type']} {{ds_{k}_{r['risk_type']}}}%" for r in top3[k])
                        for k, label in DIALOGUE_SOURCES) + "."),
            source=cb["dialogue"], how="alt text of dialogue-space.svg, from the chart's bindings")

    # ------------------------------------------------------------ CVE
    def cve(self) -> None:
        R = self.reg
        _, rows = table(CVE)
        R.count("cve_claude_total", sum(int(r["n_credit_claude"]) for r in rows), source=CVE, how="sum n_credit_claude, all months")
        R.count("cve_ai_total", sum(int(r["n_ai_credited"]) for r in rows), source=CVE, how="sum n_ai_credited, all months")
        R.put("cve_baseline", cve_baseline(ROOT / CVE_MANIFEST), source=CVE_MANIFEST, how="pinned date of the baseline row")
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
        a1.annotate(self.say("{cve_last_pub}"), (xs[-1], pub[-1]), xytext=(-2, 4), textcoords="offset points",
                    ha="right", color=INK, fontsize=9, fontweight="bold")
        a1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        a1.set_title("CVEs published per month", loc="left", color=INK, fontsize=11, fontweight="bold")
        self.style(a2)
        a2.bar(xs, claude, color=S2, width=0.78, label="Credit names Claude")
        a2.bar(xs, [a - c for a, c in zip(ai, claude)], bottom=claude, color=MUTED, width=0.78,
               label="Credit names another AI system or term")
        a2.annotate(self.say("{cve_last_ai} ({cve_last_claude} Claude)"), (xs[-1], ai[-1]),
                    xytext=(-4, 4), textcoords="offset points", ha="right", color=INK, fontsize=9, fontweight="bold")
        a2.set_title("CVEs whose credits name an AI system, per month", loc="left", color=INK, fontsize=11, fontweight="bold")
        a2.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=INK)
        for i in ticks:
            R.put(f"cve_year_{months[i][:4]}", months[i][:4], source=CVE, how="year of a charted month (chart tick)")
        a2.set_xticks(ticks, [self.say("{" + f"cve_year_{months[i][:4]}" + "}") for i in ticks])
        fig.suptitle("Vulnerability disclosures, and the share credited to AI", x=0.01, ha="left",
                     color=INK, fontsize=13, fontweight="bold")
        fig.text(0.01, 0.01, self.say("Source: CVEProject/cvelistV5 baseline {cve_baseline} (corpus/cve), "
                 "{cve_chart_first} to {cve_last}.\n"
                 "Credit = the CNA credits field only, matched to named AI systems. Method credit: Epoch AI (CC BY)."),
                 color=INK2, fontsize=7)
        fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.12)
        self.save_fig(fig, "cve-ai-credit.svg")
        self.compose("alt_cve", (
            "Two bar charts by month, {cve_chart_first} to {cve_last}: CVEs published per month, {cve_last_pub} in the last "
            "month; CVEs whose credits name an AI system, {cve_last_ai} in the last month, {cve_last_claude} of them "
            "naming Claude."), source=CVE, how="alt text of cve-ai-credit.svg, from the chart's bindings")

    # ------------------------------------------------------------ deck
    def render(self, head: str) -> None:
        """Every line that ships is checked: body text, HTML comments (Marp presenter notes), image
        alt text, and the front-matter fields that render (title, ...). A numeral in a built line
        must come from a binding used on that template line."""
        tpl = TEMPLATE.read_text()
        fm_lines = tpl[:tpl.index("\n---\n", 4) + 5].count("\n")
        self.reg.put("generated_notice", f"<!-- GENERATED by scripts/build_edition.py --codebook {self.codebook} from {head}. "
                     "Edit deck/deck.template.md, not this file. -->", source="build", how="notice")
        vals = {k: v["text"] for k, v in self.reg.values.items()}
        missing = sorted(set(keys_in(tpl)) - set(vals))
        self.errs += [f"unresolved binding {{{{{m}}}}}" for m in missing]

        def fill(x: str) -> str:
            return re.sub(r"\{\{(\w+)\}\}", lambda m: vals.get(m.group(1), m.group(0)), x)

        def shown(x: str) -> str:   # image targets are paths; size keywords in alt text are layout
            return re.sub(r"!\[([^\]]*)\]\([^)]*\)", lambda m: "![" + MARP_SIZE.sub("", m.group(1)) + "]", x)
        for i, line in enumerate(tpl.splitlines(), 1):
            in_fm = i <= fm_lines
            for alt in re.findall(r"!\[([^\]]*)\]\(", line):
                if not re.fullmatch(r"\{\{alt_\w+\}\}", MARP_SIZE.sub("", alt).strip()):
                    self.errs.append(f"deck.template.md:{i}: image alt text must be one alt binding: {alt!r}")
            if in_fm and not FM_CHECKED.match(line):
                continue
            bad = sorted(tokens(shown(re.sub(r"\{\{\w+\}\}", "", line))))
            if bad:
                self.errs.append(f"deck.template.md:{i}: hand-typed numerals {bad}")
            if not missing:
                self.check_text(f"DECK.md:{i}", shown(fill(line)), keys_in(line))
            if in_fm:
                continue
            plain = re.sub(r"<[^>]+>", "", line)
            quoted = [next(g for g in m.groups() if g is not None) for m in QUOTED.finditer(plain)]
            bq = re.match(r"\s*>\s?(.*)", line)
            if bq:
                quoted.append(bq.group(1).strip())
            if re.search(r"(?i)<blockquote|<q[ >]", line):
                quoted.append(re.sub(r"<[^>]+>", "", re.search(r"(?i)<(blockquote|q)\b[^>]*>(.*)", line).group(2)).strip())
            for q in quoted:
                if not QUOTE_BINDING.fullmatch(q):
                    self.errs.append(f"deck.template.md:{i}: quoted text must be one quote binding: \"{q}\"")
        self.outs["DECK.md"] = fill(tpl).encode()

    def run(self) -> tuple[dict[str, bytes], list[str]]:
        display.selftest()
        if not self.preflight():
            return {}, self.errs
        head = source_commit(self.inputs())
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

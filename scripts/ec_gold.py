#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb==2.0.0", "blake3==1.0.11"]
# ///
"""Human gold set for the earnings-call AI codebook (v0.1): sample, code, score.

The NLI witnesses (docs/earnings-call-ai-corpus.md §5) are proposals with
unknown precision. This script draws a stratified sample of AI windows, gives a
person a terminal loop to code them, and scores each witness against the human
labels. It writes no label itself: spec §9 bars LLM-generated labels, so every
label in sample.tsv must be typed by a person.

    uv run scripts/ec_gold.py sample --n 240     # writes gold/earnings-calls/codebook-v0.1/sample.tsv
    uv run scripts/ec_gold.py code --coder NAME  # interactive; resumable; saves after every row
    uv run scripts/ec_gold.py score              # writes .../score.tsv and prints it

Strata
------
The 38,600 windows are partitioned into 13 strata, so every window belongs to
exactly one and stratum weights are valid for any estimate:

  lexical_risk           the window text matches (?i)\\brisk(s|y|ier|iest)?\\b,
                         the lexical measure in scripts/ec_risk_series.py.
                         Taken out first, so its precision is measured on its
                         own population.
  ai_risk:<cell>:<period>  every other window, by the two witnesses' `ai_risk`
                         scores at 0.5 -- cell is both, deberta_only,
                         modernbert_only or neither -- crossed with period of
                         report_date: <=2022, 2023-2025, 2026+.

Allocation at --n 240 (ALLOCATION below; other n scale it by largest remainder,
capped at the population):

  lexical_risk                       30
  ai_risk:both:<each period>         12  x3 = 36   precision of the agreed positives
  ai_risk:deberta_only:<period>      18  x3 = 54   disagreement cells are oversampled:
  ai_risk:modernbert_only:<period>   18  x3 = 54   they decide which witness is right
  ai_risk:neither:<each period>      22  x3 = 66   the recall estimate: positives the
                                                   witnesses both missed live here

`neither` holds about 95% of windows, so its 66 rows carry very large weights
and the recall estimate is wide. That is stated, not hidden: score.tsv prints
n beside every rate.

Draw: within a stratum, windows are ordered by blake3("ec-gold-v0.1|" + window_id)
and the first k taken. No RNG and no clock; re-running `sample` on the same
inputs is byte-identical. The sample file carries no model score (blind coding);
`score` joins the scores back in.

Scoring: Horvitz-Thompson weights w = stratum_population / coded rows in the
stratum. precision = sum(w*gold*pred) / sum(w*pred); recall = sum(w*gold*pred) /
sum(w*gold). A risk-type prediction is the type score >= 0.5 AND the same
witness's ai_risk >= 0.5, as in ec_report.py; its gold is ai_risk=y with the
type listed. Risk types are scored once they have >= 5 coded positives.

Analyst questions (--set questions)
-----------------------------------
    uv run scripts/ec_gold.py --set questions sample   # gold/earnings-calls/codebook-questions-v0.1/sample.tsv
    uv run scripts/ec_gold.py --set questions code --coder NAME
    uv run scripts/ec_gold.py --set questions score

Unit: the 4,288 analyst questions in corpus/earnings-calls/ai-questions.parquet,
coded y/n on all 10 hypotheses of codebook-questions-v0.1.tsv. The claim under
test is "oversight questions are rare vs commercial", so the strata serve
precision of `oversight` (any of q_risk, q_controls, q_regulation, q_harm,
q_security) and `commercial` (q_revenue, q_efficiency), and recall of oversight.
Four strata, checked in this order (a question takes the first that applies):

  oversight_both    both witnesses >= 0.5 on at least one oversight hypothesis
                    (the report's definition of a flagged oversight question)
  oversight_one     one witness, not both, >= 0.5 on an oversight hypothesis:
                    the disagreement cell, where per-witness precision and the
                    flagged set's recall are decided
  commercial_only   both witnesses >= 0.5 on a commercial hypothesis, not oversight
  neither           the rest; oversight questions both witnesses missed live here

Allocation at --n 200 (Q_ALLOCATION; populations at codebook-questions-v0.1):

  oversight_both    141 -> 100   most of the flagged set, not all: all 141
                                 would leave 59 rows for the other three cells
  oversight_one     121 ->  30
  commercial_only  1113 ->  30
  neither          2913 ->  40   oversampled against commercial for oversight recall

No period split: the <=2022 cells hold 7 (oversight_both), 11 (oversight_one)
and 61 (commercial_only) questions, too few to stratify on. Draw order is
blake3("ec-gold-questions-v0.1|" + question_id); weights and estimators as above.
A group is predicted when any member hypothesis is (for both>=0.5: any member
with both witnesses >= 0.5, as in ec_question_report.py).
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import shutil
import sys
import tempfile
import textwrap
from pathlib import Path

import blake3
import duckdb

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus" / "earnings-calls"
PROP = ROOT / "proposals" / "earnings-calls" / "codebook-v0.1"
GOLD = ROOT / "gold" / "earnings-calls" / "codebook-v0.1"
SAMPLE = GOLD / "sample.tsv"
SCORE = GOLD / "score.tsv"
SALT = "ec-gold-v0.1|"
THRESHOLD = 0.5
MIN_POSITIVES = 5
RISK_WORD = r"(?i)\brisk(s|y|ier|iest)?\b"
PERIODS = [("<=2022", None, "2023-01-01"), ("2023-2025", "2023-01-01", "2026-01-01"), ("2026+", "2026-01-01", None)]
CELLS = ["both", "deberta_only", "modernbert_only", "neither"]
BASE_N = 240
ALLOCATION = {"lexical_risk": 30}
for _c, _k in (("both", 12), ("deberta_only", 18), ("modernbert_only", 18), ("neither", 22)):
    for _p in PERIODS:
        ALLOCATION[f"ai_risk:{_c}:{_p[0]}"] = _k
META = ["window_id", "stratum", "stratum_population", "symbol", "report_date", "speaker", "role", "text"]
LABELS = ["about_ai", "ai_risk", "risk_types", "governance", "coder", "note"]
COLUMNS = META + LABELS
YN = ("about_ai", "ai_risk", "governance")

# Analyst-question set (--set questions).
QUESTIONS = CORPUS / "ai-questions.parquet"
Q_PROP = ROOT / "proposals" / "earnings-calls" / "codebook-questions-v0.1"
Q_SAMPLE = ROOT / "gold" / "earnings-calls" / "codebook-questions-v0.1" / "sample.tsv"
Q_SALT = "ec-gold-questions-v0.1|"
Q_BASE_N = 200
Q_ALLOCATION = {"oversight_both": 100, "oversight_one": 30, "commercial_only": 30, "neither": 40}
Q_META = ["question_id", "stratum", "stratum_population", "symbol", "report_date", "speaker", "text"]


def codebook() -> list[dict]:
    with open(CORPUS / "codebook-v0.1.tsv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def risk_types() -> list[dict]:
    return [r for r in codebook() if r["group"] == "risk_type"]


# ---------------------------------------------------------------- tsv i/o

def read_tsv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def tsv_bytes(rows: list[dict], columns: list[str], note: str = "") -> bytes:
    buf = io.StringIO()
    buf.write(note)
    w = csv.DictWriter(buf, fieldnames=columns, delimiter="\t", lineterminator="\n",
                       quoting=csv.QUOTE_MINIMAL, extrasaction="raise")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


def rel(path: Path) -> str:
    path = path.resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# ---------------------------------------------------------------- sample

def allocate(n: int, pop: dict[str, int], alloc: dict[str, int] = ALLOCATION) -> dict[str, int]:
    """Scale an allocation to n by largest remainder (ties: allocation order), cap at population."""
    total = sum(alloc.values())
    exact = {s: k * n / total for s, k in alloc.items()}
    k = {s: int(v) for s, v in exact.items()}
    order = sorted(alloc, key=lambda s: (-(exact[s] - k[s]), list(alloc).index(s)))
    for s in order[: n - sum(k.values())]:
        k[s] += 1
    return {s: min(v, pop.get(s, 0)) for s, v in k.items()}


def scores_view(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(f"""CREATE TABLE sc AS
        SELECT d.window_id, d.hypothesis_id, d.p_entail AS p_deb, m.p_entail AS p_mod
        FROM '{PROP / 'deberta.parquet'}' d JOIN '{PROP / 'modernbert.parquet'}' m USING (window_id, hypothesis_id)""")


def strata(con: duckdb.DuckDBPyConnection) -> None:
    period = "CASE " + " ".join(
        f"WHEN report_date < '{hi}' THEN '{name}'" for name, _, hi in PERIODS if hi) + f" ELSE '{PERIODS[-1][0]}' END"
    con.execute(f"""CREATE TABLE st AS
        WITH r AS (SELECT window_id, p_deb >= {THRESHOLD} AS d, p_mod >= {THRESHOLD} AS m
                   FROM sc WHERE hypothesis_id = 'ai_risk')
        SELECT w.window_id, w.symbol, w.report_date, w.speaker, w.role, w.text,
               CASE WHEN regexp_matches(w.text, '{RISK_WORD}') THEN 'lexical_risk'
                    ELSE 'ai_risk:' || CASE WHEN r.d AND r.m THEN 'both' WHEN r.d THEN 'deberta_only'
                                             WHEN r.m THEN 'modernbert_only' ELSE 'neither' END
                         || ':' || {period} END AS stratum
        FROM '{CORPUS / 'ai-windows.parquet'}' w JOIN r USING (window_id)""")


def cmd_sample(a: argparse.Namespace) -> int:
    if a.sample.exists() and not a.force:
        coded = [r for r in read_tsv(a.sample) if r.get("coder")]
        if coded:
            sys.exit(f"{rel(a.sample)} has {len(coded)} coded rows; refusing to overwrite (use --force)")
    con = duckdb.connect()
    scores_view(con)
    strata(con)
    n_windows = con.execute("SELECT count(*) FROM '" + str(CORPUS / "ai-windows.parquet") + "'").fetchone()[0]
    n_st = con.execute("SELECT count(*) FROM st").fetchone()[0]
    if n_st != n_windows:
        sys.exit(f"{n_windows - n_st} windows lack an ai_risk score in both witnesses; rebuild proposals first")
    pop = dict(con.execute("SELECT stratum, count(*) FROM st GROUP BY 1").fetchall())
    unknown = set(pop) - set(ALLOCATION)
    if unknown:
        sys.exit(f"unexpected strata: {sorted(unknown)}")
    k = allocate(a.n, pop)
    rows = con.execute("SELECT window_id, stratum, symbol, report_date, speaker, role, text FROM st").fetchall()
    by: dict[str, list[tuple]] = {}
    for r in rows:
        by.setdefault(r[1], []).append((blake3.blake3((SALT + r[0]).encode("utf-8")).hexdigest(), r))
    out = []
    for s in ALLOCATION:
        for _, r in sorted(by.get(s, []))[: k[s]]:
            rec = dict(zip(["window_id", "stratum", "symbol", "report_date", "speaker", "role", "text"], r))
            rec["stratum_population"] = pop.get(s, 0)
            rec.update({c: "" for c in LABELS})
            out.append(rec)
    write_atomic(a.sample, tsv_bytes(out, COLUMNS))
    print(f"{'stratum':34} {'population':>10} {'sampled':>7}")
    for s in ALLOCATION:
        print(f"{s:34} {pop.get(s, 0):>10} {k[s]:>7}")
    print(f"{'total':34} {sum(pop.values()):>10} {len(out):>7}")
    print(f"wrote {rel(a.sample)}")
    return 0


# ---------------------------------------------------------------- code

def is_coded(r: dict, yn: tuple[str, ...] = YN) -> bool:
    return bool(r.get("coder")) and all(r.get(c) in ("y", "n") for c in yn)


class Quit(Exception):
    pass


class Skip(Exception):
    pass


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip().lower()
    except EOFError:
        raise Quit


def ask_yn(label: str, hypothesis: str) -> str:
    while True:
        ans = ask(f"\n{label}: {hypothesis}\n  [y]es / [n]o / [s]kip row / [q]uit > ")
        if ans in ("y", "n"):
            return ans
        if ans == "s":
            raise Skip
        if ans == "q":
            raise Quit
        print("  answer y, n, s or q")


def ask_types(types: list[dict]) -> str:
    print("\nrisk types (numbers separated by spaces or commas; Enter = none listed fits):")
    for i, t in enumerate(types, 1):
        print(f"  {i:2}. {t['id']:14} {t['hypothesis']}")
    while True:
        ans = ask("  > ").replace(",", " ")
        if ans == "s":
            raise Skip
        if ans == "q":
            raise Quit
        try:
            picks = sorted({int(x) for x in ans.split()})
        except ValueError:
            print("  numbers only, or s / q")
            continue
        if all(1 <= p <= len(types) for p in picks):
            return ";".join(types[p - 1]["id"] for p in picks)
        print(f"  numbers must be 1-{len(types)}")


def cmd_code(a: argparse.Namespace) -> int:
    if not a.sample.exists():
        sys.exit("no sample: run `uv run scripts/ec_gold.py sample --n 240` first")
    coder = a.coder or ask("coder name (recorded on every row you code) > ")
    if not coder or "\t" in coder:
        sys.exit("a coder name is required")
    hyp = {r["id"]: r["hypothesis"] for r in codebook()}
    types = risk_types()
    rows = read_tsv(a.sample)
    todo = [i for i, r in enumerate(rows) if not is_coded(r)]
    width = min(shutil.get_terminal_size((100, 24)).columns, 100) - 4
    print(f"{len(rows) - len(todo)} of {len(rows)} coded; {len(todo)} to go.")
    print("Code what the speaker says, not what you think of AI. s skips a row (offered again next run).")
    done = 0
    try:
        for n, i in enumerate(todo, 1):
            r = rows[i]
            print("\n" + "=" * width)
            print(f"[{n}/{len(todo)}]  {r['symbol']}  {r['report_date']}  {r['speaker']} ({r['role']})  {r['window_id']}")
            print("-" * width)
            for para in r["text"].splitlines() or [""]:
                print(textwrap.fill(para, width=width, initial_indent="  ", subsequent_indent="  "))
            try:
                lab = {"about_ai": ask_yn("about_ai", hyp["about_ai"]),
                       "ai_risk": ask_yn("ai_risk", hyp["ai_risk"])}
                lab["risk_types"] = ask_types(types) if lab["ai_risk"] == "y" else ""
                lab["governance"] = ask_yn("governance", hyp["governance"])
                note = ask("\nnote (optional, Enter for none) > ")
            except Skip:
                print("  skipped")
                continue
            r.update(lab, coder=coder, note=" ".join(note.split()))
            write_atomic(a.sample, tsv_bytes(rows, COLUMNS))
            done += 1
    except (Quit, KeyboardInterrupt):
        print("\nquit")
    print(f"coded {done} rows this session; {sum(is_coded(r) for r in rows)} of {len(rows)} total. Saved.")
    return 0


# ---------------------------------------------------------------- score

def rate(num: float, den: float) -> str:
    return f"{num / den:.3f}" if den > 0 else ""


def cmd_score(a: argparse.Namespace) -> int:
    if not a.sample.exists():
        sys.exit("no sample: run `uv run scripts/ec_gold.py sample --n 240` first")
    rows = read_tsv(a.sample)
    coded = [r for r in rows if is_coded(r)]
    n_coded = {}
    for r in coded:
        n_coded[r["stratum"]] = n_coded.get(r["stratum"], 0) + 1
    weight = {s: int(next(r["stratum_population"] for r in rows if r["stratum"] == s)) / c for s, c in n_coded.items()}
    con = duckdb.connect()
    scores_view(con)
    ids = [r["window_id"] for r in coded]
    p: dict[tuple[str, str], tuple[float, float]] = {}
    if ids:
        con.execute("CREATE TABLE ids (window_id VARCHAR)")
        con.executemany("INSERT INTO ids VALUES (?)", [(i,) for i in ids])
        for wid, h, d, m in con.execute("SELECT window_id, hypothesis_id, p_deb, p_mod FROM sc JOIN ids USING (window_id)").fetchall():
            p[(wid, h)] = (d, m)
    lex = {}
    if ids:
        lex = dict(con.execute(f"""SELECT window_id, regexp_matches(text, '{RISK_WORD}')
            FROM '{CORPUS / 'ai-windows.parquet'}' JOIN ids USING (window_id)""").fetchall())

    TYPE_IDS = {t["id"] for t in risk_types()}

    def pred(wid: str, h: str, witness: str) -> bool:
        if witness == "lexical":
            return bool(lex[wid])
        d, m = p[(wid, h)]
        ok = {"deberta": d >= THRESHOLD, "modernbert": m >= THRESHOLD, "both": d >= THRESHOLD and m >= THRESHOLD}[witness]
        if h in TYPE_IDS:
            ok = ok and pred(wid, "ai_risk", witness)
        return ok

    def gold(r: dict, h: str) -> bool:
        if h in TYPE_IDS:
            return r["ai_risk"] == "y" and h in r["risk_types"].split(";")
        return r[h] == "y"

    hyps = list(YN) + [t["id"] for t in risk_types() if sum(gold(r, t["id"]) for r in coded) >= MIN_POSITIVES]
    out = []
    for h in hyps:
        witnesses = ["deberta", "modernbert", "both"] + (["lexical"] if h == "ai_risk" else [])
        for wt in witnesses:
            tp = fp = fn = wtp = wpp = wgp = 0.0
            for r in coded:
                g, q, w = gold(r, h), pred(r["window_id"], h, wt), weight[r["stratum"]]
                tp += g and q
                fp += q and not g
                fn += g and not q
                wtp += w * (g and q)
                wpp += w * q
                wgp += w * g
            out.append({"hypothesis": h, "witness": "both>=0.5" if wt == "both" else wt, "n_coded": len(coded),
                        "gold_pos": int(tp + fn), "pred_pos": int(tp + fp), "true_pos": int(tp),
                        "precision_w": rate(wtp, wpp), "recall_w": rate(wtp, wgp)})
    cols = ["hypothesis", "witness", "n_coded", "gold_pos", "pred_pos", "true_pos", "precision_w", "recall_w"]
    strata_seen = ", ".join(f"{s}={n_coded[s]}" for s in ALLOCATION if s in n_coded) or "none"
    note = (f"# {len(coded)} of {len(rows)} sample rows coded (coded per stratum: {strata_seen}). "
            f"precision_w/recall_w are stratum-weighted (w = stratum_population / coded in stratum); counts are unweighted. "
            f"Risk types appear once they have >= {MIN_POSITIVES} coded positives. Blank = undefined (no denominator).\n")
    data = tsv_bytes(out, cols, note)
    score_path = a.sample.with_name(SCORE.name)
    write_atomic(score_path, data)
    sys.stdout.write(data.decode("utf-8"))
    print(f"wrote {rel(score_path)}")
    return 0


# ---------------------------------------------------------------- questions set

def q_codebook() -> list[dict]:
    return read_tsv(CORPUS / "codebook-questions-v0.1.tsv")


def q_hyps() -> tuple[str, ...]:
    return tuple(r["id"] for r in q_codebook())


def q_group(name: str) -> list[str]:
    return [r["id"] for r in q_codebook() if r["group"] == name]


def q_scores(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(f"""CREATE TABLE qsc AS
        SELECT d.question_id, d.hypothesis_id, d.p_entail AS p_deb, m.p_entail AS p_mod
        FROM '{Q_PROP / 'deberta.parquet'}' d JOIN '{Q_PROP / 'modernbert.parquet'}' m USING (question_id, hypothesis_id)""")


def q_cmd_sample(a: argparse.Namespace) -> int:
    if a.sample.exists() and not a.force:
        coded = [r for r in read_tsv(a.sample) if r.get("coder")]
        if coded:
            sys.exit(f"{rel(a.sample)} has {len(coded)} coded rows; refusing to overwrite (use --force)")
    con = duckdb.connect()
    q_scores(con)
    ov, cm = q_group("oversight"), q_group("commercial")
    inn = lambda ids: "hypothesis_id IN (" + ", ".join(f"'{h}'" for h in ids) + ")"  # noqa: E731
    con.execute(f"""CREATE TABLE qst AS
        WITH f AS (SELECT question_id,
                   bool_or(p_deb >= {THRESHOLD} AND p_mod >= {THRESHOLD}) FILTER (WHERE {inn(ov)}) AS ov_both,
                   bool_or(p_deb >= {THRESHOLD} OR p_mod >= {THRESHOLD}) FILTER (WHERE {inn(ov)}) AS ov_any,
                   bool_or(p_deb >= {THRESHOLD} AND p_mod >= {THRESHOLD}) FILTER (WHERE {inn(cm)}) AS cm_both
                   FROM qsc GROUP BY 1)
        SELECT q.question_id, q.symbol, q.report_date, q.speaker, q.text,
               CASE WHEN f.ov_both THEN 'oversight_both' WHEN f.ov_any THEN 'oversight_one'
                    WHEN f.cm_both THEN 'commercial_only' ELSE 'neither' END AS stratum
        FROM '{QUESTIONS}' q JOIN f USING (question_id)""")
    n_q = con.execute(f"SELECT count(*) FROM '{QUESTIONS}'").fetchone()[0]
    n_st = con.execute("SELECT count(*) FROM qst").fetchone()[0]
    if n_st != n_q:
        sys.exit(f"{n_q - n_st} questions lack witness scores; rebuild proposals first")
    pop = dict(con.execute("SELECT stratum, count(*) FROM qst GROUP BY 1").fetchall())
    k = allocate(a.n, pop, Q_ALLOCATION)
    by: dict[str, list[tuple]] = {}
    for r in con.execute("SELECT question_id, stratum, symbol, report_date, speaker, text FROM qst").fetchall():
        by.setdefault(r[1], []).append((blake3.blake3((Q_SALT + r[0]).encode("utf-8")).hexdigest(), r))
    hyps = q_hyps()
    out = []
    for s in Q_ALLOCATION:
        for _, r in sorted(by.get(s, []))[: k[s]]:
            rec = dict(zip(["question_id", "stratum", "symbol", "report_date", "speaker", "text"], r))
            rec["stratum_population"] = pop.get(s, 0)
            rec.update({c: "" for c in (*hyps, "coder", "note")})
            out.append(rec)
    write_atomic(a.sample, tsv_bytes(out, Q_META + [*hyps, "coder", "note"]))
    print(f"{'stratum':20} {'population':>10} {'sampled':>7}")
    for s in Q_ALLOCATION:
        print(f"{s:20} {pop.get(s, 0):>10} {k[s]:>7}")
    print(f"{'total':20} {sum(pop.values()):>10} {len(out):>7}")
    print(f"wrote {rel(a.sample)}")
    return 0


def q_cmd_code(a: argparse.Namespace) -> int:
    if not a.sample.exists():
        sys.exit("no sample: run `uv run scripts/ec_gold.py --set questions sample` first")
    coder = a.coder or ask("coder name (recorded on every row you code) > ")
    if not coder or "\t" in coder:
        sys.exit("a coder name is required")
    cb = q_codebook()
    hyps = q_hyps()
    rows = read_tsv(a.sample)
    cols = Q_META + [*hyps, "coder", "note"]
    todo = [i for i, r in enumerate(rows) if not is_coded(r, hyps)]
    width = min(shutil.get_terminal_size((100, 24)).columns, 100) - 4
    print(f"{len(rows) - len(todo)} of {len(rows)} coded; {len(todo)} to go.")
    print("Code what the analyst asks, not what you think of AI. s skips a row (offered again next run).")
    done = 0
    try:
        for n, i in enumerate(todo, 1):
            r = rows[i]
            print("\n" + "=" * width)
            print(f"[{n}/{len(todo)}]  {r['symbol']}  {r['report_date']}  {r['speaker']}  {r['question_id']}")
            print("-" * width)
            for para in r["text"].splitlines() or [""]:
                print(textwrap.fill(para, width=width, initial_indent="  ", subsequent_indent="  "))
            try:
                lab = {h["id"]: ask_yn(h["id"], h["hypothesis"]) for h in cb}
                note = ask("\nnote (optional, Enter for none) > ")
            except Skip:
                print("  skipped")
                continue
            r.update(lab, coder=coder, note=" ".join(note.split()))
            write_atomic(a.sample, tsv_bytes(rows, cols))
            done += 1
    except (Quit, KeyboardInterrupt):
        print("\nquit")
    print(f"coded {done} rows this session; {sum(is_coded(r, hyps) for r in rows)} of {len(rows)} total. Saved.")
    return 0


def q_cmd_score(a: argparse.Namespace) -> int:
    if not a.sample.exists():
        sys.exit("no sample: run `uv run scripts/ec_gold.py --set questions sample` first")
    hyps = q_hyps()
    rows = read_tsv(a.sample)
    coded = [r for r in rows if is_coded(r, hyps)]
    n_coded: dict[str, int] = {}
    for r in coded:
        n_coded[r["stratum"]] = n_coded.get(r["stratum"], 0) + 1
    weight = {s: int(next(r["stratum_population"] for r in rows if r["stratum"] == s)) / c for s, c in n_coded.items()}
    p: dict[tuple[str, str], tuple[float, float]] = {}
    if coded:
        con = duckdb.connect()
        q_scores(con)
        con.execute("CREATE TABLE ids (question_id VARCHAR)")
        con.executemany("INSERT INTO ids VALUES (?)", [(r["question_id"],) for r in coded])
        for qid, h, d, m in con.execute("SELECT question_id, hypothesis_id, p_deb, p_mod FROM qsc JOIN ids USING (question_id)").fetchall():
            p[(qid, h)] = (d, m)
    groups = {"oversight": q_group("oversight"), "commercial": q_group("commercial")}

    def pred1(qid: str, h: str, witness: str) -> bool:
        d, m = p[(qid, h)]
        return {"deberta": d >= THRESHOLD, "modernbert": m >= THRESHOLD, "both": d >= THRESHOLD and m >= THRESHOLD}[witness]

    targets = [(h, [h]) for h in hyps] + [(f"group:{g}", ids) for g, ids in groups.items()]
    out = []
    for name, ids in targets:
        for wt in ("deberta", "modernbert", "both"):
            tp = fp = fn = wtp = wpp = wgp = 0.0
            for r in coded:
                g = any(r[h] == "y" for h in ids)
                q = any(pred1(r["question_id"], h, wt) for h in ids)
                w = weight[r["stratum"]]
                tp += g and q
                fp += q and not g
                fn += g and not q
                wtp += w * (g and q)
                wpp += w * q
                wgp += w * g
            out.append({"hypothesis": name, "witness": "both>=0.5" if wt == "both" else wt, "n_coded": len(coded),
                        "gold_pos": int(tp + fn), "pred_pos": int(tp + fp), "true_pos": int(tp),
                        "precision_w": rate(wtp, wpp), "recall_w": rate(wtp, wgp)})
    cols = ["hypothesis", "witness", "n_coded", "gold_pos", "pred_pos", "true_pos", "precision_w", "recall_w"]
    strata_seen = ", ".join(f"{s}={n_coded[s]}" for s in Q_ALLOCATION if s in n_coded) or "none"
    note = (f"# {len(coded)} of {len(rows)} sample rows coded (coded per stratum: {strata_seen}). "
            f"precision_w/recall_w are stratum-weighted (w = stratum_population / coded in stratum); counts are unweighted. "
            f"A group is positive when any member is; for both>=0.5, when any member has both witnesses >= 0.5. "
            f"Blank = undefined (no denominator).\n")
    data = tsv_bytes(out, cols, note)
    score_path = a.sample.with_name(SCORE.name)
    write_atomic(score_path, data)
    sys.stdout.write(data.decode("utf-8"))
    print(f"wrote {rel(score_path)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", choices=["windows", "questions"], default="windows",
                    help="unit set: AI windows (codebook-v0.1) or analyst questions (codebook-questions-v0.1)")
    ap.add_argument("--sample", type=Path, default=None,
                    help="sample file (default: gold/earnings-calls/<codebook>/sample.tsv); score.tsv is written beside it")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample", help="draw the stratified sample (deterministic)")
    s.add_argument("--n", type=int, default=None, help=f"default {BASE_N} (windows) / {Q_BASE_N} (questions)")
    s.add_argument("--force", action="store_true", help="overwrite a sample that already has coded rows")
    c = sub.add_parser("code", help="interactive coding loop (resumable)")
    c.add_argument("--coder", default="")
    sub.add_parser("score", help="precision/recall per hypothesis and witness")
    a = ap.parse_args()
    if a.set == "questions":
        a.sample = a.sample or Q_SAMPLE
        if a.cmd == "sample" and a.n is None:
            a.n = Q_BASE_N
        return {"sample": q_cmd_sample, "code": q_cmd_code, "score": q_cmd_score}[a.cmd](a)
    a.sample = a.sample or SAMPLE
    if a.cmd == "sample" and a.n is None:
        a.n = BASE_N
    return {"sample": cmd_sample, "code": cmd_code, "score": cmd_score}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())

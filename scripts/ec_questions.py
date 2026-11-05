#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "duckdb==2.0.0",
#   "blake3==1.0.8",
# ]
# ///
"""Analyst questions about AI on S&P 500 earnings calls: the question corpus.

Unit: one *AI question*, meaning a paragraph spoken in the Q&A by someone
outside the company that contains '?', is at most MAX_CHARS long, and contains an AI term (the same TERMS as
scripts/ec_extract.py). Questioners are identified from the call's own
structure, not from the cross-issuer name count used for `role` in the window
corpus, which mislabels executives whose names recur across firms:

  1. Q&A starts at the first paragraph announcing questions (QA_START below)
     that comes after someone other than the operator has spoken, so the
     operator's opening "...followed by a question-and-answer session" does
     not count. Calls with no such paragraph are skipped and counted.
  2. Anyone who spoke before that point gave prepared remarks. Anyone who gave
     prepared remarks on ANY of the issuer's calls is an insider.
  3. A questioner is a non-operator speaker, not an insider, with at least one
     turn that directly follows an Operator turn (the operator introduces
     each questioner; executives answer after the questioner, not the operator),
     and at least one Q&A turn containing '?'.

Every questioner turn in an S&P call is counted for the denominator, AI or
not, so "share of analyst questions that are about AI" has a base.

    uv run scripts/ec_questions.py build     # writes corpus/earnings-calls/ai-questions.parquet + question-calls.tsv
    uv run scripts/ec_questions.py verify    # re-reads every turn from the pinned source and re-hashes it

The committed table holds ids, metadata and the BLAKE3 of each full turn, never
the text; the same table with the verbatim turn is written to the gitignored
.eccorpus/ai-questions.parquet (scripts/ec_text.py). Requires the pinned source
parquet in .eccorpus/ (scripts/ec_extract.py fetch).
"""

from __future__ import annotations

import sys
from pathlib import Path

import blake3
import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ec_extract as ex  # noqa: E402  (TERMS / ANY regex, source path, corpus dir)
import ec_text as ect  # noqa: E402  (committed table vs local text)

CORPUS = ex.CORPUS
OUT_Q = ect.QUESTIONS          # committed: ids, metadata, BLAKE3; no text
OUT_Q_TEXT = ect.QUESTIONS_TEXT  # gitignored .eccorpus/: the same table with the turn text
OUT_CALLS = CORPUS / "question-calls.tsv"
MAX_CHARS = 3000  # 99th percentile of AI questioner turns is ~3,300; longer turns are mostly mis-attributed remarks
QA_START = (r"(?i)(first question|question-and-answer|question and answer|\bq ?& ?a\b|"
            r"open (it |the call |the line |the floor )?(up )?(for|to) (your )?questions|"
            r"(take|get to|begin|start) (your |the )?questions|questions? (will )?come[s]? from|"
            r"queue for questions|polling for questions)")


def b3(s: str) -> str:
    return blake3.blake3(s.encode()).hexdigest()


def cmd_build() -> int:
    src = ex.source_path()
    con = duckdb.connect()
    con.execute("SET threads=8")
    con.execute(f"CREATE VIEW src AS SELECT * FROM '{src}'")
    con.execute(f"""CREATE TABLE calls AS SELECT symbol, fiscal_year, fiscal_quarter FROM read_csv('{CORPUS / "calls.tsv"}')
                    WHERE (duplicate_of IS NULL OR duplicate_of = '') AND n_paragraphs > 2""")
    con.execute("""
      CREATE TABLE para AS
      SELECT s.symbol, s.fiscal_year, s.fiscal_quarter, s.report_date::VARCHAR AS report_date,
             t.paragraph_number AS pn, t.speaker AS speaker_raw, t.content,
             -- one person, one key: drop the " - Company, Inc." suffix some transcripts append
             lower(trim(split_part(coalesce(t.speaker, ''), ' - ', 1))) AS speaker,
             lower(trim(coalesce(t.speaker, ''))) = 'operator' AS is_op
      FROM src s SEMI JOIN calls c USING (symbol, fiscal_year, fiscal_quarter),
           LATERAL (SELECT unnest(s.transcripts, recursive := true)) t""")
    # The operator's opening ("...followed by a question-and-answer session") is not the
    # start of Q&A: it must come after someone other than the operator has spoken.
    con.execute("""
      CREATE TABLE first_speaker AS SELECT symbol, fiscal_year, fiscal_quarter, min(pn) AS fs_pn
      FROM para WHERE NOT is_op GROUP BY ALL""")
    con.execute(f"""
      CREATE TABLE qa AS SELECT p.symbol, p.fiscal_year, p.fiscal_quarter, min(p.pn) AS qa_pn
      FROM para p JOIN first_speaker f USING (symbol, fiscal_year, fiscal_quarter)
      WHERE p.pn > f.fs_pn AND regexp_matches(p.content, '{QA_START}') GROUP BY ALL""")
    con.execute("""
      CREATE TABLE prepared AS SELECT DISTINCT p.symbol, p.fiscal_year, p.fiscal_quarter, p.speaker
      FROM para p JOIN qa USING (symbol, fiscal_year, fiscal_quarter) WHERE p.pn < qa.qa_pn AND NOT p.is_op""")
    # Insiders: anyone who gave prepared remarks on ANY of this issuer's calls.
    con.execute("CREATE TABLE insider AS SELECT DISTINCT symbol, speaker FROM prepared")
    con.execute("""
      CREATE TABLE seq AS SELECT *, lag(is_op) OVER (PARTITION BY symbol, fiscal_year, fiscal_quarter ORDER BY pn) AS prev_op
      FROM para""")
    con.execute("""
      CREATE TABLE questioner AS
      SELECT DISTINCT s.symbol, s.fiscal_year, s.fiscal_quarter, s.speaker
      FROM seq s JOIN qa USING (symbol, fiscal_year, fiscal_quarter)
      ANTI JOIN insider i USING (symbol, speaker)
      WHERE s.pn > qa.qa_pn AND NOT s.is_op AND s.prev_op AND s.speaker IS NOT NULL AND trim(s.speaker) <> ''""")
    # ...and who actually asks something: at least one of their Q&A turns contains '?'.
    con.execute("""
      DELETE FROM questioner q WHERE NOT EXISTS (
        SELECT 1 FROM para p JOIN qa USING (symbol, fiscal_year, fiscal_quarter)
        WHERE p.symbol = q.symbol AND p.fiscal_year = q.fiscal_year AND p.fiscal_quarter = q.fiscal_quarter
          AND p.speaker = q.speaker AND p.pn > qa.qa_pn AND p.content LIKE '%?%')""")
    con.execute("""
      CREATE TABLE turns AS
      SELECT p.* FROM para p JOIN qa USING (symbol, fiscal_year, fiscal_quarter)
      SEMI JOIN questioner q USING (symbol, fiscal_year, fiscal_quarter, speaker)
      WHERE p.pn > qa.qa_pn""")
    any_re = ex.ANY.replace("'", "''")
    con.execute(f"ALTER TABLE turns ADD COLUMN ai BOOLEAN")
    con.execute(f"UPDATE turns SET ai = regexp_matches(content, '{any_re}')")

    # Unit: an AI questioner turn that asks something ('?') and is question-sized (<= MAX_CHARS).
    rows = con.execute(f"""SELECT symbol, fiscal_year, fiscal_quarter, report_date, pn, speaker_raw, content
                          FROM turns WHERE ai AND content LIKE '%?%' AND length(content) <= {MAX_CHARS} ORDER BY symbol, fiscal_year, fiscal_quarter, pn""").fetchall()
    out = []
    for sym, fy, fq, rd, pn, spk, content in rows:
        ph = b3(content)
        out.append((b3(f"q|{sym}|{fy}|{fq}|{pn}|{ph}")[:16], sym, fy, fq, rd, pn, spk, ph, len(content), content))
    con.execute("""CREATE TABLE q (question_id VARCHAR, symbol VARCHAR, fiscal_year INT, fiscal_quarter INT,
                   report_date VARCHAR, paragraph_number INT, speaker VARCHAR, turn_blake3 VARCHAR,
                   n_chars INT, text VARCHAR)""")
    con.executemany("INSERT INTO q VALUES (?,?,?,?,?,?,?,?,?,?)", out)
    if con.execute("SELECT count(*) - count(DISTINCT question_id) FROM q").fetchone()[0]:
        sys.exit("question_id collision")
    order, opts = "ORDER BY symbol, fiscal_year, fiscal_quarter, paragraph_number", \
        "(FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 8192)"
    ex.BULK.mkdir(exist_ok=True)
    con.execute(f"COPY (SELECT * FROM q {order}) TO '{OUT_Q_TEXT}' {opts}")
    con.execute(f"COPY (SELECT * EXCLUDE (text) FROM q {order}) TO '{OUT_Q}' {opts}")
    con.execute(f"""
      COPY (SELECT c.symbol, c.fiscal_year, c.fiscal_quarter, qa.qa_pn IS NOT NULL AS qa_found,
                   count(DISTINCT qn.speaker) AS n_questioners,
                   count(t.pn) AS n_questioner_turns, count(t.pn) FILTER (WHERE t.ai AND t.content LIKE '%?%' AND length(t.content) <= {MAX_CHARS}) AS n_ai_questions
            FROM calls c LEFT JOIN qa USING (symbol, fiscal_year, fiscal_quarter)
            LEFT JOIN questioner qn USING (symbol, fiscal_year, fiscal_quarter)
            LEFT JOIN turns t ON t.symbol = c.symbol AND t.fiscal_year = c.fiscal_year
                 AND t.fiscal_quarter = c.fiscal_quarter AND t.speaker = qn.speaker
            GROUP BY ALL ORDER BY 1, 2, 3)
      TO '{OUT_CALLS}' (HEADER, DELIMITER '\t')""")
    s = con.execute(f"""SELECT count(*), count(*) FILTER (WHERE qa_found), sum(n_questioner_turns), sum(n_ai_questions)
                        FROM read_csv('{OUT_CALLS}')""").fetchone()
    print(f"calls {s[0]}, Q&A found {s[1]}, questioner turns {s[2]}, AI questions {s[3]} -> {OUT_Q.name}")
    return cmd_verify()


def cmd_verify() -> int:
    """Re-read every question turn from the pinned source and re-hash it (the committed table
    carries no text), then check the local text table, if built, against the same hashes."""
    con = duckdb.connect()
    con.execute("SET threads=8")
    con.execute(f"CREATE TABLE q AS SELECT * FROM '{OUT_Q}'")
    text = ex.source_paragraphs(con, "q")
    bad = 0
    for qid, sym, fy, fq, pn, tb, n in con.execute(
            "SELECT question_id, symbol, fiscal_year, fiscal_quarter, paragraph_number, turn_blake3, n_chars FROM q").fetchall():
        t = text.get((sym, fy, fq, pn))
        if t is None or b3(t) != tb or len(t) != n or b3(f"q|{sym}|{fy}|{fq}|{pn}|{tb}")[:16] != qid:
            bad += 1
    local = "not built"
    if OUT_Q_TEXT.exists():
        lb = con.execute(f"""SELECT count(*) FROM q FULL JOIN '{OUT_Q_TEXT}' x USING (question_id)
                             WHERE x.turn_blake3 IS DISTINCT FROM q.turn_blake3""").fetchone()[0]
        lb += sum(b3(t) != tb for tb, t in con.execute(f"SELECT turn_blake3, text FROM '{OUT_Q_TEXT}'").fetchall())
        local, bad = f"{lb} bad", bad + lb
    print(f"verify: {con.execute('SELECT count(*) FROM q').fetchone()[0]} questions re-read from the pinned source, "
          f"{bad} mismatches; local text table {local}")
    return 1 if bad else 0


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "build":
        return cmd_build()
    if cmd == "verify":
        return cmd_verify()
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main())

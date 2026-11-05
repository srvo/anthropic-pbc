# S&P 500 earnings calls: AI corpus

Every passage in which a current S&P 500 company's earnings call mentions AI,
byte-anchored, with the all-calls denominator. Method:
[`docs/earnings-call-ai-corpus.md`](../../docs/earnings-call-ai-corpus.md).

**No transcript text is stored here.** Quotes from the calls may be published;
whole transcripts and the whole corpus may not (maintainer decision,
2026-11-04). This folder holds ids, symbols, dates, speakers and roles,
paragraph numbers, `[start_char, end_char)` offsets and BLAKE3 hashes. The text
is rebuilt from the pinned source into the gitignored `.eccorpus/`, and
`verify` re-slices every window from the source and checks every hash.

| File | What it is |
|---|---|
| `MANIFEST.tsv` | Pins: source parquet (HF dataset commit, bytes, BLAKE3, SHA-256 = HF LFS oid) and the Wikipedia revision defining the universe. |
| `sp500-constituents.tsv` | 503 tickers + CIKs from Wikipedia revision 1382178819. |
| `calls.tsv` | **Denominator.** Every S&P 500 call in the source, AI or not: paragraphs, duplicate share-class listing, AI paragraph and window counts. |
| `ai-paragraphs.parquet` | Every source paragraph matching the AI term regex: its key, speaker, role and BLAKE3. No text. |
| `ai-windows.parquet` | The unit of analysis: match sentence ±1, as `[start_char, end_char)` of a source paragraph, with BLAKE3 of the window and the paragraph. No text. |
| `codebook-v0.1.tsv` | The NLI hypotheses the witnesses score. |
| `question-calls.tsv` | **Question denominator.** Per call: whether a Q&A was found, questioners, all questioner turns, AI questions. |
| `ai-questions.parquet` | Every AI question an outside questioner asked in the Q&A: its key, speaker, length and the BLAKE3 of the full turn (`scripts/ec_questions.py`). No text. |
| `codebook-questions-v0.1.tsv` | The NLI hypotheses for question intent: commercial, capital, threat, workforce, oversight. |

Rebuild and check from scratch:

    uv run scripts/ec_extract.py fetch          # 2.3 GB into .eccorpus/, verified against MANIFEST
    uv run scripts/ec_extract.py constituents
    uv run scripts/ec_extract.py build          # byte-identical outputs on rerun
    uv run scripts/ec_extract.py verify         # re-slice every window from the source + re-hash
    uv run scripts/ec_questions.py build        # analyst questions; verifies against the source

`build` also writes the text, locally: `.eccorpus/ai-paragraphs.parquet`,
`.eccorpus/ai-windows.parquet` and `.eccorpus/ai-questions.parquet` are the
tables above with their verbatim text, joined by id (`scripts/ec_text.py`).
They are byte-identical to the tables this folder held before 2026-11-04, so
the `windows_blake3` recorded in each witness run names them.

Model output lives apart from the corpus, in `proposals/earnings-calls/`, because
it is a witness's proposal, not text.

## Attribution and terms

This folder is **not** covered by the repository's CC0 dedication.

- **Transcripts:** derived from the `defeatbeta/yahoo-finance-data` dataset
  (https://huggingface.co/datasets/defeatbeta/yahoo-finance-data), table
  `stock_earning_call_transcripts`, commit `31ee0261`, licensed under the
  **Open Data Commons Attribution License (ODC-BY 1.0)**. That dataset states its
  transcripts are sourced from Yahoo Finance earnings-call pages and are intended
  for research and educational purposes. The words are the speakers'. This
  folder republishes none of them: it holds ids, offsets and hashes, and the
  text is rebuilt locally from the pinned source. Short quotes, each with its
  window or question id, are published in the reports
  (`proposals/earnings-calls/**/report/risk-quotes-ttm.tsv`,
  `oversight-questions.tsv`), the gold samples (`gold/earnings-calls/`) and the
  deck.
- **S&P 500 constituent list:** derived from Wikipedia, "List of S&P 500
  companies", revision 1382178819, **CC BY-SA 4.0**.
- "S&P 500" is a trademark of S&P Dow Jones Indices LLC; this corpus is not
  affiliated with or endorsed by it.

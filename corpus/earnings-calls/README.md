# S&P 500 earnings calls: AI corpus

Every passage in which a current S&P 500 company's earnings call mentions AI,
verbatim, byte-anchored, with the all-calls denominator. Method:
[`docs/earnings-call-ai-corpus.md`](../../docs/earnings-call-ai-corpus.md).

| File | What it is |
|---|---|
| `MANIFEST.tsv` | Pins: source parquet (HF dataset commit, bytes, BLAKE3, SHA-256 = HF LFS oid) and the Wikipedia revision defining the universe. |
| `sp500-constituents.tsv` | 503 tickers + CIKs from Wikipedia revision 1382178819. |
| `calls.tsv` | **Denominator.** Every S&P 500 call in the source, AI or not: paragraphs, duplicate share-class listing, AI paragraph and window counts. |
| `ai-paragraphs.parquet` | Every paragraph matching the AI term regex, verbatim, with BLAKE3. |
| `ai-windows.parquet` | The unit of analysis: match sentence ±1, as `[start_char, end_char)` of a stored paragraph, with BLAKE3. |
| `codebook-v0.1.tsv` | The NLI hypotheses the witnesses score. |

Rebuild and check from scratch:

    uv run scripts/ec_extract.py fetch          # 2.3 GB, verified against MANIFEST
    uv run scripts/ec_extract.py constituents
    uv run scripts/ec_extract.py build          # byte-identical outputs on rerun
    uv run scripts/ec_extract.py verify         # re-slice + re-hash every window

Model output lives apart from the corpus, in `proposals/earnings-calls/`, because
it is a witness's proposal, not text.

## Attribution and terms

This folder is **not** covered by the repository's CC0 dedication.

- **Transcripts:** derived from the `defeatbeta/yahoo-finance-data` dataset
  (https://huggingface.co/datasets/defeatbeta/yahoo-finance-data), table
  `stock_earning_call_transcripts`, commit `31ee0261`, licensed under the
  **Open Data Commons Attribution License (ODC-BY 1.0)**. That dataset states its
  transcripts are sourced from Yahoo Finance earnings-call pages and are intended
  for research and educational purposes. The words are the speakers'; this corpus
  republishes only the AI-mentioning paragraphs, for research.
- **S&P 500 constituent list:** derived from Wikipedia, "List of S&P 500
  companies", revision 1382178819, **CC BY-SA 4.0**.
- "S&P 500" is a trademark of S&P Dow Jones Indices LLC; this corpus is not
  affiliated with or endorsed by it.

# Hacker News: Anthropic and AI-security comments (IDs only)

Two focused sets of Hacker News comments, January 2021 to August 2026: those
that mention Anthropic or Claude, and those about AI security incidents (CVEs,
breaches, prompt injection, jailbreaks, leaked weights or keys). Method:
[`docs/hacker-news-corpus.md`](../../docs/hacker-news-corpus.md).

**No comment text and no usernames are stored here.** HN commenters are mostly
private individuals, so this folder holds item ids, character offsets into a
deterministic normalisation of each comment, and BLAKE3 hashes. The text is
rebuilt locally from the pinned source into the gitignored `.hncorpus/`, and
`verify` checks every hash. Any comment can be read at
`https://news.ycombinator.com/item?id=<item_id>`.

| File | What it is |
|---|---|
| `MANIFEST.tsv` | Pins: 68 monthly parquet files of `open-index/hacker-news` at dataset commit `c54ced59`, with bytes and SHA-256 (= the Hugging Face LFS oid). |
| `months.tsv` | **Denominator.** Per month: all live comments, and comments in each set. |
| `windows.parquet` | The unit: match sentence ±1 as `[start_char, end_char)` of the normalised comment, with set, term families, and BLAKE3 of the window and the comment. |

Rebuild and check from scratch:

    uv run scripts/hn_extract.py fetch    # 5.6 GB into .hncorpus/, SHA-256 checked
    uv run scripts/hn_extract.py build    # byte-identical on rerun; verifies on completion
    uv run scripts/hn_extract.py verify

Model output lives in `proposals/hacker-news/`, as witness proposals.

## Attribution and terms

This folder is **not** covered by the repository's CC0 dedication.

- **Source:** `open-index/hacker-news`
  (https://huggingface.co/datasets/open-index/hacker-news), licensed under the
  **Open Data Commons Attribution License (ODC-BY 1.0)**. Its items mirror the
  public Hacker News API (https://github.com/HackerNewsAPI/HN-API). The comments
  belong to their authors; this folder republishes none of their words.
- "Hacker News" is operated by Y Combinator; this corpus is not affiliated with
  or endorsed by it.

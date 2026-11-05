# Wikipedia AI-risk corpus

What English Wikipedia files under AI risk, pinned to one revision per article,
converted to plain text by published rules, and byte-anchored. It is a
reference map for placing call, analyst and practitioner language. Method:
[`docs/wikipedia-ai-risk-corpus.md`](../../docs/wikipedia-ai-risk-corpus.md).

| File | What it is |
|---|---|
| `MANIFEST.tsv` | **The pin.** 151 articles: title, page id, revision id, revision timestamp, as-of time (2026-11-04T00:00:00Z), bytes, MediaWiki SHA-1 and BLAKE3 of the wikitext, how the article entered (`via`), and the API URL of the revision. |
| `seeds.tsv` | The seed categories and articles, what each resolved to, and subcategories that were listed but not entered. |
| `articles.parquet` | Every paragraph of every article, verbatim from the converted Markdown: title, revision, heading path, paragraph number, `[md_start, md_end)`, BLAKE3 of the Markdown and of the paragraph. |
| `sections.tsv` | **Denominator.** Every section of every article, including dropped end-matter (`kept = 0`): heading level, heading path, paragraph and character counts. |
| `windows.parquet` | The scoring unit, in the shape of `../earnings-calls/ai-windows.parquet`: `window_id`, `[start_char, end_char)` of a stored paragraph, BLAKE3, text. |
| `dimensions-candidate.tsv` | **Candidate for human review, not a taxonomy.** Headings of the AI-risk sections of four hub articles, with the articles each section links to and a literal-only match to `codebook-v0.1.tsv`. |

Rebuild and check from scratch:

    uv run scripts/wp_extract.py fetch          # pinned revisions -> .wpcorpus/, BLAKE3 checked
    uv run scripts/wp_extract.py build          # byte-identical outputs on rerun; verifies on completion
    uv run scripts/wp_extract.py verify         # re-convert, re-slice, re-hash, rebuild and compare

`pin --as-of` re-discovers articles from live category membership and
overwrites `MANIFEST.tsv`; run it only to make a new pin.

## Attribution and terms

This folder is **not** covered by the repository's CC0 dedication.

Text in `articles.parquet`, `windows.parquet`, `sections.tsv` and
`dimensions-candidate.tsv` is from English Wikipedia, by its contributors, and
is licensed under the **Creative Commons Attribution-ShareAlike 4.0
International License (CC BY-SA 4.0)**,
https://creativecommons.org/licenses/by-sa/4.0/. These files are adapted:
templates, references, tables and images were removed and markup was
reduced to plain Markdown by `scripts/wp_extract.py`. They are shared under
the same licence.

Each article's source is the exact revision named in `MANIFEST.tsv`. Its
history and author list is at
`https://en.wikipedia.org/w/index.php?oldid=<revid>` and
`https://en.wikipedia.org/w/index.php?title=<title>&action=history`. The
151 revisions range from revid 1301533223 (2025-07-20) to revid 1383632719
(2026-11-03), each the last revision at or before 2026-11-04T00:00:00Z.

Wikipedia is a trademark of the Wikimedia Foundation; this corpus is not
affiliated with or endorsed by it.

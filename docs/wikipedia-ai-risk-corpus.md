# Wikipedia AI-risk corpus: method

### What English Wikipedia files under AI risk, pinned, as a reference map

**Status: corpus HELD as verbatim text; dimension list is a CANDIDATE.** The
corpus files are deterministic conversions of pinned Wikipedia revisions that
`verify` re-checks byte for byte. `dimensions-candidate.tsv` is read from
Wikipedia's own headings by a published rule. It is not a taxonomy and not a
codebook. Sloane decides the codebook. No model has scored anything here.

Version: v0.1 · 2026-11-04. Companion to
[`earnings-call-ai-corpus.md`](earnings-call-ai-corpus.md). This file does not
edit the paper or its hash.

## 1. Purpose

The earnings-call corpus records what executives and analysts say about AI.
This corpus records what one public reference work says the risks of AI are.
It is the reference space that call, analyst and practitioner language can
later be placed against. It is a map of a dialogue, not a ground truth about
risk.

## 2. Discovery

Discovery is a published seed list, written as constants in
`scripts/wp_extract.py`:

- **Categories:** AI safety; Ethics of artificial intelligence; Existential
  risk from artificial intelligence; Regulation of artificial intelligence.
  Three other candidate names do not exist on Wikipedia and were dropped
  (`seeds.tsv`).
- **Depth 1.** The article members of each category are taken. Subcategories
  are listed in `seeds.tsv` and not entered. On 2026-11-04 the only
  subcategories hold biographies of advocates, scientists and legal scholars.
- **Seed articles:** 18 named hub and risk articles. A missing title is dropped
  and reported, and a redirect is followed and recorded.

Result: 151 articles. 18 seed articles were named. One, "AI-assisted
targeting", does not exist and was dropped. One, "Environmental impact of
artificial intelligence", redirects to "Environmental impact of AI". The four
categories hold 35, 12, 66 and 68 articles, with overlap.

Category membership is read when `pin` runs, not as of a past date. The pin
is therefore not re-runnable to the same list later. `MANIFEST.tsv` is the
pin; `fetch` rebuilds from it on any date.

Category members are kept whatever they are. The categories hold
organisations, books, laws, films and a few biographies beside risk
articles, and the `via` column records how each article entered. Filtering
them would be a judgment, so it is left to the reader of the output.

## 3. Pinning

Each article is pinned to its last revision at or before `--as-of`
(2026-11-04T00:00:00Z), using the API's `rvstart` with `rvdir=older`.
`MANIFEST.tsv` records title, page id, revision id, revision timestamp, the
as-of time, byte count, MediaWiki's own SHA-1 and the BLAKE3 of the wikitext.
Time enters only as that recorded argument. The revisions run from revid
1301533223 (2025-07-20) to revid 1383632719 (2026-11-03).

## 4. Conversion

Wikitext is parsed with mwparserfromhell 0.7.2 and rendered to plain
Markdown by published rules:

- Headings are kept as `#` lines, one `#` per level. The lead is `(lead)`.
- Templates, references, tables, galleries, maths and files are dropped. A
  short allowlist of inline templates whose argument is prose (`nowrap`,
  `lang` and similar) keeps that argument.
- Links are reduced to their label. Category, file and interlanguage links
  are dropped. A bracketed external link keeps its label; a bare URL is
  dropped.
- List items become `- ` lines; bold and italic markup is removed.
- Standard end-matter sections (References, Notes, See also, External links,
  Further reading and their variants) are dropped with their subsections.
  `sections.tsv` still lists them, with `kept = 0`.
- Whitespace is collapsed, and the space or empty parentheses a dropped
  template leaves behind are removed.

Dropping templates loses some words, for example a converted unit or a
date written through a template. The loss is the same on every rebuild.

## 5. Unit

A **paragraph** is a run of non-blank lines in the converted Markdown, so a
prose paragraph or one list. Each is stored with `[md_start, md_end)` in its
article's Markdown, the Markdown's BLAKE3 and its own BLAKE3.

A **window** is the scoring unit, in the shape of the earnings-call
`ai-windows.parquet`. It is the whole paragraph when the paragraph is at most
1,500 characters. A longer paragraph is cut into consecutive chunks of whole
sentences, each at most 1,500 characters. Paragraphs under 80 characters,
mostly single list items and captions, get no window.

Result: 1,984 sections, 3,761 paragraphs (median 442 characters, 90th
percentile 939, maximum 7,565) and 3,749 windows. 78 paragraphs are under 80
characters and 55 are over 1,500.

The paragraph is the right unit here and the sentence window is not. A
Wikipedia paragraph is written to carry one point, unlike a transcript
paragraph that can hold a whole prepared speech. The 1,500-character ceiling
is the one the earnings-call windows use, and it keeps a window inside the
witnesses' 512-token input. The classifier can score windows with
`--units corpus/wikipedia-ai-risk/windows.parquet --id-col window_id`.

## 6. Candidate dimensions

`dimensions-candidate.tsv` lists headings from four hub articles:

- AI safety, Ethics of artificial intelligence, and Existential risk from
  artificial intelligence: every kept heading.
- Artificial intelligence: only the subtree under "Ethics > Risks and harm".

Each row gives the source title, revision, heading level, heading path, the
targets of the section's `{{Main}}`, `{{Further}}` and `{{See also}}`
hatnotes, and every article the section's own text links to.
`n_linked_in_corpus` counts how many of those targets are in this corpus.

The `codebook_v0_1_literal_match` column names a
`corpus/earnings-calls/codebook-v0.1.tsv` id only when that id, with
underscores read as spaces, appears as a whole word in the heading. Most rows
are blank by design. No hypothesis was written for this list.

Result: 110 headings. 13 carry a literal match, and a literal match is not a
semantic one. For example, "Authoritarian governance" matches `governance`,
which in the codebook means a company's own oversight. "Algorithmic biases"
does not match `bias`, because the rule takes whole words only.

Every row is marked `candidate: not reviewed`. Choosing which headings
become dimensions, merging them, and writing hypotheses is Sloane's decision.

## 7. What this corpus does not answer

- **Wikipedia records editor attention, not risk.** A heading exists because
  editors wrote one. Its size measures how much they wrote, and neither
  measures likelihood or harm.
- **English-language and Western bias.** The editors who write English
  Wikipedia skew towards North America and Europe. Risks felt most outside
  them, such as labelling work, data-centre siting, and surveillance in other
  legal systems, can be thin or absent here.
- **Recency.** The pin is one day's text. Articles on fast-moving subjects
  are rewritten often, and the structure of the hub articles will change.
- **Categories are curated loosely.** Membership mixes risks with the
  organisations, books and fiction about them, and some relevant articles are
  in no seed category.
- **Silence is not absence.** A risk that has no heading has no heading. It
  is not shown to be unimportant.
- **No model output yet.** Scoring windows against the codebook is a
  separate, witnessed step under
  [`bert-enrichment-spec.md`](bert-enrichment-spec.md) §5.

## 8. Rebuild

    uv run scripts/wp_extract.py pin --as-of 2026-11-04   # only to re-pin; overwrites MANIFEST.tsv
    uv run scripts/wp_extract.py fetch                    # pinned revisions -> .wpcorpus/, BLAKE3 checked
    uv run scripts/wp_extract.py build                    # verifies on completion
    uv run scripts/wp_extract.py verify                   # re-convert, re-slice, re-hash, rebuild and compare

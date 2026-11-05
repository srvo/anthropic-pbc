# Democracy proxies: GDELT phrase timelines and Rooney Report toplines

Quick, citable proxy series for "health of democracy" as a public topic (how
often news and television say the words) and as stated attitudes (what
survey respondents tell the Notre Dame Health of Democracy Survey). Method and
limits: [`docs/democracy-proxies.md`](../../docs/democracy-proxies.md).

**None of these series measures any effect of Anthropic on democracy.** They
measure attention and stated attitudes. Anthropic co-mention counts show only
whether the company appears near the words.

| File | What it is |
|---|---|
| `MANIFEST.tsv` | Pins: every GDELT API response and every Rooney PDF/page, with request URL, bytes, SHA-256, BLAKE3 and as-of date. The bytes live in the gitignored `.democorpus/`. GDELT responses cannot be re-requested identically later, so the saved bytes are the pin. |
| `gdelt-timelines.tsv` | One row per (source, query, mode, series, period): `value` and `unit`. DOC rows from `timelinevolraw` also carry a `(norm)` series: total articles GDELT monitored that day. **As of 2026-11-04, 17 of 24 requests are pinned**: every TV response, and the DOC `timelinevol` responses except the `democracy` control. The DOC `democracy` control and all DOC `timelinevolraw` responses hit GDELT's rate limit (HTTP 429) and are marked `NOT PINNED` in `gdelt-summary.tsv`. |
| `gdelt-summary.tsv` | Per query: resolution, first and last period, periods with a non-zero value, peak period and value, and the sum. |
| `rooney-reports.tsv` | The 13 Rooney Reports linked from the listing page: PDF SHA-256, pages, embedded images per page (charts and logos, not extracted), and any AI-use disclosure, verbatim. |
| `rooney-transcription.tsv` | **Input, hand-transcribed.** Every percent stated in report text, with group, wave as stated, the report's wording, and a verbatim quote. |
| `rooney-toplines.tsv` | **Output.** The transcription after `build` has checked each quote against the page text of the pinned PDF and each percent against its quote, with the quote's BLAKE3. |
| `rooney-questionnaire.tsv` | **Input, hand-copied.** Item stems from the two questionnaires the Institute publishes as PDFs (October 2025, May 2026). |
| `rooney-items.tsv` | **Output.** The stems after `build` has found each in the pinned questionnaire, with page numbers. |

Rebuild and check:

    uv run scripts/democracy_proxies.py fetch-gdelt  --as-of 2026-11-04   # skips anything already pinned
    uv run scripts/democracy_proxies.py fetch-rooney --as-of 2026-11-04
    uv run scripts/democracy_proxies.py build     # no network; byte-identical on rerun
    uv run scripts/democracy_proxies.py verify    # re-hash every pin, rebuild, compare bytes

A fresh `fetch-gdelt` on another day returns different bytes. That would be a
new pin, not a reproduction: keep the old `.democorpus/` to reproduce these
TSVs.

## Attribution and terms

This folder is **not** covered by the repository's CC0 dedication.

- **GDELT.** Data from the GDELT Project (https://www.gdeltproject.org/),
  DOC 2.0 and TV 2.0 APIs. GDELT's terms of use
  (https://www.gdeltproject.org/about.html) make its datasets "available for
  unlimited and unrestricted use for any academic, commercial, or governmental
  use of any kind without fee", and require that "any use or redistribution of
  the data must include a citation to the GDELT Project and a link to this
  website". This README is that citation. TV results come from captions in the
  Internet Archive's Television News Archive (https://archive.org/details/tv),
  which we credit as the underlying source. The raw responses stay in
  `.democorpus/`.
- **Rooney Reports and questionnaires.** (c) University of Notre Dame,
  Rooney Democracy Institute. This folder republishes short verbatim quotes and
  the numbers in them, with page anchors, for commentary and research. The PDFs
  are not redistributed; each is pinned by URL and SHA-256. Cite the survey as
  the Institute asks: Hall, Matthew E.K., and David E. Campbell. 2022. *Notre
  Dame health of democracy survey.* Notre Dame, IN: Rooney Democracy Institute.
  https://rooneyinstitute.nd.edu/research/health-of-democracy-survey/

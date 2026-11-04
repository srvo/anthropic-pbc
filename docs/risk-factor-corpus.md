# Risk-factor corpus — method and limits

### What this corpus is, and what it refuses to be

Status: METHOD. Binds nothing. The corpus is an input to analysis, not a finding.
Nothing here is scored, summarized, or judged. Every downstream claim must cite a
`text_blake3` value and re-slice it, per [`descartes-spec.md`](descartes-spec.md).

Sources: SEC EDGAR primary documents, addressed through the
`defeatbeta/yahoo-finance-data` filing index on Hugging Face (ODC-BY).

Version: v1 · extractor `rf-extract-v1` · `scripts/rf_extract.py`

---

## 1. Why the parquet is not the corpus

`defeatbeta/yahoo-finance-data` publishes `data/US/stock_sec_filing.parquet`:
7,913,275 rows across 10,818 symbols, filing dates 1993-08-13 → 2026-11-02. Its
columns are metadata only — `symbol, cik, accession_number, company_name,
form_type, form_type_description, filing_date, report_date, acceptance_date_time,
filing_url`. There is no filing text in it.

So the dataset supplies the two things that make an EDGAR crawl addressable — CIK
and accession number — and nothing else. Every word in this corpus was fetched
from `sec.gov` and extracted here. Calling the parquet "the corpus" would be false.

| Form | Rows in index |
|---|---|
| 10-K | 105,908 |
| DEF 14A | 107,298 |
| 8-K | 1,241,518 |
| 10-Q | 333,169 |

## 2. Scope: 2010 → present

80,592 filings across 5,626 companies. The 1993–2009 window was excluded
deliberately, and not because of cost: 5,626 of the 5,627 distinct filers in the
whole 10-K index first appear at or after 2010, so going back to 1993 adds about
6,253 filings and roughly one company. What it would add is a *different*
disclosure vocabulary — pre-2005 filings predate the disclosure changes that
standardized Item 1A's boilerplate. Mixing them into one corpus would make
"how risk language changed" indistinguishable from "how the form changed".

Pre-2001 filings are also outside EDGAR's full-text search index, so they can only
be reached by document fetch, never by query.

## 3. Extraction

`scripts/rf_extract.py` fetches the 10-K primary document, converts HTML to text,
and slices Item 1A between its heading and the next Item heading. Raw HTML is
discarded: Item 1A is 1–3% of a filing, so storing documents would be ~200 GB
while storing anchored spans is a few GB.

The heading is the hard part, and the naive approaches all fail on real filings:

- **First match fails.** `Item 1A. Risk Factors` appears in the table of contents,
  in the forward-looking-statements note, and in cross-references ("see Item 1A")
  before it appears as the section itself.
- **Longest match fails.** ARKR's cross-reference runs into the next heading and
  produces a long but wrong span.
- **Line-anchored matching fails.** The common EDGAR generator puts the item label
  and the title in separate table cells, so the text reads
  `Item 1A \n\n Risk Factors` — never on one line.
- **Word-internal splitting is real.** Some filings wrap each letter in its own
  span, yielding `I tem 1A` (BDL, FREVS) or `ITE M 1A` (ALK).

A candidate must begin at a line start, must not be followed by a continuation
phrase (`of this Annual Report`, `below`) or a bare page number (TOC row), must
close at the next Item heading, and must land between 2,000 and 250,000 characters.
The first surviving candidate wins, on the observation that the real section
precedes its siblings in document order.

## 4. Recorded outcomes

An explicitly absent section is a fact about the filing, and is recorded as
`not-applicable` rather than counted as a failure. "Item 1A. Risk Factors. Not
applicable." is common among smaller reporting companies (JOB, CLRI, OCC, FNWD,
GHST) and "Not required for a smaller reporting company" appears too.

A section whose closing heading cannot be found is **refused**, not stored. An
earlier version of this extractor allowed spans to run to end-of-document; DGX and
ALK were silently recorded at 362,210 and 279,612 characters, having swallowed
their exhibits and Item 15. Those spans were wrong, and the fix is to drop them.
A span with an unverified end boundary is not a long span — it is a failed one.

## 5. Integrity

Every span is hashed with BLAKE3 over its UTF-8 bytes, stored as
`blobs/<hash>.txt.gz`, and re-read and re-hashed before the record is written.
`uv run scripts/rf_extract.py verify` re-checks the whole store and fails on any
missing blob or hash mismatch. Current state of the smoke sample: 128 spans, 0 bad.

The hash is the claim's anchor: a downstream quote is verifiable only if it
re-slices to the stored digest. Determinism holds — no clock, host, user or random
id enters a record; the gzip mtime is pinned to 0.

## 6. Yield, and its honest limit

On the first 200 filings — which are the *oldest* in the window and the messiest —
165 extracted, 35 failed: 82.5%. Yield is expected to rise with filing year as
documents standardize, but that is a prediction, not a measurement, until the bulk
run reports.

**A failed extraction is not an absent risk factor.** The 35 refusals in that
sample are filings where the section exists but the boundary could not be
established. Any analysis of this corpus must report coverage — extracted ÷
attempted — alongside its findings. A risk that appears in 80% of filings is
interesting only relative to the 80% that extracted.

## 7. What this corpus does not answer

Item 1A is forward-looking by design: it asks what *could* harm the company. It
is structurally hostile to admitting a realized loss, and a search over it will
never find one directly.

"Has this risk produced a direct loss?" is answerable only by joining to other
filings for the same CIK — 8-K Item 2.06 (material impairments), 8-K Item 1.05
(cyber incidents), Item 7 MD&A, litigation disclosures. That join is a separate
extractor and is not built here. Any claim that a named risk caused a dollar loss
must cite the filing where the loss is booked, never an Item 1A sentence.

---

# Part II — loss evidence

### Why this is a separate corpus, not a query over Part I

Part I answers "what did companies say could harm them." It cannot answer "what
did it cost," and no amount of searching Item 1A changes that. Item 1A is
forward-looking boilerplate by mandate; a company that suffered a loss writes the
loss into an 8-K, into MD&A, or into litigation disclosures — not into the section
asking what might go wrong.

So Part II reads a different source, selected by EDGAR's **structured `items[]`
array** rather than by text search. Five codes describe a materialized event:

| Code | Event |
|---|---|
| 1.05 | Material cybersecurity incident |
| 2.04 | Triggering events / covenant acceleration |
| 2.05 | Costs of exit or disposal |
| 2.06 | Material impairment |
| 4.02 | Non-reliance on prior financials (restatement) |

Extractor: `scripts/rf_loss.py`. Store: `.rfcorpus/loss.duckdb`.

### Result

13,570 events across 6,187 companies, 2010-01-04 → 2026-11-03, from 1,275,249
8-K filings scanned over 204 month-slices with **zero unreadable slices**.

| Item | Events |
|---|---|
| 2.05 exit/disposal costs | 4,900 |
| 4.02 restatement | 4,709 |
| 2.04 covenant acceleration | 2,906 |
| 2.06 impairment | 1,703 |
| 1.05 cyber incident | 85 |

Spot-checked against known events: the 1.05 set correctly contains VF Corp's
December 2023 breach and First American Financial's cyber incident.

### Two API traps, both found by testing

**The `items=` filter is accepted and ignored.** Querying `items=2.06` returns
2.01 filings. EDGAR does not error; it silently returns unfiltered results.
Filtering must happen client-side on the returned array, which this extractor does.

**Results cap at 10,000 per query** regardless of ordering, so enumeration slices
by month. A month above the cap is recorded as `capped` in the output rather than
silently truncated. No month in the delivered run exceeded it, but the guard stays.

### The bug: reported success while losing four months

The first implementation reported 2010 complete while silently dropping May,
August, September and November. A 9,000-hit month is ~90 sequential requests,
which trips EDGAR's rate limiter partway through paging; the failure was caught by
a bare `except Exception` and counted as a completed slice. With retry and
backoff, 2010 went from 493 to 1,190 events. Unreadable slices are now recorded as
named gaps, and the run prints them — a missing month must never look like a month
with no events.

### What an event is not

**An event is not an attribution.** A 2.06 impairment says a write-down was
booked. It does not say which risk caused it. The 1,703 impairment filings and the
52,000+ Item 1A spans share a key — CIK — and that is all they share until a human
reads both and states the link.

Any claim of the form "risk X named in filing A caused loss L in filing B" must
cite both filings and both BLAKE3 hashes. A join on CIK alone produces candidates
for reading, never conclusions. The count of shared CIKs between the two corpora
is a *work queue*, not a finding.

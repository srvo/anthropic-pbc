# Risk-factor record manifest

This directory holds a **held local audit projection**, not filing text or a
completed acquisition package. See [the method and limits](../../docs/risk-factor-corpus.md).

- `metadata.source.yml`: authored methods, attribution, rights declarations,
  column definitions and recorded pin parameters. This is the editing surface.
- `MANIFEST.tsv`: generated record-digest pins and the declared upstream revision.
  SHA-256 aggregate digests and Git revisions occupy separate columns.
- `MANIFEST.meta.yml`: generated statistics, coverage and generation provenance.
  Do not edit it directly.

Run `uv run scripts/rf_manifest.py write` from the repository root, followed by
`uv run scripts/rf_manifest.py check`. Both commands require retained staging
stores `.rfcorpus/rf.duckdb` and `.rfcorpus/loss.duckdb`. The check compares the
complete outputs without modifying them. `uv run scripts/test_rf_manifest.py`
runs synthetic tests without those stores.

Source attribution: company Form 10-K and Form 8-K filings available through
SEC EDGAR, with the Item 1A filing index addressed through
`defeatbeta/yahoo-finance-data` at the revision recorded in `MANIFEST.tsv`.
The index is described in the catalog as ODC-BY; it is not redistributed here.
Existing authored rights declarations are retained in the source metadata and
are not validated by this generator. Counts and hashes establish no new source
license, blanket permission to redistribute filings, or human endorsement.

Loss discovery did not retain attempted-month/page receipts, so its completeness
is unknown. Record-digest verification does not verify raw filing or text-blob
bytes, and no lake placement or custody receipt is claimed.

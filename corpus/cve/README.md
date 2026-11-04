# CVE records: monthly series and AI-related records

Monthly counts of published CVE records since January 2020, by severity and by
CNA, plus the CVE ids that concern AI software or credit an AI system or AI lab.
The universe, dating and severity rules reproduce Epoch AI's CVE explorer.
Method and limits: [`docs/cve-series.md`](../../docs/cve-series.md).

| File | What it is |
|---|---|
| `MANIFEST.tsv` | Pins: the cvelistV5 daily baseline release asset (URL, release tag, tag commit, bytes, SHA-256, BLAKE3) and its single inner archive `cves.zip`. |
| `monthly.tsv` | One row per month, 2020-01 to 2026-10: `n_published` (the universe), severity buckets (`critical` … `unknown`), `n_notable_cna`, `n_linux_cna`, `n_excl_linux`, and `n_published_any_id_year` (the same count without the id-year rule). |
| `monthly-by-cna.tsv` | Month × Epoch's 21 notable CNAs + `Other`. Rows sum to `n_published`. |
| `ai-related.tsv` | One row per AI-related CVE: id, publication date, CNA short name, severity, the product/description rules that matched (`field:family`), the credited AI systems, and `system:credit-type` pairs. No descriptions or credit text. |
| `monthly-ai.tsv` | Per month: `n_published`, `n_ai_product` (affected product or description matched), `n_ai_product_affected` (affected-product fields only), `n_ai_credited`, `n_ai_credited_discovery` (excluding remediation-only credits), and one `n_credit_<system>` column per credited system. |

Rebuild and check from scratch:

    uv run scripts/cve_series.py fetch     # ~650 MB release asset + ~720 MB inner zip into .cvecorpus/, checked against MANIFEST
    uv run scripts/cve_series.py build     # byte-identical outputs on rerun
    uv run scripts/cve_series.py verify    # re-check pins, rebuild in memory, compare BLAKE3
    uv run scripts/cve_series.py pin --as-of YYYY-MM-DD   # only to move the snapshot

GitHub keeps the hourly cvelistV5 releases for a limited period (about six
weeks were listed at pin time). If the asset URL stops resolving, the tag commit
in `MANIFEST.tsv` identifies the same tree in the repository's history; a zip
built from it will not be byte-identical to the release asset, so re-pin.

## Attribution and terms

This folder is **not** covered by the repository's CC0 dedication.

- **CVE records:** derived from the CVE Program's `CVEProject/cvelistV5`
  repository, used under the CVE Program's terms of use
  (https://www.cve.org/Legal/TermsOfUse). CVE® is a registered trademark of The
  MITRE Corporation. The files here carry only CVE ids, publication dates, CNA
  short names, derived severity buckets and derived rule labels; no record text.
- **Method:** the universe, dating, severity rule and notable-CNA list follow
  Epoch AI's CVE explorer (https://epoch.ai/data/cve), licensed **CC BY 4.0**.
  Credit: Epoch AI. This series is an independent rebuild, not Epoch's data; see
  the cross-check in `docs/cve-series.md`.

# Epoch AI data: pinned snapshot, 2026-11-04

A byte-level snapshot of every public Epoch AI dataset listed at
https://epoch.ai/data on 2026-11-04, kept so later analysis can join against a
fixed copy. Cyber vulnerabilities is not repeated here: `corpus/cve/` rebuilds
it from cvelistV5. This folder holds no analysis.

**The saved bytes are the pin, not the URL.** Epoch's download URLs are not
versioned, and the bundles are regenerated: zip member timestamps carry the
generation time, and `benchmark_data.zip` changed size between two downloads
made minutes apart on the pin date. A fresh download of a URL in `MANIFEST.tsv`
will usually not match its hashes. Re-pinning moves the snapshot; the
gitignored `.epochcorpus/` copy is the only one that verifies against this
manifest. To compare across snapshots, use `inventory.tsv`: its BLAKE3 hashes
cover each table's own bytes, so a table that did not change keeps its hash
when its zip is rebuilt.

| File | What it is |
|---|---|
| `MANIFEST.tsv` | One row per pinned download: dataset, role (`bundle` = the file listed on /data; `page-file` = a standalone file on the dataset page that the bundle lacks), URL, local path under `.epochcorpus/`, bytes, SHA-256, BLAKE3, `as_of`, and the "Updated" date Epoch shows for that file. |
| `CITATIONS.tsv` | Each dataset's citation string, copied verbatim from its Epoch page at pin time. |
| `inventory.tsv` | One row per member of each pinned file: dataset, file, member, kind, bytes, rows (data records, header excluded), columns, column names (JSON array), BLAKE3 of the member bytes, `anthropic_rows`, the committed path if the table is copied here, and a note. |
| `<dataset>/*.csv` | Verbatim copies of the CSV tables under 5,000,000 bytes, byte-identical to the member in the pinned file (BLAKE3 in `inventory.tsv`). |

Rebuild and check:

    uv run scripts/epoch_data.py pin --as-of 2026-11-04   # downloads into .epochcorpus/, writes MANIFEST.tsv + CITATIONS.tsv (moves the snapshot)
    uv run scripts/epoch_data.py build                    # inventory.tsv + verbatim tables; byte-identical on rerun
    uv run scripts/epoch_data.py verify                   # re-hash pins, rebuild in memory, compare BLAKE3

`pin` waits 2 s between requests and sends a descriptive User-Agent. It fails
if /data lists a download that the script does not know about.

## Files

| Dataset | Pinned file | Bytes | Updated (per Epoch) | CSV tables | Committed here |
|---|---|---:|---|---:|---:|
| AI chip components (`ai-chip-components`) | `ai_chip_components.zip` | 64,354 | 2026-07-23 | 6 | 6 |
| AI chip imports (`ai-chip-imports`) | `ai_chip_trade.zip` | 857,281 | 2026-11-03 | 2 | 2 |
| AI chip owners (`ai-chip-owners`) | `ai_chip_owners.zip` | 50,543 | 2026-05-12 | 3 | 3 |
| AI chip sales (`ai-chip-sales`) | `ai_chip_sales.zip` | 27,460 | 2026-10-21 | 5 | 5 |
| AI chip users (`ai-chip-users`) | `ai_chip_users.zip` | 6,220 | 2026-09-09 | 2 | 2 |
| AI companies (`ai-companies`) | `ai_companies.zip` | 45,273 | 2026-10-27 | 6 | 6 |
| AI data centers (`ai-data-centers`) | `data_centers.zip` | 120,128 | 2026-11-02 | 6 | 6 |
| AI models (`ai-models`) | `ai_models.zip` | 3,372,804 | 2026-11-03 | 4 | 3 |
| AI use in math research (`arxiv`) | `math_acknowledgment_trends_monthly.csv.gz` | 292,234 | 2026-10-06 | 1 | 0 |
| AI use in research (`ai-research-use`) | `ai_research_use_monthly.csv` | 249,095 | 2026-10-30 | 1 | 1 |
| | `ai_research_use_cases_monthly.csv` (page-file) | 1,853,078 | 2026-10-30 | 1 | 1 |
| | `ai_research_tools_monthly.csv` (page-file) | 1,017,129 | 2026-10-30 | 1 | 1 |
| Capabilities & benchmarking (`benchmarks`) | `benchmark_data.zip` | 2,362,346 | 2026-11-04 | 90 | 23 |
| Frontier Lab Hiring (`frontier-lab-hiring`) | `frontier_lab_hiring.zip` | 5,870,534 | 2026-11-04 | 6 | 5 |
| GPU clusters (`gpu-clusters`) | `gpu_clusters.csv` | 304,311 | 2026-03-13 | 1 | 1 |
| Machine learning hardware (`machine-learning-hardware`) | `ml_hardware.zip` | 31,979 | 2026-10-30 | 1 | 1 |
| Polling on AI usage (`polling`) | `polling_on_ai_usage_jul_2026.csv` | 720,349 | 2026-08-14 | 1 | 1 |
| | `polling_on_ai_usage_jul_2026_microdata.csv` (page-file) | 613,420 | 2026-08-14 | 1 | 1 |

Zip bundles also carry a `README.md` each and, in `benchmark_data.zip`,
`epoch_capabilities_index/eci_bootstraps.json` (3,835,779 bytes). These appear
in `inventory.tsv` with their hashes but are not copied here. Per-table CSVs
that Epoch also serves separately duplicate bundle members and are not pinned
twice.

### Kept only in `.epochcorpus/`

- **Over 5,000,000 bytes:** `ai-models/all_ai_models.csv` (6,933,174),
  `arxiv/math_acknowledgment_trends_monthly.csv` (7,836,169 bytes once
  decompressed), `frontier-lab-hiring/frontier_lab_hiring_posting_texts.csv`
  (30,834,798).
- **Third-party benchmark results:** the 67 `benchmarks/*_external.csv`
  tables. Epoch says this external data "retains its original licensing", so
  CC BY does not settle whether it can be redistributed. Epoch's own 23
  benchmark tables are committed.
- **ChatGPT usage: excluded.** The dataset's workbook reads "AI not authorized
  by YouGov is not authorized to ingest or scrape this data." This snapshot is
  built by AI tooling, so the dataset is not downloaded, pinned or parsed.

## Attribution and terms

This folder is **not** covered by the repository's CC0 dedication. Epoch AI's
data "is free to use, distribute, and reproduce provided the source and authors
are credited under the Creative Commons Attribution license"
(https://creativecommons.org/licenses/by/4.0/). The tables here are unmodified
copies. Credit, as each dataset page gives it (also in `CITATIONS.tsv`):

- Epoch AI, 'Data on AI chip components'. Published online at epoch.ai. Retrieved from 'https://epoch.ai/data/ai-chip-components' [online resource]. Accessed 4 Nov 2026.
- Epoch AI, 'Data on AI chip imports'. Published online at epoch.ai. Retrieved from 'https://epoch.ai/data/ai-chip-imports' [online resource]. Accessed 4 Nov 2026.
- Epoch AI, 'Data on AI chip owners'. Published online at epoch.ai. Retrieved from 'https://epoch.ai/data/ai-chip-owners' [online resource]. Accessed 4 Nov 2026.
- Epoch AI, 'Data on AI chip sales'. Published online at epoch.ai. Retrieved from 'https://epoch.ai/data/ai-chip-sales' [online resource]. Accessed 4 Nov 2026.
- Epoch AI, 'Data on AI chip users'. Published online at epoch.ai. Retrieved from 'https://epoch.ai/data/ai-chip-users' [online resource]. Accessed 4 Nov 2026.
- Josh You, John Croxton, Venkat Somala, Yafah Edelman, 'Data on AI companies'. Published online at epoch.ai. Retrieved from 'https://epoch.ai/data/ai-companies' [online resource]. Accessed 4 Nov 2026.
- Epoch AI, 'AI data centers'. Published online at epoch.ai. Retrieved from 'https://epoch.ai/data/ai-data-centers' [online resource]. Accessed 4 Nov 2026.
- Epoch AI, 'Data on AI models'. Published online at epoch.ai. Retrieved from 'https://epoch.ai/data/ai-models' [online resource]. Accessed 4 Nov 2026.
- Epoch AI, 'AI use in math research'. Published online at epoch.ai. Retrieved from 'https://epoch.ai/data/arxiv' [online resource]. Accessed 4 Nov 2026.
- Epoch AI, 'AI use in research'. Published online at epoch.ai. Retrieved from 'https://epoch.ai/data/ai-research-use' [online resource]. Accessed 4 Nov 2026.
- Epoch AI, 'Capabilities & benchmarking'. Published online at epoch.ai. Retrieved from 'https://epoch.ai/benchmarks/use-this-data' [online resource]. Accessed 4 Nov 2026. Benchmark questions and answers are the property of their respective creators; external results keep their original licensing.
- Epoch AI, 'Data on Frontier Lab Hiring'. Published online at epoch.ai. Retrieved from 'https://epoch.ai/data/frontier-lab-hiring' [online resource]. Accessed 4 Nov 2026.
- Epoch AI, 'Data on GPU clusters'. Published online at epoch.ai. Retrieved from 'https://epoch.ai/data/gpu-clusters' [online resource]. Accessed 4 Nov 2026.
- Epoch AI, 'Data on machine learning hardware'. Published online at epoch.ai. Retrieved from 'https://epoch.ai/data/machine-learning-hardware' [online resource]. Accessed 4 Nov 2026.
- Epoch AI, 'Polling on AI usage (July 2026)'. Published online at epoch.ai. Retrieved from 'https://epoch.ai/data/polling' [online resource]. Accessed 4 Nov 2026.

## Tables that mention Anthropic

A pointer for later joins, not a finding. `anthropic_rows` in `inventory.tsv`
counts the data rows in which any cell contains "anthropic" in any letter case.
A row counts once however many cells match. The match is a substring, so it
counts a lab column, a model's developer, a provider category or a source URL
alike. 33 of the 138 parsed CSV tables have no matching row. Counts below are
matching rows / all rows.

- **ai-chip-users:** `intermediates_by_lab.csv` 14 / 74; `year_end_by_lab.csv` 2 / 11.
- **ai-companies:** `ai_companies.csv` 1 / 11; `ai_companies_compute_spend.csv` 8 / 14;
  `ai_companies_funding_rounds.csv` 16 / 49; `ai_companies_revenue_reports.csv` 21 / 72;
  `ai_companies_staff_reports.csv` 13 / 51; `ai_companies_usage_reports.csv` 3 / 51.
- **ai-data-centers:** `data_center_chip_quantities.csv` 16 / 244; `data_center_timelines.csv` 25 / 575;
  `data_centers.csv` 9 / 96.
- **ai-models:** `all_ai_models.csv` 38 / 3,708 (local only); `frontier_ai_models.csv` 3 / 138;
  `large_scale_ai_models.csv` 18 / 534; `notable_ai_models.csv` 27 / 1,092.
- **arxiv:** `math_acknowledgment_trends_monthly.csv` 11,970 / 75,276 (local only).
- **benchmarks, Epoch's own tables:** `model_metadata.csv` 164 / 1,222; `gpqa_diamond.csv` 53 / 333;
  `otis_mock_aime_2024_2025.csv` 56 / 313; `chess_puzzles.csv` 31 / 155;
  `epoch_capabilities_index/eci_scores.csv` 27 / 271; `epoch_capabilities_index/processed_data_for_eci.csv` 1 / 2,859;
  `frontiermath.csv` 27 / 101; `frontiermath_tier_4.csv` 19 / 72; `frontiermath_tier_4_v2.csv` 13 / 78;
  `frontiermath_tiers_1_3_v2.csv` 13 / 122; `frontiermath_erdos.csv` 5 / 14; `mystery_game_puzzles.csv` 21 / 143;
  `simpleqa_verified.csv` 19 / 100; `math_level_5.csv` 16 / 108; `ebr_bench.csv` 11 / 29;
  `furniture_assembly.csv` 10 / 36; `swe_bench_verified.csv` 9 / 35; `mirrorcode.csv` 4 / 15;
  `spireclimb.csv` 3 / 7; `spireclimb_sts1_a20_heart.csv` 3 / 7; `spireclimb_sts2_a10.csv` 3 / 7.
  (`benchmark_metadata.csv` and `epoch_capabilities_index/edi_scores.csv`: 0.)
- **benchmarks, external tables (local only):** 60 of the 67 have matching rows, from 1 to 74;
  the largest are `arc_agi_external.csv` 74 / 312, `arc_agi_2_external.csv` 67 / 290,
  `dtbench_external.csv` 55 / 235, `terminalbench_external.csv` 54 / 204 and `lmca_external.csv` 48 / 197.
  The rest are in `inventory.tsv`.
- **frontier-lab-hiring:** `frontier_lab_hiring_open_roles_by_category.csv` 3,026 / 6,069;
  `frontier_lab_hiring_open_roles_by_city.csv` 3,586 / 12,346; `frontier_lab_hiring_open_roles_by_country.csv` 2,290 / 7,875;
  `frontier_lab_hiring_postings.csv` 1,757 / 4,055; `frontier_lab_hiring_posting_texts.csv` 1,758 / 4,055 (local only);
  `frontier_lab_hiring_revisions.csv` 3,898 / 7,584.
- **polling:** `polling_on_ai_usage_jul_2026.csv` 26 / 3,008; `polling_on_ai_usage_jul_2026_microdata.csv` 1 / 1,103.

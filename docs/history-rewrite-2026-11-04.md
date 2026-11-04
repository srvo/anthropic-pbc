# History rewrite, 2026-11-04

Branch `ec-ai-corpus` was rewritten before its first push, to keep the
repository small (Praxis `PRINCIPLES.md` P1: permacomputing, keep everything as
small as possible; decided by Sloane, 2026-11-04).

## What was removed

Every earlier version of three earnings-call tables that carried full
transcript text: `corpus/earnings-calls/ai-paragraphs.parquet`,
`ai-windows.parquet` and `ai-questions.parquet`. The text came from
Yahoo-sourced transcripts (via the defeatbeta dataset). The repository now
commits ids, character offsets and hashes for these tables, and rebuilds the
text into the gitignored `.eccorpus/` from the pinned source
(`docs/earnings-call-ai-corpus.md` §2a). Quotes stay committed.

Removed blobs (3, 33.5 MB): `7d614c9e60d7`, `a398b70c08d8`, `fd47c7a36fd6`.
Packed repository: 113 MiB before, 82 MiB after (measured on a clean clone). The rest is mostly model-output parquets, Epoch CSVs and Wikipedia article text; see the audit below.

## What did not change

- The tree at the branch tip is identical before and after (`f0b6337`).
- Commits before the first parquet commit keep their hashes. That includes
  everything on `origin/main` (tip `f3358a7`) and edition v0 of the paper
  (`1afb042`).
- Only the three tables' old versions were removed; no other file changed.

## How

`git filter-repo` 2.47.0 (`uvx git-filter-repo==2.47.0`), run in a scratch
clone with `--strip-blobs-with-ids` and `--refs c64b7f3^..ec-ai-corpus`.
Limiting the range matters: the repository's initial commit carries a GitHub
signature, which filter-repo strips, so an unlimited run rewrites every commit.
The branch was then moved with `git update-ref`, guarded on the old tip, so no
working tree or index was touched.

## Old commit hashes

Documents written before the rewrite cite old hashes (for example the review
`docs/review-2026-11-04.md` cites `a83255b`, and Praxis `OPENQUESTIONS.md` cites
`23a4bb6`). Look them up here. Commit messages that named other commits were
rewritten by filter-repo; file contents were not.

| Old | New | Subject |
|---|---|---|
| `c64b7f3` | `b175c3c` | Add S&P 500 earnings-call AI corpus and BERT witness tooling |
| `71db655` | `0abdd1b` | Score earnings-call AI windows with two NLI witnesses on Modal |
| `05b5a9b` | `7646104` | Add exploratory BERTopic map of earnings-call AI windows |
| `04f7dc7` | `78c3cd4` | Document loss-evidence corpus: 13,570 events, 6,187 companies |
| `2df66c7` | `e98613a` | Add AI-as-risk time series, 12-month risk ranking, and verbatim quotes |
| `8ccfaa4` | `48e8ce5` | Add analyst-question intent analysis and human gold-set coder |
| `eb52f4c` | `5f67689` | Add Hacker News Anthropic and AI-security corpus (ids only), scored |
| `c2d8317` | `3cebe58` | Add Wikipedia AI-risk corpus and codebook coverage report |
| `5defccf` | `ac4e145` | Add pinned monthly CVE series with AI-credited counts |
| `e121992` | `34dc07e` | Add corpus roadmap: source policy, codebook v0.2 plan, open-web sources |
| `5005f7c` | `609fb04` | Add pinned snapshot of Epoch AI datasets as of 2026-11-04 |
| `1acf062` | `1ea759d` | Add DATASETS.md catalog (Marp deck) and collaboration-first AGENTS.md |
| `05c2cf1` | `184308e` | AGENTS.md: compute is vendor-agnostic; Modal is one convenience wrapper |
| `9f467ca` | `cb6e4f8` | Add PASTEBIN.md (open dump + ingest procedure) and OPENQUESTIONS.md |
| `4810456` | `1b83ac0` | Add per-dataset signing records and SSH signature check |
| `38e337f` | `e1750c5` | attest_datasets: neutral signer example in help text |
| `e83412f` | `7eea953` | Add OWID-style compute graph (dag.yml) with content-hash staleness |
| `c4f9d2e` | `b3eb28b` | Fix heading guard that rejected every section opening 'In this section' |
| `2b8c78e` | `30d7b0f` | Plan: regroup along OWID URIs with enforced metadata |
| `ef04fa8` | `9adfa88` | Metadata schema and gap validator; CVE metadata complete |
| `edda31f` | `cd62ae8` | dag.py meta: count and show fields declared unknown |
| `e934f04` | `0f93e57` | Score all sources against codebook v0.2 DRAFT; dialogue-space map |
| `e362459` | `fabf0e8` | Enable Entire |
| `29c344d` | `9597bfb` | Fix HN build host-timezone dependence; rebuild HN reports |
| `abd7d21` | `f51717e` | Complete metadata for all 33 steps; fix contradictions it surfaced |
| `7fcf0ef` | `2be7058` | Add health-of-democracy proxies: GDELT timelines and Rooney toplines |
| `a00fd5e` | `6931a64` | Metadata for the three democracy steps: 36/36 complete, 0 gaps |
| `80f27a1` | `6ab20da` | Fix seven democracy doc/code contradictions found by metadata pass |
| `309d25a` | `aad7ed0` | Move dataset tooling, metadata schema and notes to Praxis |
| `265cb60` | `f7cc811` | Add DECK.md: top-level Marp deck of the report in charts |
| `1fe7dff` | `5826ab3` | DECK.md: record the Marp CLI version that renders it |
| `d8287d1` | `c0fb21a` | Plan: build the report as an edition from a source commit |
| `e9405a6` | `c4cd4e4` | Add edition build: DECK.md from a source commit and one risk codebook |
| `57cf9f8` | `4cd33bc` | Edition build: bind the comparison year instead of hard-coding it |
| `443ab0a` | `6608ba5` | Edition build: compute caption shares from counts, as the chart does |
| `c2f33b7` | `a102497` | Edition build: wrap the ranking chart subtitle |
| `a4ad456` | `ff8ca2a` | Edition build: display controls |
| `f5c9c45` | `6e861fa` | Edition build: measure chart text with the Agg renderer |
| `cdee7e2` | `102b7d2` | Test the edition display controls; document them |
| `efbfd48` | `e18d73b` | report-build: record that the build is the review step |
| `23a4bb6` | `ab4972b` | Route every report number through scripts/display.py |
| `a83255b` | `fb63972` | report-build: open questions move to Praxis Q15-Q23; fix stale status |
| `3e82955` | `b8fb01c` | Adversarial review of the repository at fb63972 |
| `5121b5a` | `08b6923` | Wire Entire into every agent: Claude, Codex, Cursor, Droid, OpenCode, pi |
| `ff09880` | `b20f700` | review: buzz-saw pass; correct which finding was re-checked by hand |
| `479b1b9` | `2bb845c` | Attribute hand-written datasets to Sloane Ortell: personal working paper |
| `61ec44d` | `f2a0ba9` | M9: mark built corpora in roadmap; log that spec §7 spike layout is unbuilt |
| `39e2ac3` | `a0707fb` | M8: mark Praxis/Descartes docs as copies; point links to local copies |
| `aadfa60` | `20abc61` | M10: say plainly the risk-factor corpus is unpinned and not rebuildable |
| `5a08fa7` | `a56436f` | Low: drop private vault key name from earnings-call compute table |
| `d634cc3` | `9899797` | M11: verify fails cleanly when bulk data is absent; pin blake3 in hn_extract |
| `effb3e5` | `0199900` | Merge review fixes: docs and hygiene (M8-M11) |
| `d0c62f6` | `c3a6258` | Re-record dataset attestations after attribution and verify-path changes |
| `d4c8c2a` | `c5131d6` | build_edition: source commit is the last commit touching an input (M1) |
| `20f23e7` | `860f691` | build_edition: check numerals against their own bindings, on every channel (M2, M3) |
| `83fdc08` | `b6cd2e0` | build_edition: tighter quote check, q_33k as the paper states it, CVE baseline from its manifest (M4, M6) |
| `60eaf93` | `1ada5dc` | edition: count company speakers only; show the per-passage rate beside the call rate (H1, H2) |
| `b4a3c3c` | `a777437` | edition: intent caption compares group totals; HN-security caption states the selection (M5) |
| `5c6f0bf` | `acf4175` | dialogue space: record each source's window; caption says windows differ and levels compare only in rough order (H4) |
| `0b62ffa` | `ad35171` | edition: alt text for every chart, composed from the chart's registered values (Q23) |
| `3bee692` | `225b01d` | display.score rounds float32 scores from their float32 repr; HN chart shows an undefined rate as a dash (low) |
| `2bcdf9e` | `40cdcf3` | report-build: control test count after the review fixes |
| `b4da6ee` | `db05a68` | Merge review fixes: edition build, controls and captions (H1-H4, M1-M6, Q23) |
| `90df6af` | `7911914` | Edition alt text: write bound percentages as 'per cent' |
| `fff6988` | `7674ed3` | AGENTS.md: permacomputing, keep everything as small as possible |
| `1b6ac7f` | `cb1c1ac` | earnings calls: commit ids, offsets and hashes; text only in .eccorpus/ |
| `aff1412` | `21919f1` | earnings calls: document that text is not committed; quotes are |
| `5a52652` | `cd7ae1f` | Merge earnings corpus to pointers: ids, offsets and hashes; text only in .eccorpus/ |

## Still larger than it needs to be

Found on 2026-11-04 by the same audit; not yet changed:

- `corpus/wikipedia-ai-risk/articles.parquet` (859 KB) and `windows.parquet`
  (1.02 MB) both hold the full prose of 151 articles: the same text twice.
- `proposals/earnings-calls/codebook-v0.1/report/window-flags.tsv`, 5.5 MB of
  ids and flags in TSV.
- Witness parquets in long format with text ids: `proposals/hacker-news/`
  25 MB, `proposals/earnings-calls/` 15 MB.
- `corpus/hacker-news/windows.parquet`, 10 MB, two 64-character hashes per
  row.
- `corpus/epoch/`, 18 MB of whole third-party CSVs, kept because the saved bytes
  are the pin.

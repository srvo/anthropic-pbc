# AGENTS.md

Public research repository: a hash-sealed working paper on Anthropic PBC, plus
public-data corpora that test its method across the S&P 500. Everything here is
published, so proprietary Ethical Capital work belongs in monocloud, never here.
Repo content is CC0 except `corpus/*/`, which carries its own attribution README.

## Where to look

- **Editing the paper** (`docs/anthropic-contrapunctus.md`): every hash pin moves
  with it. Run `uv run scripts/seal.py check --allow-unsealed`; README "Maintaining the seal".
- **Any model output** (BERT, NLI, embeddings, topics): read
  `docs/bert-enrichment-spec.md` §5 and §9 first. Models are *witnesses* whose
  output is a proposal in `proposals/`, never a verdict. Results are appended to
  that spec's §10 log, never edited into §§1–9.
- **Earnings-call AI corpus**: `docs/earnings-call-ai-corpus.md` (method, unit,
  rebuild order). Data is in `corpus/earnings-calls/`.
- **10-K Item 1A risk-factor corpus**: `docs/risk-factor-corpus.md`.
- **Other corpora**, each with a method doc in `docs/`:
  - Hacker News: `hacker-news-corpus.md`. It stores ids only and never commits
    comment text or usernames.
  - Wikipedia AI-risk articles: `wikipedia-ai-risk-corpus.md`.
  - CVE monthly series: `cve-series.md`.
- **Adding a source**: take broad, verifiable, normalisable data, such as
  Epoch AI datasets, over hand-picked sensational sources. Hacker News is the
  only social forum.

## Compute

GPU work goes to **Modal**. It is authenticated through the local `modal`
profile via `uvx`, with no venv and no BWS secret:

    uvx --with duckdb==2.0.0 --with blake3 modal run scripts/ec_classify_modal.py --model deberta

Measured speeds, costs and alternatives (Mac MPS, RunPod via BWS
`RUNPOD_API_KEY`, CPU-only k3s on the Proxmox cluster) are in
`docs/earnings-call-ai-corpus.md` §9. Copy the `ec_classify_modal.py` pattern
for new GPU jobs: shared scoring functions in the local script, imported by the
Modal class.

## Conventions

- **Deterministic.** No clock, host or random id enters any output; time is a
  recorded argument. A rebuild must be byte-identical, so check that by
  re-hashing.
- **Verbatim and anchored.** Stored text carries BLAKE3 and character offsets,
  and a `verify` command re-slices and re-hashes everything.
- **Pinned.** Scripts are `uv run` PEP 723 scripts with exact versions. Sources
  are pinned by revision and hash in a `MANIFEST.tsv`, and bulk bytes live in a
  gitignored dot-directory (`.eccorpus/`, `.rfcorpus/`) that the manifest can
  re-fetch.
- **Denominators.** Report a rate against every unit attempted (for example
  `calls.tsv`), and report coverage beside every finding.

## Gotchas

- `scripts/ec_classify_modal.py` must not use `from __future__ import annotations`:
  Modal reads `modal.parameter()` types at runtime.
- Modal methods return only plain Python types: the local side has no torch,
  so a torch object or exception (even `torch.__version__`) fails to unpickle
  after the GPU work is done. Shards are saved as they arrive, so rerunning
  only merges.
- Shards are tagged by model, dtype and backend, so runs on different hardware
  never merge, by design. To combine workers, pass the same `--backend`.

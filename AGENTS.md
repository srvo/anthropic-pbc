# AGENTS.md

Public research repository: a hash-sealed working paper on Anthropic PBC, plus
public-data corpora that test its method. **It exists to be worked on by
others.** A researcher or agent who has never seen it should be able to clone
it, rebuild every dataset, check every number, and add to it, with no access
to anything private. Every convention below serves that.

Everything here is published, so proprietary Ethical Capital work belongs in
monocloud, never here. Repo content is CC0 except `corpus/*/`, which carries
its own attribution README.

## Start here

- **`DATASETS.md`** is the catalog of every corpus: source, license, pin date,
  how often the source changes, refresh commands, and witness runs. It is a
  Marp deck generated from `corpus/datasets.tsv` and each corpus's
  `MANIFEST.tsv` by `uv run scripts/datasets_md.py`. Never edit it by hand.
- **`docs/corpus-roadmap.md`** lists what is planned and what is open. Pick up
  work there.

## Collaborating

- **Leave the work rebuildable by a stranger.** Every result traces to a
  committed script, a pinned source and a hash. A step that only works on one
  machine or with one person's credentials is unfinished.
- **Commit each piece as soon as it is complete and verified**: rebuild
  byte-identical, `verify` passes. Small commits, one corpus or one result each.
- **Keep to your own files.** Others work in this tree at the same time. Stage
  only your own paths and hunks; never stage `__pycache__/` or `.claude/`.
- **Disagree in the open.** A finding is changed by appending to the spec's
  §10 log, never by rewriting earlier entries. Codebooks change only by human
  review: a draft is marked `DRAFT` until approved.
- **Gold labels come from people.** `scripts/ec_gold.py code --coder NAME`
  records the coder's name on every row. A second coder works on a copy of the
  sample (`--sample PATH`) so that both codings survive and agreement can be
  measured. No LLM labels (spec §9).
- **Write for the next reader.** The method doc for each corpus says what it
  does *not* answer, as plainly as what it does.

## Adding a dataset

1. Choose broad, verifiable, normalisable data, such as Epoch AI datasets, over
   hand-picked sensational sources. Hacker News is the only social forum.
2. Write `scripts/<name>.py` with `pin` (or `fetch`), `build` and `verify`, and
   pin the source in `corpus/<name>/MANIFEST.tsv` (URL, bytes, SHA-256, BLAKE3).
3. Write `corpus/<name>/README.md` (files and attribution) and
   `docs/<name>.md` (method and limits).
4. Respect source terms. A dataset whose terms bar AI ingestion is not
   fetched. Private individuals' text is stored as ids and hashes only (see the
   Hacker News corpus).
5. Add a row to `corpus/datasets.tsv`, run `uv run scripts/datasets_md.py`, and
   commit the deck with the data. `uv run scripts/datasets_md.py check` fails
   if the deck is stale.

## Where to look

- **Editing the paper** (`docs/anthropic-contrapunctus.md`): every hash pin moves
  with it. Run `uv run scripts/seal.py check --allow-unsealed`; README "Maintaining the seal".
- **Any model output** (BERT, NLI, embeddings, topics): read
  `docs/bert-enrichment-spec.md` §5 and §9 first. Models are *witnesses* whose
  output is a proposal in `proposals/`, never a verdict. Results are appended to
  that spec's §10 log, never edited into §§1–9.
- **Per-corpus method**: one doc per corpus in `docs/`, linked from `DATASETS.md`.

## Compute

**Compute is vendor-agnostic.** The scoring lives in `scripts/ec_classify.py`,
which runs on any machine: CUDA, Apple MPS or CPU. It can split the shards
across several machines (`--workers N --worker i`, then `--merge-only`).
Results are the same wherever they run, up to the documented bfloat16/float32
tolerance. Every run records its device, GPU, library versions and backend
tag, and runs from different hardware never merge silently.

Remote GPU wrappers are conveniences on top of that script, never
requirements. The maintainer uses Modal (`scripts/ec_classify_modal.py`,
through the local `modal` profile via `uvx`):

    uvx --with duckdb==2.0.0 --with blake3 modal run scripts/ec_classify_modal.py --model deberta

A wrapper for another provider (RunPod, a university cluster, k3s) follows the
same pattern. It imports `ec_classify`'s scoring functions, adds no logic of
its own, and tags its shards with its own `--backend`. Measured speeds and
costs are in `docs/earnings-call-ai-corpus.md` §9. To score another corpus or
codebook, pass `--units`, `--codebook`, `--id-col` and `--out`.

## Conventions

- **Deterministic.** No clock, host or random id enters any output; time is a
  recorded argument. A rebuild must be byte-identical, so check that by
  re-hashing.
- **Verbatim and anchored.** Stored text carries BLAKE3 and character offsets,
  and a `verify` command re-slices and re-hashes everything.
- **Pinned.** Scripts are `uv run` PEP 723 scripts with exact versions. Sources
  are pinned by revision and hash in a `MANIFEST.tsv`, and bulk bytes live in a
  gitignored dot-directory (`.eccorpus/`, `.hncorpus/`, ...) that the manifest
  can re-fetch. Where a source cannot be re-fetched byte-identically (Epoch
  bundles, API responses), the saved bytes are the pin.
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
- Without `--out`, the classifier writes to `proposals/earnings-calls/<codebook stem>/`,
  which would overwrite earnings-call results when another corpus reuses a codebook.

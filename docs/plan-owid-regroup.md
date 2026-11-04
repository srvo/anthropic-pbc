# Plan: regroup by the compute graph, with strict metadata

Status: PLAN · 2026-11-04. Requested by Sloane: regroup the repository along
OWID's ETL design (https://docs.owid.io/projects/etl/architecture/design/compute-graph/)
and be "ultra, ultra rigorous" about metadata.

## Goal

1. Every step in `dag.yml` lives at a path derived from its URI.
2. Every step carries complete metadata, and a missing field fails the build.

A reader holding any file can tell, from the file alone, what it is, where it
came from, how it was made, what each column means, and under what license.

## 1. Layout

OWID derives paths from URIs. We do the same:

| URI | Committed path | Bulk bytes (gitignored) |
|---|---|---|
| `snapshot://ns/version/name` | `snapshots/ns/version/name.meta.yml` and the MANIFEST | `.snapshots/ns/version/name/` |
| `data://meadow/ns/version/name` | `data/meadow/ns/version/name/` | `.data/meadow/...` for local-only text |
| `data://garden/ns/version/name` | `data/garden/ns/version/name/` | |
| `data://witness/ns/version/name` | `data/witness/ns/version/name/` (was `proposals/`) | shards |
| `data://gold/ns/version/name` | `data/gold/ns/version/name/` (was `gold/`) | |

`gold` is a new channel: human labels. It is never written by a model.

What changes:
- `corpus/`, `proposals/` and `gold/` are replaced.
- The dot-directories (`.eccorpus/`, `.hncorpus/`, ...) collapse into
  `.snapshots/` and `.data/`.

What stays:
- Scripts stay in `scripts/` and are named by `cmd` in each step. Splitting
  them per step, as OWID's `etl/steps/` does, can come later; it buys little
  while one script builds several steps.
- `docs/` stays as it is.
- The paper, `index.html`, and the seal and its hash pins are untouched; none
  of them reference these paths.

A compatibility note in each old folder's README points to the new path for
one release.

## 2. Metadata: required fields, enforced

The schema follows OWID's metadata reference (origin → dataset → table →
indicator) and adds fields this repository needs: hashes, witness status, and
what a dataset does not answer.

**Snapshot origin** (`<name>.meta.yml`). Every field is required, or `null`
with a `reason:`.
- `producer`, `title`, `description`
- `citation_full`, `attribution_short`
- `url_main`, `url_download`
- `date_published`, `date_accessed`, `version_producer`
- `license: {name, url}`, `terms_notes`: for example, YouGov's no-AI-ingestion
  notice, or third-party benchmark tables that keep their own licences
- `files`: path, bytes, SHA-256, BLAKE3. This absorbs the MANIFEST.
- `refetch`: `exact` | `saved_bytes_are_pin`, with the reason
- `personal_data`: `none` | `ids_only` | `verbatim_public_figures` | ...

**Dataset** (`<name>.meta.yml` beside the outputs):
- `title`, `description`, `channel`, `uri`
- `origins`: the snapshot URIs, resolved transitively
- `processing`: what the step does, in plain sentences, and what it drops
- `unit_of_analysis`, `denominator`: which file holds it
- `coverage`: dates, universe, known gaps
- `does_not_answer`: required; it may not be empty
- `license`: derived from the origins, the most restrictive wins
- `status`: held | witness | gold
- for `witness`: `model`, `revision`, `codebook`, and `proposal_only: true`

**Table** (one entry per output file):
- `title`, `description`, `primary_key`, `rows`
- `columns`, one entry for **every** column:
  - `title`, `description`, `type`, `unit`
  - for verbatim text: `verbatim: true`
  - for a hash column: `hash_of`
  - for a code column: `values`

**Enforcement** (`uv run scripts/dag.py check`). It fails when:
- a required field is missing or empty;
- a column in the file is not documented, or a documented column is not in the
  file;
- a hash in the metadata does not match the file;
- a `witness` dataset lacks `proposal_only: true`, or a non-witness step depends
  on a witness step without being marked a proposal;
- a license is weaker than an origin's.

Row counts and hashes are written by the build, never by hand. Descriptions
are written by hand and reviewed like code.

`DATASETS.md` renders all of this, so the deck becomes the human view of the
metadata.

## 3. Phases (one commit each, each verified)

1. **Schema and validator.** Write `schema/metadata.schema.yml`. Add checks to
   `dag.py check` that report missing metadata without failing yet, so we can
   see the gap.
2. **Metadata backfill.** One dataset per commit, starting with CVE and Epoch
   (smallest), then Wikipedia, Hacker News and the earnings calls. Columns are
   introspected from the files; descriptions are written and checked against
   the method docs.
3. **Regroup.** Wait until the v0.2 scoring and the democracy work have landed.
   Then `git mv` everything to the URI paths, in one commit per dataset:
   - update script constants and the graph's outputs;
   - rebuild, check byte-identical, `verify`, `dag.py lock`, re-record the
     attestations.
4. **Strict.** Flip `check` to fail on any gap, and add it to the
   collaboration rules in AGENTS.md.
5. **Signing.** Sloane signs once the layout is final. Signatures taken before
   the regroup would go stale on the move.

## Open decisions (also in OPENQUESTIONS.md)

- Whether `snapshots/` keeps a TSV MANIFEST beside the YAML for grep-ability
  (proposed: yes, generated from the YAML).
- Whether scripts split into per-step files now or later (proposed: later).

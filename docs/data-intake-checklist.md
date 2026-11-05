# Data intake checklist

A dataset enters this repository once and stays: anyone can rebuild it, check
it and cite it without asking us. Nothing is "in" until every box below is
ticked. A dataset that fails a box stays out, or goes in labelled as a lead.

## Before it lands

- [ ] **Source named.** Producer, title and the URL a stranger would fetch.
- [ ] **Licence read.** The terms allow redistribution of what we commit; anything
      they forbid (e.g. YouGov's AI-ingestion ban) is left out and the gap is noted.
- [ ] **Personal data judged.** `personal_data:` set in the metadata
      (`none`, `verbatim_public_text`, ...). No private individual is profiled.
- [ ] **Re-fetch class decided.** `refetch: exact` (same bytes again) or
      `refetch: snapshot` (the source changes; our copy is the record), with the reason.

## When it lands

- [ ] **Pinned in a manifest.** One row per file in `corpus/<id>/MANIFEST.tsv`
      (or `sources/MANIFEST.tsv` for a primary source): url, pinned date, bytes,
      sha256, blake3.
- [ ] **Metadata written.** `<step>.meta.yml` per `praxis/datasets/metadata.schema.yml`:
      citation, accessed date, licence, refetch, personal data.
- [ ] **A step in the graph.** A `dag.yml` node with its URI
      (`snapshot://`, `data://meadow|garden|witness/`, `viz://`), inputs,
      outputs and the exact `cmd`; `dag.lock.tsv` updated by the build, never by hand.
- [ ] **Bulk bytes handled.** Small derived files are committed. Large or
      licence-bound bytes go in a gitignored `.<id>corpus/` and are re-fetched from
      the manifest pin. No dataset lives only on one machine (the 10-K risk-factor
      corpus currently fails this).
- [ ] **Registered.** A row in `corpus/datasets.tsv` and a section in `DATASETS.md`.
- [ ] **Rebuilds twice, identically.** Running the step twice from the pins gives
      the same output hashes.

## After it lands

- [ ] **Model output marked.** Anything a model produced is a `witness` step and a
      proposal until a person checks a gold sample (`gold/`), with agreement reported.
- [ ] **Linked to the argument, or labelled as background.** Either a card rests on a
      quote from it, or the trace page lists it as background with what it would feed.
- [ ] **Cadence recorded.** How often the source changes and how we refresh
      (`source_cadence`, `refresh` in `corpus/datasets.tsv`).

## Web search leads are not data

Results from the query queue (`scripts/query_queue.py`) are **leads**. They live in
`research/leads.tsv` with the query that found them. A lead becomes evidence only
when its source is pinned under this checklist and a quote from it passes the
Descartes byte check.

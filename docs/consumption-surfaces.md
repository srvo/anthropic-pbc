# How this report gets consumed

A working paper is read, but it is also fetched, parsed, quoted and re-used. This
records the surfaces by which that happens, what each one needs, and what is
actually in place today versus proposed.

**Status of this document:** enumeration and proposal. Nothing here is
implemented beyond what the "today" column says. Measured 2026-11-07.

The governing constraint is Praxis P1 (permacomputing): a surface that needs a
build system, a framework or a network font to work is not finished. Every
surface below is designed to be a static file, a plain response, or a few lines of
generated JSON.

---

## The consumers

Five kinds of reader, and they want genuinely different things. Naming them
separately matters because a surface good for one is often bad for another.

| Consumer | Wants | Cares about | Will not do |
| --- | --- | --- | --- |
| **A person reading** | The argument, in order, with figures | Legibility, contrast, print, mobile | Tolerate a 20MB page |
| **An LLM agent** | Exact text, in chunks, with provenance | Stable ids, no boilerplate, unambiguous quotes | Execute JavaScript |
| **A search engine** | One canonical URL, description, structured metadata | `robots.txt`, sitemap, `ld+json`, stable titles | Index what is blocked |
| **A researcher / replicator** | Datasets, manifests, claims, rebuild commands | Pins, hashes, licences, determinism | Accept a PDF as evidence |
| **A skeptic / disputant** | A specific claim and the evidence under it | A way to disagree attributable to them | Read 100k words to find the point |

---

## 1 · curl — the report as a response

**Today:** partially works, and accidentally.

| URL | Status | Note |
| --- | --- | --- |
| `raw.githubusercontent.com/.../docs/anthropic-contrapunctus.md` | **200**, `text/plain`, byte-identical to local (106,829 B) | The paper is already curl-able |
| `raw.githubusercontent.com/.../CITATION.cff` | **200** | Citation metadata |
| `srvo.github.io/anthropic-pbc/docs/anthropic-contrapunctus.md` | **404** | GitHub Pages does not serve `.md` |
| `srvo.github.io/anthropic-pbc/argument.json` | **404** | Not on `main` yet |

So curl works **only if you know to use `raw.githubusercontent.com`**, which is an
implementation detail of GitHub, not something this product promises. A reader who
curls the site's own domain gets a 404.

**Proposed:**

- Serve the paper's markdown from the published origin: either enable Jekyll's
  passthrough for `docs/**`, or copy the `.md` into the site root at seal time.
  The plan says emitted files are rebuilt, so this belongs in `scripts/seal.py`.
- A stable, documented entry point: `srvo.github.io/anthropic-pbc/paper.md`,
  `.../paper.txt`, `.../metadata.json`.
- `curl -s .../paper.md | wc -w` should be the obvious way to ask "how long is it"
  — and should match the word count the page claims.
- Set `Content-Type` deliberately. `text/plain` for `.md`/`.txt` so a browser
  displays rather than downloads; `application/json` for data.
- No `Content-Encoding` surprises and no cookie walls. A curl of any surface must
  return the same bytes as the committed file — that is checkable and worth testing.

**What stays true:** the markdown is the canonical source. The HTML is rendered
from it. A curl consumer never needs to parse the HTML.

---

## 2 · LLM agents — the report as retrievable text

**Today:** nothing purpose-built. An agent can fetch the markdown and read 106KB,
but there is no chunk boundary, no stable fragment ids, and no machine-readable
statement of what the paper does and does not claim.

The specific hazards for an agent reading this paper:

- **Verdict vocabulary is load-bearing.** CONFIRMED / REFUTED / MISLEADING /
  NUANCED / UNVERIFIED mean specific things here. An agent that reads
  "MISLEADING" as a generic negative will misreport the paper.
- **Every claim has a limit.** The paper pairs benefit claims with evidence limits
  and harm claims with attribution limits. An agent quoting the claim without the
  limit inverts the argument.
- **Model output is a proposal, not a finding.** Sections built on witness
  (BERT-family) output are circle-3 evidence. Quoting them as findings is wrong.
- **Five premises are unsupported.** `argument.json` says so. An agent summarising
  the thesis as accepted would be wrong in a way the repository already knows.

**Proposed:**

- **`llms.txt`** at the site root: the paper's own summary of itself, what it
  claims, what it does not, and where the machine-readable pieces are. Short,
  plain, and honest about the five unsupported premises.
- **Sectioned markdown with stable anchors.** One file per §0–§9 plus appendices,
  each starting with a fixed heading id, so an agent can fetch a section rather
  than the whole paper. Generated from the canonical `.md` at seal time, never
  hand-split.
- **`argument.json`** is already agent-shaped: premises, `rests_on`, evidence with
  quote text and source path, `fails`, `unsupported`. Serving it from the site
  makes the argument's structure fetchable without parsing prose.
- **A claims endpoint.** `claims/anthropic-contrapunctus.tsv` exposes 112 rows of
  label → source → exact quote. As JSON, an agent can verify a quotation it is
  about to repeat instead of trusting its memory of the paper.
- **The limits travel with the claims.** Any agent-facing artifact carries
  `status: proposal` and the unsupported-premise list. An artifact that omits them
  is a bug, not a simplification.

**What to avoid:** a hand-maintained "LLM summary" that drifts from the paper. It
must be generated, and `check` must fail when it is stale — the same discipline as
`argument.json` and the seal.

---

## 3 · Search engines — the report as an indexable page

**Today:** nothing.

- No `robots.txt`, no `sitemap.xml`.
- No `<meta name="description">`, no Open Graph or Twitter card tags.
- No `application/ld+json` structured data.
- `<title>` is "Anthropic PBC" — accurate but says nothing about the question the
  paper answers.
- The page is a single long HTML document with an inline copy of the paper; there
  is no per-section URL to rank or link to.

**Proposed:**

- **`robots.txt`** allowing the paper and corpora, with an explicit decision
  recorded about the corpora (some third-party licences constrain re-use; that is a
  licence question, not a crawler question, and should say so).
- **`sitemap.xml`** listing the paper, the datasets deck, and each section anchor.
- **`<meta name="description">`** — one sentence, the paper's own framing.
- **Open Graph / Twitter card**, so a shared link previews with the actual claim
  rather than a bare title. One static OG image, generated, under the size budget.
- **`application/ld+json`**: `ScholarlyArticle` with `author`, `datePublished`,
  `identifier` (the DOI), `license` (CC0), `citation`, and `isBasedOn` for the
  pinned primary sources. This is the machine-readable version of what
  `CITATION.cff` already says in YAML.
- **Per-section anchors** so §4.1 is linkable and rankable on its own.
- **Stable canonical URLs.** An edition is immutable and DOI-pinned; the site
  should say which edition a URL resolves to, and `rel="canonical"` should not
  drift when later work lands.

---

## 4 · The researcher — the report as a rebuildable package

**Today:** this is the strongest surface, and the one the repo was built around.

- `sources/MANIFEST.tsv` — URL, bytes, SHA-256, BLAKE3 per source.
- `corpus/*/MANIFEST.tsv` — nine corpora, each pinned.
- `dag.yml` — the compute graph, with `snapshot://` and `data://` URIs.
- `claims/anthropic-contrapunctus.tsv` — 112 rows, byte-anchored quotations.
- `DATASETS.md` — generated catalog with licences and refresh commands.
- `CITATION.cff` and `.zenodo.json` — citation metadata with a DOI.
- `scripts/seal.py` — the paper, page, figures and hash pins kept in lockstep.

**Gaps:** the rebuild is documented for someone who knows the repo, not for a
stranger. `uv run ../praxis/datasets/dag.py` assumes a sibling checkout that a
reader does not have.

**Proposed:**

- A single **`REPRODUCE.md`**: clone, check out Praxis beside it, run one command,
  get the same hashes. Explicit about what needs network and what does not.
- A **`checksums.txt`** at the site root so a downloaded copy can be verified
  without cloning.
- State plainly which steps are deterministic and which are witness steps whose
  output varies by hardware (the bf16 note in `dag.yml` already says this; a
  reader should not have to find it).

---

## 5 · The disputant — the report as a thing to disagree with

**Today:** `docs/contrapunctus-attest.md` describes a signed endorsement/dispute
protocol. The edit plane files gaps as GitHub issues (gated — see below).

**Proposed:** the granularity the edit plane already has — whole argument,
premise, quotation — should be reachable from the published page, not only from a
notebook a reader has to run. A skeptic should be able to land on §4.1, see claim
Q094 and its exact quote, and disagree with *that*, attributed.

---

## What this document does not decide

- **Whether the corpora are crawlable.** That is a licence question per corpus;
  several carry ODC-BY or CC BY-SA attribution terms.
- **Whether a public issue surface is opened.** The Dark plan has
  `policy-public-item-flagging-20261106` and `arch-public-contributor-surface-20261106`
  open, which gate exactly that. Deferred by the owner, 2026-11-07.
- **Which agent-facing artifacts are worth building first.** `llms.txt` and served
  `argument.json` are the cheapest; sectioned markdown is the most useful to an
  agent and the most work to keep generated correctly.

## Sequencing, cheapest first

1. `robots.txt` + `sitemap.xml` — static files, no generation, immediate.
2. `<meta name="description">`, OG/Twitter, `<title>` that names the question.
3. Serve `paper.md` from the site origin; verify curl parity with a test.
4. Serve `argument.json` and a claims JSON; `llms.txt` generated from the paper.
5. `ld+json` regardless — it is static and validates.
6. Sectioned markdown, generated at seal time.
7. `REPRODUCE.md` and `checksums.txt`.

# Corpus roadmap

Planned sources and open questions for the public-data corpora. The built
corpora are listed first; everything after "Planned" is not built.

## Built

Each of these has a method doc, `dag.yml` steps and a pinned `MANIFEST.tsv`.
`DATASETS.md` is the full catalog.

| Corpus | Method doc | Data |
|---|---|---|
| S&P 500 earnings calls | [`earnings-call-ai-corpus.md`](earnings-call-ai-corpus.md) | `corpus/earnings-calls/` |
| Hacker News | [`hacker-news-corpus.md`](hacker-news-corpus.md) | `corpus/hacker-news/` |
| Wikipedia AI-risk articles | [`wikipedia-ai-risk-corpus.md`](wikipedia-ai-risk-corpus.md) | `corpus/wikipedia-ai-risk/` |
| Monthly CVE series | [`cve-series.md`](cve-series.md) | `corpus/cve/` |
| Epoch AI datasets snapshot | [`corpus/epoch/README.md`](../corpus/epoch/README.md) | `corpus/epoch/` |
| Health-of-democracy proxies | [`democracy-proxies.md`](democracy-proxies.md) | `corpus/democracy/` |

Not rebuildable yet: the 10-K risk-factor corpus
([`risk-factor-corpus.md`](risk-factor-corpus.md)) has a method doc and
scripts but no `dag.yml` step and no `MANIFEST.tsv`; its store is local only.

## Source policy (Sloane, 2026-11-04)

- **Take everything, not the loudest.** Grab as much verifiable data as
  possible so the corpus is broad and normalisable. Do not index the most
  sensationalist sources: they are hard to normalise and invite cherry-picking.
- **One social forum.** Hacker News
  ([`hacker-news-corpus.md`](hacker-news-corpus.md)) is the social voice. No
  other social media.
- **Prefer structured research datasets.** Epoch AI (epoch.ai/data, CC BY) is
  the model; its CVE series is rebuilt in [`cve-series.md`](cve-series.md), and
  every other public Epoch dataset is pinned in `corpus/epoch/` (built).
- Every source is pinned (MANIFEST plus hashes), with coverage and
  denominators reported beside any finding.

## Codebook

`corpus/codebooks/codebook-v0.2-draft.tsv` keeps the 16 v0.1 hypotheses
unchanged and adds 14. Each new one cites the Wikipedia heading and revision
it came from (`corpus/wikipedia-ai-risk/dimensions-candidate.tsv`). It is a
draft until Sloane approves the wording. Motive: scoring Wikipedia with v0.1
left 51% of its AI-risk passages with no specific type
([`wikipedia-ai-risk-corpus.md`](wikipedia-ai-risk-corpus.md)).

## Planned

### Open question: what have AI agents and scraping done to the open web?

Wikipedia names this dimension ("Ethics of artificial intelligence",
Challenges > Strain on open knowledge platforms; v0.2 hypothesis `open_web`).
These candidate sources are broad and measurable, and each must be checked for
license and pinnability before use:

- **Wikimedia**: pageview and bandwidth statistics by agent type (user,
  spider, automated), and Wikimedia's own reports on crawler load.
- **Stack Exchange**: question and answer volume by month, from the data dump
  or the Data Explorer. It is the standard proxy for Q&A sites displaced by
  chat assistants.
- **robots.txt and terms of service restricting AI crawlers**: the Data
  Provenance Initiative's longitudinal audit of web-domain consent, and
  Common Crawl's robots.txt captures.
- **Crawler-to-referral ratios by AI operator**, from Cloudflare Radar
  (check its license terms).
- **Voidly** (voidly.ai): CC BY 4.0 incident records of internet censorship
  (shutdowns, blocking, throttling), with evidence chains and confidence
  scores. This bears on the health-of-democracy thread more than on scraping.
  It is a single small vendor whose incidents are ML-classified, so treat it as
  one witness, not ground truth.

### Health of democracy: beyond the built proxies

Built: GDELT phrase timelines and Rooney Institute survey toplines
([`democracy-proxies.md`](democracy-proxies.md), `corpus/democracy/`). Still
planned: the Trust Project and the BCG Trust Index, for which only feasibility
notes exist (in `democracy-proxies.md`). None of these measures Anthropic's
effect on democracy; they measure attention and conditions.

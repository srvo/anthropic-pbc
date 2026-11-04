# Corpus roadmap

Planned sources and open questions for the public-data corpora. Nothing here is
built yet unless it links to a method doc.

## Source policy (Sloane, 2026-11-04)

- **Take everything, not the loudest.** Grab as much verifiable data as
  possible so the corpus is broad and normalisable. Do not index the most
  sensationalist sources: they are hard to normalise and invite cherry-picking.
- **One social forum.** Hacker News
  ([`hacker-news-corpus.md`](hacker-news-corpus.md)) is the social voice. No
  other social media.
- **Prefer structured research datasets.** Epoch AI (epoch.ai/data, CC BY) is
  the model; its CVE series is already rebuilt in [`cve-series.md`](cve-series.md).
  A snapshot of every Epoch dataset is in progress in `corpus/epoch/`.
- Every source is pinned (MANIFEST plus hashes), with coverage and
  denominators reported beside any finding.

## Codebook

`corpus/codebooks/codebook-v0.2-draft.tsv` keeps the 16 v0.1 hypotheses
unchanged and adds 14. Each new one cites the Wikipedia heading and revision
it came from (`corpus/wikipedia-ai-risk/dimensions-candidate.tsv`). It is a
draft until Sloane approves the wording. Motive: scoring Wikipedia with v0.1
left 51% of its AI-risk passages with no specific type
([`wikipedia-ai-risk-corpus.md`](wikipedia-ai-risk-corpus.md)).

## Open question: what have AI agents and scraping done to the open web?

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

## Health of democracy

In progress: GDELT phrase timelines, Rooney Institute survey toplines, and
feasibility notes on the Trust Project and the BCG Trust Index (`docs/democracy-proxies.md`
when it lands). None of these measures Anthropic's effect on democracy; they
measure attention and conditions.

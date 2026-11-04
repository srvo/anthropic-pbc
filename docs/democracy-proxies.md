# Democracy proxies: method, limits and feasibility

### Attention to democracy and stated democratic attitudes, with Anthropic as a test case

**Status: METHOD and DATA. Binds nothing.** These series measure two things:
how much news and television *talk about* the health of democracy, and what
American survey respondents *say* about democratic norms. **None of them
measures Anthropic's effect on democracy, positive or negative.** A rise or fall
in any series here says nothing about Anthropic. An Anthropic co-mention count
says only that the company's name appeared near the words.

The paper's claim to be tested is that Anthropic is positively involved with the
health of democracy. These proxies are the denominator for that test, the
background against which any Anthropic-specific evidence would have to stand
out. They are not evidence for the claim.

Version: v0.1 · 2026-11-04 · `scripts/democracy_proxies.py` · data in
[`corpus/democracy/`](../corpus/democracy/README.md).

---

## 1. What each proxy measures

| Proxy | Measures | Unit | Does not measure |
|---|---|---|---|
| GDELT DOC 2.0 phrase timelines | Share of online news articles GDELT monitors that contain a phrase | % of monitored articles per day; raw article count, plus GDELT's daily total | Whether democracy is healthy; the stance of the article; anything about articles GDELT does not monitor |
| GDELT TV 2.0 phrase timelines | Share of national-network caption airtime that contains a phrase | % of monitored 15-second caption clips per month; raw clip count | Same; also caption errors and the stations the Internet Archive records |
| Rooney Report toplines | Percent of US respondents, usually by party, agreeing with a stated democratic-norm item | Percent as printed in report text | Trends the reports do not print; anything about AI or technology companies (not asked; see §4) |

## 2. GDELT phrase timelines

### 2.1 Queries

Every query runs against both APIs, with the longest span each allows, ending at
the as-of date (2026-11-04).

| query_id | DOC 2.0 (online news) | TV 2.0 (`market:"National"`) |
|---|---|---|
| `hod` | `"health of democracy"` | `"health of democracy"` |
| `anthropic_hod` | `anthropic "health of democracy"`: both in one article | the same, in one 15-second clip |
| `anthropic_near20_democracy` / `anthropic_democracy_clip` | `near20:"anthropic democracy"`: the two words within 20 words | `anthropic democracy`: both in one 15-second clip |
| `claude_near20_democracy` / `claude_democracy_clip` | `near20:"claude democracy"` | `claude democracy` in one clip |
| `democracy` (control) | `democracy` | `democracy` |
| `anthropic` (control) | `anthropic` | `anthropic` |

Query semantics, from GDELT's documentation. DOC 2.0 ANDs terms within an article,
and `nearN:` requires the words within N words. TV 2.0 ANDs terms within a
single 15-second caption clip: "By default all of your keywords/phrases must
appear in a single 15 second clip" (GDELT TV 2.0 API announcement,
https://blog.gdeltproject.org/gdelt-2-0-television-api-debuts/). A clip is
already a proximity window of about 40 spoken words, so the TV co-mention
queries are proximity queries without an operator. `context:` (the clip plus the
clips on either side) was not used.

Modes. DOC: `timelinevol` (percent of all monitored articles) and
`timelinevolraw` (article count, with `norm` = all articles monitored that day).
TV: `timelinevol` with `datacomb=combined` (all national stations as one
series), once as the default percent of monitored airtime, and once with
`datanorm=raw` (clip counts). GDELT defines the TV percent as the matching clips
divided "by the total number of all monitored clips from that station or set of
stations over that time interval".

**Use the normalized share for comparisons over time.** GDELT's monitored
volume changes from day to day, which is what the DOC `norm` column records.
Raw counts are kept beside the share so that small-number series can be read
honestly, where one article is the difference between zero and a spike. (On
2026-11-04 the DOC raw responses could not be pinned; see §2.2.)

### 2.2 Results

**Coverage (denominator first).** 24 requests were planned: 6 queries × 2
modes × 2 APIs. **17 were pinned.** All 12 TV responses and 5 DOC
`timelinevol` responses were received. **The DOC `democracy` control and all 6
DOC `timelinevolraw` responses were not received**: GDELT's DOC API returned
HTTP 429 (rate limit) through repeated, spaced attempts on 2026-11-04, and we
stopped rather than keep hitting it. They are listed as `NOT PINNED` in
`gdelt-summary.tsv`. `fetch-gdelt` resumes where it stopped, but a later fetch
is a later observation (§2.3). Consequence: **no DOC raw article counts and no
DOC daily totals**, so DOC co-mentions below are shares and day counts, not
article counts.

- DOC: daily, 2017-01-01 to 2026-11-03. The API returned 3,547 days. The rest of
  the span is missing from GDELT's response (for example 2025 has 348 days and
  2026 has 281 of 307), not zero.
- TV: monthly, 2009-07 to **2024-10**, 184 months, national stations combined.
  Nothing after October 2024 is returned (§2.3).
- A TV response of `{}` (2 bytes) means no matching clip in the whole span.

**"Health of democracy" as a topic.**

| | DOC: mean daily share of articles | TV: national caption clips (share of airtime) |
|---|---|---|
| 2017 | 0.00099% | 1 |
| 2018 | 0.00150% | 15 |
| 2019 | 0.00169% | 5 |
| 2020 | 0.00174% | 13 |
| 2021 | 0.00228% | 20 |
| 2022 | **0.00307%** | 34 |
| 2023 | 0.00263% | 42 |
| 2024 | 0.00201% | 46 (Jan-Oct only) |
| 2025 | 0.00146% | not covered |
| 2026 (to Nov 3) | 0.00204% | not covered |

DOC means are the average of daily `timelinevol` values over the days returned.
In online news the phrase peaked in 2022 and fell back by 2025. The top single
days are 2026-09-12 (0.0794%) and 2026-09-20 (0.0720%), then 2022-01-22/23
(around the anniversary of January 6) and 2022-06-07. Without the raw response
we cannot check whether the September 2026 spikes reflect a small daily
denominator. GDELT's daily totals vary widely, so treat them as unconfirmed. On
TV, 193 clips in all, first in 2011-06, rising through 2024. The peak month is
2024-03, with 17 clips (0.0016% of airtime).

Control `democracy` on TV: 674,311 clips. The peak months are 2022-01 (15,220
clips, 1.38% of airtime), 2022-11 and 2024-01. The DOC control is not pinned.

**Anthropic co-mentions (the test).**

| Query | Result |
|---|---|
| DOC `anthropic "health of democracy"` | Non-zero on **3 days in ~10 years**: 2023-08-31, 2026-01-30, 2026-04-11, each under 0.001% of articles |
| DOC `near20:"anthropic democracy"` | Non-zero on **64 days**: 1 each in 2018 and 2020, 4 each in 2023-2025, **50 in 2026**. Peak 2026-02-28 (0.2052% of articles, an order of magnitude above any other day), then 2026-03-18 and 2026-03-01 |
| DOC `near20:"claude democracy"` | Non-zero on 1,602 days, **declining** from 320 days in 2017 to 69 in 2026. That shape is other people named Claude (Jean-Claude and others; not verified article by article), not Anthropic's model. Unusable without disambiguation |
| DOC `anthropic` (control) | Non-zero on 2,144 days; near-daily from 2023. Peak 2026-09-13 (0.5547%) |
| TV `anthropic "health of democracy"`, same clip | **0** clips, 2009-07 to 2024-10 |
| TV `anthropic democracy`, same clip | **0** clips |
| TV `claude democracy`, same clip | 17 clips in 10 months, last in 2023-03; not checked to be Anthropic's Claude |
| TV `anthropic` (control) | 828 clips: 320 in 2023, 410 in Jan-Oct 2024; peak 2023-09 (93 clips) |

What this shows: in the record GDELT monitors, Anthropic and "health of
democracy" almost never appear together, in news or on national TV. Anthropic
near "democracy" became a visible pairing only in 2026, concentrated around one
late-February episode. **These counts do not say whether that coverage credited
Anthropic, criticized it, or merely listed it.** Reading the articles would
need DOC `artlist` mode (URLs and titles), which is not built here.

### 2.3 Known weaknesses

- **"Anthropic" before 2021 is mostly the anthropic principle.** The control
  series is reported from 2017 (DOC) and 2009 (TV) without filtering. Read it
  from 2021 on.
- **"Claude" is a common first name** (Claude Monet, Claude Shannon, and
  others), so `claude` co-mentions are an upper bound.
- **DOC 2.0 searches machine-translated text** in many languages, while
  `"health of democracy"` is an English phrase. Translated articles can match.
- **TV coverage ends in October 2024.** The API accepts a 2026 end date but
  returns no months after 2024-10. The TV series therefore covers none of the
  period in which Anthropic became a household name.
- **API responses are not reproducible.** GDELT recomputes. The saved bytes in
  `.democorpus/gdelt/`, hashed in `MANIFEST.tsv`, are the only pin. A later
  fetch is a new observation, not a check.
- **TV GKG not used.** The American Television Global Knowledge Graph
  (https://blog.gdeltproject.org/announcing-the-american-television-global-knowledge-graph-tv-gkg/)
  annotates the same captions with GKG themes and entities. It would allow
  theme-coded rather than phrase-coded series, but it is a bulk dataset (files
  or BigQuery), not an API, and GDELT warns that captions carry "a high level
  of inherent noise", with person and organization names especially reduced.
  It draws on the same Internet Archive recordings, so it would add themes but
  not later months.

## 3. Rooney Reports (Notre Dame Health of Democracy Survey)

### 3.1 Source

The Rooney Democracy Institute's listing page
(https://rooneyinstitute.nd.edu/research/health-of-democracy-survey/rooney-reports/)
links 13 report PDFs, October 2024 to May 2026. All 13 are pinned, along with
the listing page itself, the survey page, and the two questionnaires the
Institute publishes as PDFs (October 2025 and May 2026 AmeriSpeak omnibus).
`fetch-rooney` checks that every PDF linked from the pinned listing page is
pinned.

The survey has run since October 2022. Its fieldwork is by NORC's AmeriSpeak
panel (R05: "fielded by NORC/UChicago via the Amerispeak panel"), and later
waves follow a panel of the same respondents (R10: N = 1,093).

### 3.2 Method: transcribe text, never charts

Each report is two pages of prose around one to three chart images. Every
percent that appears **in the text layer** was hand-transcribed into
`rooney-transcription.tsv`. Each row carries the report, page, wave as the
report states it, group, the report's wording of the item, whether that wording
is quoted or only described, the value as printed, the numeric percent, and a
verbatim quote. `build` re-extracts each page with `pypdf==5.4.0` and fails
unless:

- the quote is on the stated page (after normalizing whitespace, curly quotes
  and dashes);
- the printed value is in the quote;
- the numeric percent is in the quote.

Hedged values ("roughly 10%", "approximately 93%") keep the hedge in
`value_text` and the number in `percent`. Bounds and ranges ("Over 40%",
"19-22%", "near 4-6%") and verbal fractions ("one-in-four", "Nearly 1 in 5",
"Around 6 in 10") have an empty `percent`: converting them would be an
inference.

**Not extracted:** everything in the chart images. `rooney-reports.tsv` lists
the embedded images per page (charts and logos; 1 to 3 per page). The charts
carry figures the text omits, for example every Independent figure in R01 and
the full least-liked-group distribution in R06. They were not read and not
estimated.

Item wording. The reports paraphrase. For the October 2025 wave, the published
questionnaire gives exact stems, so `rooney-questionnaire.tsv` maps 30 report
items to questionnaire blocks, and `build` checks that each stem occurs in the
pinned questionnaire PDF (`rooney-items.tsv`, with page numbers). Earlier waves'
questionnaires are on Google Drive as codebooks and were not pinned, so for
reports drawing on 2024 and spring 2025 waves the wording is the report's own.

### 3.3 Results

There are 129 transcribed values from 13 reports, all verified against the
pinned PDFs. Most reports print no whole-sample figure, several print none for
Independents, and groups change from report to report (party, Trump vote,
Christian nationalist identity, leaners), so few items form a true series. The
ones that recur across waves, as printed:

| Item (questionnaire block) | Group | Fall 2024 | Spring 2025 | Fall 2025 | Report |
|---|---|---|---|---|---|
| Force may be needed to save the (traditional) American way of life (MCCLDEMO B) | D / R / I | 11 / 29 / 21 | n/p | 23 / 35 / 32 | R08 |
| A time will come when patriotic Americans have to take the law into their own hands (MCCLDEMO C) | D / R / I | 10 / 26 / "around 19-22" | D 10, R ~30, I 15 (April 2025, R07) | 18 / 31 / "around 19-22" | R07, R08 |
| Federal government should declare the US a Christian nation (CHRISTNA A) | D / R / I | "near 4-6" / 31 / 12 | R 34 | 6 / 41 / 17 | R09 |
| American way of life is under attack (CIVILWAR A) | D / R | 49 / 74 | 62 / 73 | n/p | R10 |
| US is on the brink of a new civil war (CIVILWAR B) | D / R / I | 37 / 37 / 31 | 50 / 34 / 39 | n/p | R10 |
| Voting should be easy (SUPPDEMO B) | D / R / I | 94 / 81 / n/p | n/p | 93 / 78 / 79 | R01, R11 |
| President should not be above the law (SUPPDEMO G) | non-Trump / Trump voters; then D / R / I | 97 / 81 (R04; wave not stated) | n/p | 94 / 83 / 81 | R04, R11 |

n/p: not printed in report text. Fall 2025 = the October 2025 wave.

Items asked once in the pinned reports: voting rights and media shutdown (R01);
pure independents and representation (R02); strong-leader items by Trump vote
(R04, R05); least-liked groups (R06); partisan violence (R08: 2-7% agree, Fall
2025); and norm violations, fairness and tolerance (R11-R13, October 2025).

**Inconsistencies in the source, kept as printed:**

- *Force to save the way of life, Republicans.* R07 says "Over 40% of
  Republicans agreed" and calls the result stable across August 2024, November
  2024 and April 2025. R08 gives Republicans 29% in Fall 2024. The questionnaire
  item includes "traditional" (as R07 quotes it); R08 quotes it without. The
  reports do not explain the gap. Possible causes include a different agreement
  cut on the 7-point scale, a different wave, or a different weighting. Do not
  splice R07 and R08 into one series.
- *Mighty leader.* R04 gives Trump voters 66% and non-Trump voters 16%. R05,
  from the Fall 2024 wave, gives 70.8% and 16.4% for the same item. R04 states
  no wave.
- *"Fall 2024"* names both the August 2024 and the late-November 2024 fieldwork
  in different reports. `wave_as_stated` keeps each report's label and does not
  resolve it.
- *Agreement cut.* The items use a 7-point scale. Only R11 and R13 say what
  counts as agreement ("agree or strongly agree", which apparently excludes
  "somewhat agree"). The other reports do not say.
- *R13 tolerance items* are asked about the respondent's least-liked group, and
  "run for office" is asked as a ban ("should be banned from running for public
  office"). R13's "support allowing individuals to run for office" is the
  report's framing.

**An Anthropic finding inside the democracy data.** Three reports (R08
December 2025, R09 January 2026, R10 February 2026) carry an "AI transparency
statement". It begins: "Anthropic's Claude Opus 4.6 was used in initial data
analysis and identification of trends. Results reported were manually and
independently verified by the author without use of generative AI." The full
text is in `rooney-reports.tsv`. So Anthropic's product is an input to the
production of this democracy-health research. That is a fact about tool use,
disclosed by the authors. It says nothing about whether the use improved or
degraded the research. It is also the only point in these sources where
Anthropic touches democracy measurement directly. (R08 is dated December 2025
and names Opus 4.6; we did not check that model's release date against the
report date.)

### 3.4 Microdata

The survey page offers the data to researchers on request: "The Rooney
Democracy Institute is making our Health of Democracy Survey data available to
other researchers. You can review our codebooks below and fill out a request for
the data using the form below." The request is a Google Form, and the page
states no license. Codebooks for October 2022, June 2023, December 2023, August
2024, November 2024 and April 2025 are on Google Drive; October 2025 and May 2026
are on the Institute's site. **Microdata would replace this whole transcription
step**: the full 7-point distributions, every party group, and weighted
toplines for items the reports never print (for example AUTODEMO "Having a
democratic political system", asked in October 2025). The terms for publishing
derived tables are unknown until a request is answered. Ask before building on
it.

## 4. What none of these answers

- **Attention is not health.** More articles saying "health of democracy" can
  mean more threat, more advocacy, or one viral op-ed. These series count
  words.
- **Stated attitudes are not conditions.** Rooney measures what respondents say
  about norms. It does not measure institutions, elections or rights. V-Dem and
  Freedom House (§5.3) rate conditions, by expert coding.
- **No series isolates Anthropic.** The best available is a co-mention count,
  which cannot tell praise from criticism, or Anthropic's work on democracy from
  a reporter's list of AI companies.
- **Rooney asks nothing about AI or technology companies.** Neither pinned
  questionnaire mentions artificial intelligence. The only technology option is
  "Social media and misinformation", one of six answers to the new May 2026 item
  DEMOPROB ("the most important problem facing American democracy"), and no
  pinned report prints its result.
- **Causality is out of reach.** Even a perfect Anthropic-specific series would
  show association with attention, not an effect on democratic health.

## 5. Feasibility notes (not built)

Sources for this section were read on 2026-11-04 and are cited by URL, not
pinned. Anything marked "not verified" was not confirmed from a primary page.

### 5.1 The Trust Project

**What it is:** a news-credibility *standard*, not a measure of trust levels.
https://thetrustproject.org describes "an international consortium of news
organizations" whose member sites display eight Trust Indicators: Best
Practices, Journalist Expertise, Type of Work, References, Methods, Locally
Sourced, Diverse Voices, and Actionable Feedback. It reports "more than 300 news
sites" as partners.

**Time series:** none found. It publishes no member-count history and no survey.
Its FAQ (https://thetrustproject.org/faq/) cites only one-off results (Reach
Plc's own report of higher trust in The Mirror after adopting the indicators,
and a University of Texas Center for Media Engagement experiment). The only
series one could build is adopting outlets over time, reconstructed from
Wayback snapshots of the partner list (not attempted). That would count a supply
of credibility labels, not public trust. The site is "All rights reserved", and
its FAQ calls "The Trust Project and Trust Indicators" exclusive trademarks.

**Verdict:** not a democracy-health proxy. At most, an outlet-level covariate:
whether a news source carries the indicators.

### 5.2 BCG Trust Index

**Method as BCG describes it.** Sources: the 2022 article
(https://www.bcg.com/publications/2022/trust-index-analyzing-companies-trustworthiness)
and the May 2022 report *What AI Reveals About Trust in the World's Largest
Companies*
(https://web-assets.bcg.com/f5/46/c936df6540348a390708774edbb6/bcg-what-ai-reveals-about-trust-in-the-worlds-largest-companies-may-2022-2.pdf),
pp. 7-8 and the methodology appendix, pp. 31-32.

- *Dimensions:* four. **Competence** is "whether the company can effectively
  accomplish a specific task at hand". **Fairness** is "how equitable and
  empathetic the company is in delivering on its promise". **Transparency** is
  "how open and unambiguous the company's decision making and actions are".
  **Resilience** is "how effectively the company avoids or recovers from
  challenges and crises". BCG ties them to the ability, benevolence and
  integrity model (Mayer et al. 1995).
- *Data:* scraped traditional news ("leading wire services, newspapers, and
  journals") and Twitter, "more than 100,000 sources worldwide", English only
  per the article. The universe is about 1,100 public companies with market
  capitalization above $20B, over 2018-2021.
- *Mention detection:* "a list of more than 200 words derived from the academic
  literature", positive and negative, per dimension. Examples: competence
  includes credibility, capability, expertise, reliability. Fairness includes
  concern, commitment, principle, respect, values. Transparency includes
  forthrightness, accuracy, honesty, candor. Resilience includes confidence,
  control, risk management, with antonyms such as corruption, lawsuits and
  scandals.
- *Scoring:* an NLP engine (Quid) labels each trust mention positive, neutral
  or negative. Neutral mentions are discarded. For each source, the score is
  (positive − negative) / (positive + negative), on −1.0 to +1.0. Source scores
  are weighted by "strength" = sentences × potential impressions (subscribers or
  followers). On average, impressions split 91% traditional news and 9% social
  media. Scores are compared with industry benchmarks, and BCG recommends using
  the index "primarily as a relative metric, rather than as an absolute one".
- *Self-stated limits:* it measures "trusting sentiment, a proxy for trust", and
  news and social sources may overrepresent some voices and newsworthy topics.

**Updated after 2022?** No new edition of the index was found. A 2024 article
(https://www.bcg.com/publications/2024/rebuilding-corporate-trust) reuses the
approach ("real-time natural language processing to analyze news and social
media mentions and impressions") on 177 companies, Q4 2019 to Q3 2022. bcg.com
was not searched exhaustively, so this is "not found", not "none exists". No
underlying data is public.

**Extending it to Anthropic and peers with this repo's tools.** Peers: OpenAI,
Google (Alphabet), Microsoft, Meta. BCG's own universe excludes Anthropic and
OpenAI, which are private.

| BCG component | Repo substitute | Gap |
|---|---|---|
| Mention corpus: news | GDELT DOC 2.0 `artlist` mode, which returns article URLs and titles (up to 250 per call), pinned like the timelines here, then fetched article text | Needs article fetches; publisher terms vary; GDELT gives no full text |
| Mention corpus: social | Hacker News corpus (`corpus/hacker-news/`, Anthropic set already built, IDs only); peers need their own regex sets | HN is practitioners, not the public; no Twitter/X (BCG's social source is now paid API only) |
| Mention corpus: investors | Earnings-call AI corpus (`corpus/earnings-calls/`): analysts and executives talking about the peers, verbatim and anchored | Covers public companies' calls; Anthropic appears only as mentioned by others |
| 200-keyword trust lexicon | BCG publishes examples, not the list. A published, versioned regex per dimension, built from the examples and Mayer et al. | Not BCG's list, so not BCG's index. Name it differently |
| Quid sentiment (positive / neutral / negative) | The two NLI witnesses (DeBERTa-v3-large and ModernBERT-large zero-shot, `docs/earnings-call-ai-corpus.md` §5), with hypotheses per dimension and polarity ("The text says {company} is competent at ..."). A proposed label needs both witnesses ≥ 0.5 | Witness output is a proposal, never a verdict, until a stratified human gold set measures precision (`docs/bert-enrichment-spec.md` §5) |
| Impressions weighting | None free. GDELT gives no readership. HN points or comment counts are a weak stand-in | Proprietary (audience data); report unweighted and say so |
| Industry benchmark | The peer set itself (relative, as BCG advises) | Five companies is a thin benchmark |

**Proprietary parts:** Quid (the NLP engine and its theme graphs), the
traditional-news archive with impression counts, Twitter/X firehose access, and
the full keyword list. Everything else can be rebuilt from public, pinned data
with the repo's existing method. The result would be a *BCG-style* trust
sentiment index, not the BCG Trust Index, and like BCG's it would measure talk
about trust, not trust.

### 5.3 Other free proxies

| Source | What it measures | License / terms | Cadence | AI or tech? |
|---|---|---|---|---|
| V-Dem dataset (https://v-dem.net/data/the-v-dem-dataset/), v16, March 2026 | Expert-coded democracy conditions, country-year | CC BY-SA 4.0 (share-alike, so derived tables cannot sit under CC0); free download | Annual (March) | No company coverage. Has digital-society and disinformation indicators (specific variables not verified) |
| Freedom House, Freedom in the World (https://freedomhouse.org/report/freedom-world), 2026 edition | Political rights and civil liberties scores, 208 countries and territories | "free for personal, academic, and nonprofit use"; commercial use needs permission (https://freedomhouse.org/content-permissions); no open license | Annual | No. Freedom on the Net is separate (not checked) |
| Pew Research Center, public trust in government (https://www.pewresearch.org/politics/2025/12/04/public-trust-in-government-1958-2025/) | Trust in federal government, 1958-2025; 17% in September 2025 | Terms allow citation; survey data may be republished only as excerpts, and scraping is prohibited (https://www.pewresearch.org/about/terms-and-conditions/). Cite points; do not commit the full series | Irregular, several times a year | Separate AI-attitude surveys (e.g. https://www.pewresearch.org/internet/2025/09/17/how-americans-view-ai-and-its-impact-on-people-and-society/: concern rose from 37% in 2021 to 50% in 2025), not a fixed series |
| Gallup, Confidence in Institutions (https://news.gallup.com/poll/712436/confidence-institutions-remains-near-time-low.aspx) | Confidence in 15+ institutions, since 1973 (some since 1993) | Copyright Gallup, all rights reserved; reuse terms not verified; microdata licensed (not verified) | Annual (June) | **Yes, sector level:** "large technology companies" since 2020, 32% then, 20% in June 2026 (a new low). No AI item |
| Edelman Trust Barometer (https://www.edelman.com/trust) | Trust in business, government, NGOs, media; by sector; ~28 countries | Reports free to read; data terms not verified (Edelman pages returned 403 to our fetch) | Annual (January) | **Yes:** technology sector trust and "AI companies" items (2025 tech-sector brief: 56% global trust in AI companies, via secondary summary, not verified from the PDF) |

**Recommendation.** For *conditions*, V-Dem is the only open, bulk-reusable
series. Its share-alike license means derived tables go in their own folder with
their own license, like `corpus/*/` here. For *trust in the tech sector*,
Gallup's annual item is the cleanest public series. It is seven points long and
covers the sector, not any company. No free source measures trust in Anthropic
specifically. That is a finding about the evidence base, and the paper should
say so rather than fill the gap with proxies.

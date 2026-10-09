# Favoured Banks in ChatGPT and Gemini: data pipeline design

**Owner:** Rahmananda Ridho Gamawan (RG)
**Date:** 2026-10-09
**Scope:** everything from the raw answers to analysis-ready tables. The dashboard is a separate spec, written after this pipeline is done and checked.

## 1. Goal

Measure which Indonesian banks ChatGPT and Gemini favour when people ask everyday banking questions, and which web sources those answers rely on. The output is a set of clean tables, each traceable to the 40 raw answers, that a dashboard (or anyone with pandas) can read without recomputing anything.

Success means:

- Every number in the output tables can be traced back to a row in `data/raw/`.
- Every metric is stored with its N (answers, sentences, citations or pages).
- Anything that could not be measured is stored as missing with a reason, never as zero.
- The whole pipeline reruns from a fresh clone. The only step that needs the internet is the crawl, and it runs in GitHub Actions.
- No API keys anywhere. No third-party page text committed to the repo.

## 2. Inputs

| File | What it is |
|---|---|
| `data/raw/geo-bank-research.xlsx` | 20 prompts (`#`, `Pillar`, `Intent`, `Prompt`) with RG's pasted answers in columns `ChatGPT` and `Gemini`. |
| `data/raw/chatgpt-prompt08-rerun.md` | RG's re-run of ChatGPT prompt 8. The original answer had no citation list. This file replaces that answer in full. |

Unit of analysis: one **answer** = one prompt × one engine. There are 40 answers.

Pillars: Fees & rates, Digital experience, Safety & security, Service, Trust.
Intents: Best, Compare, Decision brief, How-to, Informational.

## 3. Pipeline

```
data/raw/ (xlsx + prompt 8 re-run)
  │ Step 1  parse          (Python, local or CI)
  ▼
data/interim/answers.csv, sentences.csv, citations.csv
  │ Step 2  brand dictionary (labelled by Claude, reviewed by RG)
  ▼
config/brands.yaml  →  data/interim/mentions.csv
  │ Step 3  crawl + derive (GitHub Actions, once)
  ▼
data/interim/pages.csv, attribution.csv, page_brand_counts.csv
  │ Step 4  labels         (Claude, reviewed by RG)
  ▼
config/domains.csv, data/labels/sentiment.csv
  │ Step 5  aggregate      (Python, local or CI)
  ▼
data/processed/*.csv + *.json  and  docs/data-quality.md
```

Each step reads only the outputs of earlier steps, so any step can be rerun on its own.

### Step 1: Parse

**Answers** (`answers.csv`, 40 rows): `answer_id` (e.g. `gpt-08`, `gem-08`), `engine`, `prompt_no`, `pillar`, `intent`, `prompt`, `answer_body` (text above the citation heading), `run_note`.

**Citation section rule (from RG):** only links listed under the citation heading count. Inline links in the answer body are ignored. Heading variants found in the data:

| Engine | Heading | Answers |
|---|---|---|
| Gemini | `### Links Cited` | 19 |
| Gemini | `### Sumber & Referensi Link` | 1 |
| ChatGPT | `10 tautan sumber` / `## 10 tautan sumber` | 19 (incl. prompt 8 re-run) |
| ChatGPT | `10 referensi dan tautan sumber` | 1 |

The parser matches these with one case-insensitive pattern and uses the last match in the answer. An answer with no heading fails the run loudly instead of yielding zero citations.

**Citations** (`citations.csv`): `answer_id`, `engine`, `rank` (1 to 10, list order), `url_raw`, `url` (normalized), `domain`.

URL normalization:
1. Take the first URL on each list line (Gemini and ChatGPT both write `[url](url)`).
2. Unwrap Google redirects: `google.com/search?q=<url>` becomes `<url>`.
3. Drop query parameters starting with `utm_`. Keep the rest.
4. Lowercase the host, drop a leading `www.`, drop a trailing `/` on the path.
5. Within one answer, keep the first occurrence of a duplicate URL. (ChatGPT prompt 2 lists the same blu page twice, so it has 9 citations.)

Expected counts after Step 1: 40 answers, 399 citations, 241 unique URLs, 99 domains. The run checks these and fails if they change without the raw data changing.

**Sentences** (`sentences.csv`): `answer_id`, `sent_idx` (0-based), `text`, `n_words`.

Body cleaning before splitting:
- Remove image lines (`![...](...)`), including ChatGPT favicons and `images.openai.com` thumbnails.
- Remove ChatGPT chip artifacts: lines that are only `+N`, the line `Add to Favorites`, and short source-name lines (4 words or fewer) that sit between a favicon line and a `+N` line or the next paragraph.
- Strip markdown syntax (`#`, `*`, `**`, table pipes, link brackets) but keep the link text.
- Drop horizontal rules (`---`).

Splitting: each list item and each table row is one sentence. Paragraphs are split on `.`, `?` or `!` followed by a space and a capital letter or digit, with protection for decimals (`6,5%`, `Rp2.000`) and common abbreviations (`p.a.`, `Tbk.`, `dll.`, `No.`). `|S|` is the sentence count of that answer.

### Step 2: Brand dictionary and mentions

`config/brands.yaml` lists every bank that appears in the 40 answers. Claude builds it from the answers, and RG reviews it before Step 3. Each entry has:

- `brand`: canonical name (e.g. `Bank Jago`)
- `group`: parent group for roll-ups (e.g. `blu` → `BCA Group`), optional
- `type`: `conventional`, `digital`, `sharia`
- `aliases`: strings that count as a mention
- `case_sensitive`: true for short acronyms (`BCA`, `BRI`, `BNI`, `BSI`, `BTN`)
- `ambiguous`: true when an alias is also an ordinary word (for example `Jago`, which also means "skilled", and `blu`)

Matching rules:
- Whole-word match only.
- Longest alias wins, so `blu by BCA Digital` counts as blu, not BCA.
- For ambiguous aliases, Claude reviews each hit in context and records it in `data/labels/ambiguous_hits.csv` (keep or reject, with the sentence). Only kept hits count.

**Mentions** (`mentions.csv`): `answer_id`, `sent_idx`, `brand`, `alias_matched`, `char_pos`.

The same dictionary is used again in Step 3 to count brands in crawled pages, so it must be final before the crawl runs.

### Step 3: Crawl and derive (GitHub Actions)

The crawl can't run from Claude's workspace (its network blocks bank and news sites), so it runs as a manually triggered GitHub Actions workflow on RG's repo. Claude triggers it and commits the outputs. RG doesn't need to do anything.

**Fetching**
- One request per unique URL (241), with a 1-second gap per domain and a 20-second timeout.
- User agent: `FavouredBanksResearch/1.0 (+repo URL)`.
- Respect `robots.txt`. URLs it disallows are recorded with status `robots_disallowed` and not fetched.
- Follow redirects and record the final URL.
- HTML: extract the main text with `trafilatura`.
- PDF (the annual reports): extract text with `pypdf`, capped at the first 300 pages. Record the page count.

**Per-page derived fields** (`pages.csv`, one row per unique URL):
`url`, `final_url`, `http_status`, `fetch_error`, `content_kind` (`html`, `pdf`, `other`), `is_readable` (status 200 and at least 50 words extracted), `title`, `n_words`, `published_date`, `date_source`, `schema_types`, `has_article_schema`, `has_faq_schema`, `has_org_schema`, `crawled_at`.

- `published_date` comes from, in order: JSON-LD `datePublished`, `article:published_time` meta, then `htmldate`. `date_source` records which one was used. If none is found, both fields are empty.
- `schema_types` lists the JSON-LD `@type` values found.

**Brand counts in pages** (`page_brand_counts.csv`): `url`, `brand`, `count`, `first_pos_ratio` (position of the first mention ÷ text length). These use the Step 2 dictionary. For ambiguous aliases in pages, only the unambiguous aliases count (for example `Bank Jago` counts, bare `Jago` doesn't), because 241 pages are too many to review by hand.

**Sentence attribution** (`attribution.csv`): one row per answer sentence.
`answer_id`, `sent_idx`, `best_url`, `score`, `second_score`, `attributed` (true/false).

Method:
1. Tokenize the sentence and each cited page's text: lowercase, strip punctuation, remove Indonesian and English stopwords (a fixed list in `config/stopwords.txt`).
2. Score = share of the sentence's content-word bigrams that appear in the page text. Sentences with fewer than 3 content words use unigrams.
3. Compare only against the 10 pages cited by the same answer, and only pages with `is_readable = true`.
4. The best-scoring page gets the sentence if `score ≥ 0.30` (`config/metrics.yaml: attribution_threshold`). Ties go to the higher-ranked citation.
5. Otherwise the sentence is unattributed.

The threshold is checked before the full run: Claude hand-labels 30 sentences (15 per engine) with the page each one most likely came from, and the chosen threshold must agree on at least 24 of 30. The check and its result go in `docs/data-quality.md`.

**What is committed:** `pages.csv`, `page_brand_counts.csv` and `attribution.csv`. Raw HTML, PDFs and extracted text are not committed. They are uploaded as a workflow artifact (90-day retention), so the derive step can rerun without fetching again.

### Step 4: Labels

**Domain labels** (`config/domains.csv`, one row per domain, 99 rows): `domain`, `domain_type`, `authority_tier`, `note`.

| domain_type | Examples from the data | authority_tier |
|---|---|---|
| `regulator` | ojk.go.id, lps.go.id, bi.go.id, peraturan.bpk.go.id | High |
| `bank_official` | bca.co.id, jago.com, seabank.co.id, bni.co.id | High |
| `news_media` | keuangan.kontan.co.id, finansial.bisnis.com, detik.com, kompas.com, tirto.id | Medium |
| `fintech_platform` | fazz.com, akulaku.com, pluang.com, cermati.com | Medium |
| `blog_aggregator` | zaipad.com, kawula.id, invesnesia.com | Low |
| `forum_ugc` | reddit.com | Low |
| `app_store` | play.google.com | Low |
| `other` | anything that fits none of the above, with a note | Low |

Subdomains inherit from the parent unless listed separately (for example `find.ojk.go.id` → regulator). Authority values for scoring: High = 1.0, Medium = 0.7, Low = 0.4 (in `config/metrics.yaml`).

**Sentiment** (`data/labels/sentiment.csv`, one row per answer × brand mentioned):
`answer_id`, `brand`, `label` (`positive`, `neutral`, `negative`, `mixed`), `score` (+1, 0, −1, 0), `evidence` (the sentence index or indices used), `reason` (one line).

Claude labels these. Definitions:
- **positive:** the answer recommends the bank or describes a clear advantage.
- **negative:** the answer warns against it or describes a clear drawback.
- **mixed:** both of the above.
- **neutral:** listed or described without judgement.

RG spot-checks 4 answers (2 per engine, picked at random with a fixed seed) and records agreement in `docs/data-quality.md`.

### Step 5: Aggregate

All formulas live in `scripts/metrics.py` and all constants in `config/metrics.yaml`. Outputs go to `data/processed/` as CSV (for people) and JSON (for the dashboard). Every metric table has an `n` column.

**Answer level**

| Metric | Definition | Cut by |
|---|---|---|
| Mention rate | answers mentioning the brand ÷ answers | brand × engine, brand × pillar, brand × intent |
| AI-SOV | brand mentions ÷ all brand mentions (counted per sentence-level mention) | brand × engine, brand × pillar |
| No-brand rate | answers with zero brand mentions ÷ answers | engine × intent |
| Brand PAWC | per answer: Σ over sentences mentioning the brand of `n_words · exp(−sent_idx / |S|)` ÷ Σ over all sentences of `n_words`. Averaged over all answers in the cut, with 0 where the brand is absent. | brand × engine, brand × pillar |
| First-mention position | `sent_idx` of the first mention ÷ `|S|`, over answers that mention the brand | brand × engine |
| Sentiment | mean score and label counts | brand × engine |
| Platform diversity | engines mentioning the brand ÷ 2 | brand |

The PAWC formula follows Aggarwal et al. (KDD 2024, arXiv:2311.09735), section 2.2.1. Brand PAWC applies it to brands instead of sources, and the methodology notes say so.

**Citation level** (399 citations)

| Metric | Definition | Cut by |
|---|---|---|
| Domain citations | count of citations | domain × engine |
| Domain reach | unique pages, prompts and answers citing the domain | domain |
| Most cited domains | top 15 by citations, with type and tier | overall, per engine |
| Most cited pages | top 15 URLs by citations, with domain and engines | overall, per engine |
| Cross-engine pages | URLs cited by both engines | list + count |
| Average rank | mean `rank` (1 to 10) | domain × engine |
| Concentration | top-5 domains' share of all citations | engine |
| Domain-type mix | share of citations by `domain_type` | engine × pillar |
| Authority mix | share of citations by tier | engine |

**Page level** (crawled pages)

| Metric | Definition | Cut by |
|---|---|---|
| Source PAWC | per answer and page: Σ over sentences attributed to the page of `n_words · exp(−sent_idx / |S|)` ÷ total answer words. Summed per page across answers, then rolled up per domain. | page, domain × engine |
| Attribution coverage | attributed sentences ÷ all sentences | engine |
| Source-SOV | brand counts in readable pages ÷ all brand counts in readable pages (each unique page counted once) | brand |
| SOV gap | AI-SOV − Source-SOV | brand |
| Readability | share of pages readable, by status reason | engine, domain_type |
| Recency | days from `published_date` to the answer date, in groups ≤30, 31 to 180, 181 to 365, >365, unknown | engine, domain_type |
| Schema presence | share of readable HTML pages with any JSON-LD, and with Article / FAQ / Organization types | domain_type |

**VIS (0 to 100)**, one row per brand and per brand × engine:

`VIS = 100 × mean(PAWC_norm, Authority, Sentiment_norm, Diversity)`

- `PAWC_norm` = brand PAWC ÷ the highest brand PAWC in the same cut.
- `Authority` = mean authority value of the cited pages, in the answers that mention the brand.
- `Sentiment_norm` = (mean sentiment score + 1) ÷ 2.
- `Diversity` = platform diversity. It isn't used in the per-engine VIS, where it would always be 1.

Equal weights, stored in `config/metrics.yaml`. Brands mentioned in fewer than 3 answers get VIS but carry `low_n = true`.

### Data-quality report

`docs/data-quality.md` is generated by the pipeline and records:
- Expected vs actual counts at every step.
- Citations per answer (should be 10, or 9 for gpt-02).
- Crawl outcomes by status, with every unreadable URL listed.
- Attribution threshold check (agreement out of 30) and coverage per engine.
- Ambiguous brand hits kept and rejected.
- Sentiment spot-check result.
- Known limitations (Section 6).

## 4. Repository layout

```
geo-bank-visibility/
├── config/            brands.yaml, domains.csv, metrics.yaml, stopwords.txt
├── data/
│   ├── raw/           xlsx + prompt 8 re-run (RG's own runs)
│   ├── interim/       step 1 to 3 outputs
│   ├── labels/        sentiment.csv, ambiguous_hits.csv, attribution_check.csv
│   └── processed/     step 5 outputs (CSV + JSON)
├── scripts/           parse.py, mentions.py, crawl.py, derive.py, metrics.py, run_all.py
├── tests/             pytest, small hand-checked fixtures
├── docs/              data-quality.md, superpowers/specs/, superpowers/plans/
├── .github/workflows/ crawl.yml (manual), ci.yml (tests on push)
├── requirements.txt
└── README.md
```

## 5. Testing

Fixture-based pytest, all offline:
- **Parser:** each heading variant, Google redirect unwrapping, `utm_` stripping, the trailing-slash duplicate, and a missing heading that must raise.
- **Sentence splitter:** decimals, `Rp` amounts, abbreviations, list items, table rows, chip artifacts.
- **Brand matcher:** longest-alias wins, case-sensitive acronyms, ambiguous aliases routed to review.
- **PAWC:** a 4-sentence answer with hand-computed values for brand PAWC and source PAWC.
- **Attribution:** a fixture page and three sentences (clear match, weak match, no match).
- **Metrics:** a 6-answer fixture with hand-computed mention rate, AI-SOV, domain counts and VIS.
- **Count checks:** the real Step 1 counts (40 / 399 / 241 / 99) as a regression test.

The crawler's network code isn't unit-tested. Its derive step is tested on two saved fixture pages (one HTML, one PDF) committed under `tests/fixtures/`, which are short pages written for the test, not copies of real sites.

## 6. Known limitations (stated in the output)

- One run per prompt per engine, from RG's accounts on 2026-10-09. AI answers vary between runs, so this is a snapshot.
- The prompts ask for sources, which pushes both engines to cite more than they would by default.
- Source PAWC uses reconstructed attribution (lexical overlap), not attribution the engines published.
- Pages blocked to GitHub's servers can't be attributed or counted in Source-SOV. The share is reported.
- Sentiment and domain types are labelled by Claude and spot-checked by RG.
- Brand counts in crawled pages skip bare ambiguous aliases, which undercounts some digital banks in sources.

## 7. Out of scope for this spec

Dashboard views and design, deployment to GitHub Pages, scheduled re-runs, more engines, and traffic or revenue metrics.

## 8. Open questions (defaults apply unless RG changes them)

| # | Question | Default |
|---|---|---|
| Q1 | Repo name and visibility | Settled: `rgmwnn/geo-bank-visibility`, public |
| Q2 | Date of the original runs | 2026-10-09 for all 40 answers |
| Q3 | Keep bank subsidiaries such as blu (BCA Digital) as separate brands? | Separate brands, with a `group` field for roll-ups |

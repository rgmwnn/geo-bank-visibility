# Favoured Banks in ChatGPT and Gemini

Which Indonesian banks do ChatGPT and Gemini recommend when people ask everyday banking questions, and which web pages do those answers lean on?

This repo holds the data pipeline behind that question. It turns 40 AI answers into tables you can analyse or chart: brand mentions, share of voice, prominence in the answer, sentiment, the domains and pages each engine cites, and what those cited pages say.

## The dataset

- 20 prompts in Bahasa Indonesia about savings and digital banking, written by Rahmananda Ridho Gamawan (RG). They cover five pillars (fees and rates, digital experience, safety and security, service, trust) and five intents (best, compare, decision brief, how-to, informational).
- Each prompt was asked once in ChatGPT and once in Gemini on 9 October 2026, from RG's own accounts, with a request for 10 sources at the end.
- Raw answers: `data/raw/geo-bank-research.xlsx`, plus the two re-runs described in `docs/data-quality.md`.
- Only links listed under each answer's source heading count as citations. Links inside the answer text are ignored.

## What is measured

| Metric | Unit | Meaning |
|---|---|---|
| Mention rate | answers | Share of answers that name the bank |
| AI-SOV | mentions | The bank's share of all bank mentions in the answers |
| Brand PAWC | sentences | How much of an answer talks about the bank, with earlier sentences weighted more (`exp(-position / sentence count)`, from Aggarwal et al. 2024, applied to brands) |
| First-mention position | sentences | How early in the answer the bank first appears (0 = first sentence) |
| Sentiment | answer and bank pairs | Positive, neutral, negative or mixed, labelled by Claude with a one-line reason |
| Domain and page citations | citations | Which sites and pages each engine cites, how often, and at what position in the source list |
| Source PAWC | sentences | Share of each answer found in each cited page, matched by word-pair overlap |
| Source-SOV | crawled pages | The bank's share of brand mentions across the readable cited pages, each page weighted equally |
| SOV gap | | AI-SOV minus Source-SOV. Positive means the engines talk about the bank more than its cited sources do |
| VIS (0 to 100) | | Equal-weight mean of brand PAWC (scaled to the leader), source authority, sentiment and engine coverage |

Mobile apps and subsidiaries credit their parent bank: blu, myBCA and BCA mobile count for BCA; Livin' for Bank Mandiri; BRImo and Bank Raya for BRI; wondr for BNI; Jenius for Bank BTPN. The app name stays in the `sub_brand` column.

## How it runs

```
data/raw  ->  parse  ->  sentences  ->  brand mentions  ->  crawl + derive (GitHub Actions)  ->  metrics  ->  data/processed
```

1. `scripts/parse.py` reads the answers and the source lists, and normalizes URLs (unwraps Google redirects, drops `utm_` tags).
2. `scripts/sentences.py` cleans copy-paste leftovers and splits answers into sentences.
3. `scripts/brands.py` finds bank names using `config/brands.yaml`. Names that are also ordinary words (such as "Jago") were checked by hand and recorded in `data/labels/ambiguous_hits.csv`.
4. `.github/workflows/crawl.yml` fetches each cited page once, respecting `robots.txt`, and commits derived facts only: status, word count, publish date, schema types, brand counts and sentence match scores. No page text is stored in this repo.
5. `scripts/metrics.py` builds every table in `data/processed/` as CSV and JSON.
6. `scripts/quality.py` writes `docs/data-quality.md`: counts, crawl outcomes, the attribution check and the known limitations.

### Rerun it

```bash
pip install -r requirements.txt
python -m scripts.run_all      # everything except the crawl
pytest
```

To crawl again, run the `crawl` workflow from the Actions tab, or change `crawl/request.txt` and push.

No API keys are needed anywhere.

## Read before quoting the numbers

`docs/data-quality.md` lists what could not be measured and why. In short: this is a single snapshot of 40 answers; asking for 10 sources makes both engines cite more than usual; Source PAWC uses reconstructed matching that agreed with a hand check on 18 of 30 sentences; and pages that blocked the crawler are left out of page-level metrics.

## Credits

- Position-adjusted word count: Aggarwal, P. et al. *GEO: Generative Engine Optimization.* KDD 2024. [arXiv:2311.09735](https://arxiv.org/abs/2311.09735)
- Pipeline built with Claude, from RG's design and data.

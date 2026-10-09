# Favoured Banks Data Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn RG's 40 ChatGPT/Gemini answers into analysis-ready tables (mentions, citations, crawled-page facts, PAWC, SOV, VIS) with a data-quality report, all reproducible from the repo.

**Architecture:** Small single-purpose Python modules under `scripts/`, each reading the previous step's CSVs and writing its own. The only network step (crawl) runs in a GitHub Actions workflow that commits derived CSVs back; raw page bytes stay in a workflow artifact. Labels made by Claude (brands, domains, sentiment, attribution check) are committed files validated by tests.

**Tech Stack:** Python 3.11, pandas, openpyxl, PyYAML, requests, trafilatura, htmldate, beautifulsoup4, pypdf, pytest; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-09-favoured-banks-data-pipeline-design.md`

## Global Constraints

- No API keys or secrets anywhere; workflows use only `GITHUB_TOKEN`.
- Never commit third-party page text, HTML or PDFs. Commit only derived fields (titles, counts, dates, scores).
- Every metric table has an `n` column. Unmeasurable values are empty with a reason column, never 0.
- Run date for all 40 answers: `2026-10-09`.
- Subsidiaries credit their parent brand (`blu`/`BCA Digital` → `BCA`), with `sub_brand` kept.
- Only links under the citation heading count; inline body links are ignored.
- Expected Step 1 counts: 40 answers, 399 citations, 241 unique URLs, 99 domains.
- Crawl: user agent `FavouredBanksResearch/1.0 (+https://github.com/rgmwnn/geo-bank-visibility)`, 1 s gap per domain, 20 s timeout, respect `robots.txt`, PDFs capped at 300 pages.
- PAWC weight is `exp(-sent_idx / n_sents)`, sentence-based, per Aggarwal et al. 2024.
- All constants live in `config/metrics.yaml`; all formulas in `scripts/`.
- Prose in README and `docs/data-quality.md`: plain English, no em dashes, no hype words.

## Review Focus

1. **CRLF line endings** (the prompt 8 re-run file has them): heading detection and list parsing must behave exactly as with LF. Test in Task 1.
2. **Gemini link whose label is the real URL but href is a Google redirect, or the reverse:** both must yield the real URL. Test in Task 2.
3. **Lowercase "jago" as an ordinary word** ("jago masak") must not count as Bank Jago, while "Jago" in a bank context goes to review. Test in Task 4.
4. **HTTP 200 pages that are consent walls or JS shells (<50 words)** must be `is_readable=False` and excluded from attribution and Source-SOV. Test in Task 5.
5. **A brand that appears in crawled pages but in no answer** must still appear in Source-SOV with AI-SOV 0 and a negative SOV gap, not be dropped. Test in Task 9.

---

## File map

| File | Responsibility |
|---|---|
| `requirements.txt`, `pytest.ini` | dependencies; `pythonpath = .` |
| `config/metrics.yaml` | every constant (threshold, authority values, run date, expected counts, low-n) |
| `config/brands.yaml` | brand dictionary (Task 4) |
| `config/domains.csv` | domain type + authority tier (Task 8) |
| `config/stopwords.txt` | Indonesian + English stopwords, one per line |
| `scripts/io.py` | paths constants, `read_csv`/`write_csv` helpers, `load_config()` |
| `scripts/parse.py` | answers + citations |
| `scripts/sentences.py` | body cleaning + sentence splitting |
| `scripts/brands.py` | brand loading, matching, mentions |
| `scripts/derive.py` | offline extraction from fetched bytes, page brand counts, attribution scores |
| `scripts/crawl.py` | network fetch into a cache dir (Actions only) |
| `scripts/metrics.py` | all aggregations |
| `scripts/quality.py` | writes `docs/data-quality.md` |
| `scripts/run_all.py` | runs local steps in order |
| `.github/workflows/ci.yml` | pytest on push |
| `.github/workflows/crawl.yml` | crawl + derive + commit back |
| `data/labels/*.csv` | Claude's labels (ambiguous hits, sentiment, attribution check) |

---

### Task 1: Scaffold and answers table

**Files:**
- Create: `requirements.txt`, `pytest.ini`, `config/metrics.yaml`, `scripts/__init__.py`, `scripts/io.py`, `scripts/parse.py`, `.github/workflows/ci.yml`, `.gitignore` (ignore `.cache/`, `__pycache__/`)
- Test: `tests/test_parse_answers.py`

**Interfaces:**
- Produces:
  - `scripts.io.ROOT: Path`, `load_config() -> dict`, `write_csv(df, rel_path: str) -> None`, `read_csv(rel_path: str) -> pd.DataFrame`
  - `scripts.parse.HEADING_RE: re.Pattern` (case-insensitive, multiline; matches `links cited`, `link cited`, `sumber & referensi link`, `10 tautan sumber`, `10 referensi dan tautan sumber`, optional leading `#`s)
  - `split_citation_section(text: str) -> tuple[str, str]` returns `(body, section)` split at the LAST heading match; raises `ValueError("no citation heading")` if none.
  - `load_answers(xlsx: Path, rerun: Path) -> pd.DataFrame` columns `answer_id, engine, prompt_no, pillar, intent, prompt, answer_raw, run_date`; `answer_id` is `gpt-01`..`gpt-20`, `gem-01`..`gem-20`; ChatGPT prompt 8 text replaced by the rerun file; all text normalized to `\n` line endings.

`config/metrics.yaml` starts with:
```yaml
run_date: "2026-10-09"
expected_counts: {answers: 40, citations: 399, unique_urls: 241, domains: 99}
attribution_threshold: 0.30
attribution_min_agreement: 24   # out of 30 hand-labelled sentences
authority_values: {High: 1.0, Medium: 0.7, Low: 0.4}
low_n_answers: 3
readable_min_words: 50
pdf_max_pages: 300
recency_bins: [30, 180, 365]
vis_weights: {pawc: 1, authority: 1, sentiment: 1, diversity: 1}
```

- [ ] **Step 1: Write failing tests**

```python
def test_heading_variants_split():
    for h in ["### Links Cited", "### Sumber & Referensi Link", "## 10 tautan sumber",
              "10 tautan sumber", "10 referensi dan tautan sumber"]:
        body, sec = split_citation_section(f"Isi jawaban.\n\n{h}\n\n1. [https://a.id](https://a.id)")
        assert body.strip() == "Isi jawaban." and "https://a.id" in sec

def test_crlf_same_as_lf():
    t = "Isi.\r\n\r\n## 10 tautan sumber\r\n\r\n1. [https://a.id](https://a.id)\r\n"
    crlf = [x.replace("\r", "") for x in split_citation_section(t)]
    lf = list(split_citation_section(t.replace("\r\n", "\n")))
    assert crlf == lf

def test_missing_heading_raises():
    with pytest.raises(ValueError):
        split_citation_section("no sources here https://a.id")

def test_load_answers_real_file():
    df = load_answers(ROOT/"data/raw/geo-bank-research.xlsx", ROOT/"data/raw/chatgpt-prompt08-rerun.md")
    assert len(df) == 40 and df.answer_id.is_unique
    assert "Laporan Tahunan" in df.set_index("answer_id").loc["gpt-08", "answer_raw"]
    assert not df.answer_raw.str.contains("\r").any()
    assert (df.run_date == "2026-10-09").all()
```

- [ ] **Step 2:** Run `pytest tests/test_parse_answers.py -v`. Expected: FAIL (module not found).
- [ ] **Step 3:** Implement `scripts/io.py` and the three functions above in `scripts/parse.py`. `HEADING_RE` must allow trailing `\r` and whitespace.
- [ ] **Step 4:** Run `pytest -v`. Expected: 4 passed.
- [ ] **Step 5:** Add `ci.yml` (checkout, setup-python 3.11 with pip cache, `pip install -r requirements.txt`, `pytest -q`). Commit `feat: scaffold and answers table` and push; check the CI run is green with `gh run list -R rgmwnn/geo-bank-visibility -L 1`.

### Task 2: Citations table

**Files:**
- Modify: `scripts/parse.py`
- Test: `tests/test_citations.py`

**Interfaces:**
- Consumes: `load_answers`, `split_citation_section`
- Produces:
  - `normalize_url(url: str) -> str` (spec steps 2 to 4; returns `scheme://host/path?query`, host lowercased without `www.`, trailing `/` dropped, `utm_*` removed)
  - `domain_of(url: str) -> str`
  - `extract_citations(section: str) -> list[tuple[str, str]]` returns `(url_raw, url)` in list order, first URL per line, deduped by normalized URL
  - `build_citations(answers: pd.DataFrame) -> pd.DataFrame` columns `answer_id, engine, rank, url_raw, url, domain`
  - `main() -> None` writes `data/interim/answers.csv` (adds `answer_body` column, drops nothing) and `data/interim/citations.csv`; asserts counts against `expected_counts`, raising `AssertionError` with expected vs actual.

- [ ] **Step 1: Write failing tests**

```python
def test_unwrap_google_redirect():
    assert normalize_url("https://www.google.com/search?q=https://www.bca.co.id/id/x") == "https://bca.co.id/id/x"

def test_label_real_href_redirect_and_reverse():
    a = "1. [https://www.ojk.go.id/p](https://www.google.com/search?q=https://www.ojk.go.id/p)"
    b = "1. [https://www.google.com/search?q=https://www.ojk.go.id/p](https://www.ojk.go.id/p)"
    assert extract_citations(a)[0][1] == extract_citations(b)[0][1] == "https://ojk.go.id/p"

def test_utm_and_trailing_slash():
    assert normalize_url("https://www.jago.com/id/?utm_source=chatgpt.com&x=1") == "https://jago.com/id?x=1"

def test_duplicate_within_answer_kept_once():
    sec = "1. [https://blubybcadigital.id/info/fees-rates](x)\n2. [https://blubybcadigital.id/info/fees-rates/](y)"
    assert len(extract_citations(sec)) == 1

def test_real_counts():
    main()
    c = read_csv("data/interim/citations.csv")
    assert (len(c), c.url.nunique(), c.domain.nunique()) == (399, 241, 99)
    assert c.groupby("answer_id").size().drop("gpt-02").eq(10).all()
```

- [ ] **Step 2:** Run `pytest tests/test_citations.py -v`. Expected: FAIL.
- [ ] **Step 3:** Implement. For a line with several URLs, unwrap each and take the first that is not a Google redirect after unwrapping (they normalize to the same URL, so either order works).
- [ ] **Step 4:** Run `pytest -v`. Expected: all pass.
- [ ] **Step 5:** Commit `feat: citations table with URL normalization` (include generated CSVs).

### Task 3: Sentences table

**Files:**
- Create: `scripts/sentences.py`
- Test: `tests/test_sentences.py`

**Interfaces:**
- Consumes: `data/interim/answers.csv`
- Produces:
  - `clean_body(body: str) -> str`
  - `split_sentences(clean: str) -> list[str]`
  - `main() -> None` writes `data/interim/sentences.csv` columns `answer_id, sent_idx, text, n_words` (`n_words` = whitespace tokens)

- [ ] **Step 1: Write failing tests**

```python
CHIP = "Teks pertama.\n\n![](https://www.google.com/s2/favicons?domain=x)\n\nNEXT Indonesia Center\n\n+1\n\nAdd to Favorites\n\nTeks kedua."
def test_chip_artifacts_removed():
    assert split_sentences(clean_body(CHIP)) == ["Teks pertama.", "Teks kedua."]

def test_decimals_currency_abbrev_not_split():
    s = split_sentences("Bunga 6,5% p.a. untuk saldo Rp2.000.000. PT Bank Central Asia Tbk. menawarkan ini. No. 3 juga.")
    assert s == ["Bunga 6,5% p.a. untuk saldo Rp2.000.000.", "PT Bank Central Asia Tbk. menawarkan ini.", "No. 3 juga."]

def test_list_items_and_table_rows_are_sentences():
    md = "* **SeaBank:** bunga 3,5%\n* Jago: gratis\n\n| Bank | Bunga |\n| --- | --- |\n| Krom | 7% |"
    assert split_sentences(clean_body(md)) == ["SeaBank: bunga 3,5%", "Jago: gratis", "Bank Bunga", "Krom 7%"]

def test_link_text_kept_hr_dropped():
    assert split_sentences(clean_body("Cek [situs LPS](https://lps.go.id).\n\n---\n\nSelesai.")) == ["Cek situs LPS.", "Selesai."]

def test_real_file_every_answer_has_sentences():
    main(); s = read_csv("data/interim/sentences.csv")
    assert s.answer_id.nunique() == 40 and (s.n_words > 0).all()
    assert not s.text.str.contains(r"^\+\d+$|Add to Favorites|images\.openai\.com").any()
```

- [ ] **Step 2:** Run tests. Expected: FAIL.
- [ ] **Step 3:** Implement. Table separator rows (`|---|`) are dropped; a table row's cells are joined with single spaces. Chip source-name rule: a line of ≤4 words directly after a removed favicon line is removed.
- [ ] **Step 4:** Run `pytest -v`. Expected: all pass. Print 3 random answers' sentences and eyeball them; fix rules if any sentence is clearly mis-split, adding a test for it.
- [ ] **Step 5:** Commit `feat: sentence cleaning and splitting`.

### Task 4: Brand dictionary and mentions

**Files:**
- Create: `config/brands.yaml`, `scripts/brands.py`, `data/labels/ambiguous_hits.csv`
- Test: `tests/test_brands.py`

**Interfaces:**
- Consumes: `data/interim/sentences.csv`
- Produces:
  - `@dataclass Brand: brand: str, parent: str | None, type: str, aliases: list[str], case_sensitive: bool, ambiguous: bool, ambiguous_aliases: list[str]` (`ambiguous` is true when `ambiguous_aliases` is non-empty; YAML may omit it)
  - `load_brands(path: Path) -> list[Brand]`
  - `find_matches(text: str, brands: list[Brand], unambiguous_only: bool = False) -> list[Match]` where `Match(brand: Brand, alias: str, start: int, end: int)`; whole-word, longest alias wins on overlap; when `unambiguous_only`, aliases flagged ambiguous are skipped (an alias is ambiguous if listed under the entry's `ambiguous_aliases` key; the entry-level `ambiguous: true` means it has at least one)
  - `credit(b: Brand) -> tuple[str, str]` returns `(parent or brand, brand if parent else "")`
  - `main() -> None` writes `data/interim/mentions.csv` (`answer_id, sent_idx, brand, sub_brand, alias_matched, char_pos`) using only ambiguous hits marked `keep` in `data/labels/ambiguous_hits.csv`, and appends any new unreviewed ambiguous hits to that file with `decision` empty, then raises `SystemExit("review ambiguous hits")` if any are empty.

YAML entry shape (note `ambiguous_aliases` subset):
```yaml
- brand: Bank Jago
  parent: null
  type: digital
  aliases: [Bank Jago, Jago Syariah, Jago]
  ambiguous_aliases: [Jago]
  case_sensitive: true
```

- [ ] **Step 1: Write failing tests**

```python
B = [Brand("BCA", None, "conventional", ["BCA", "Bank Central Asia"], True, False, []),
     Brand("blu", "BCA", "digital", ["blu by BCA Digital", "BCA Digital", "blu"], True, True, ["blu"]),
     Brand("Bank Jago", None, "digital", ["Bank Jago", "Jago"], True, True, ["Jago"])]

def test_longest_alias_and_rollup():
    m = find_matches("Buka blu by BCA Digital sekarang.", B)
    assert [credit(x.brand) for x in m] == [("BCA", "blu")]

def test_parent_and_sub_in_one_sentence_two_mentions():
    assert len(find_matches("BCA dan blu sama-sama bagus.", B)) == 2

def test_lowercase_jago_is_not_a_bank():
    assert find_matches("Dia jago masak.", B) == []

def test_case_sensitive_acronym():
    assert find_matches("bca", B) == [] and len(find_matches("BCA", B)) == 1

def test_unambiguous_only_skips_bare_jago():
    assert find_matches("Jago itu", B, unambiguous_only=True) == []
    assert len(find_matches("Bank Jago itu", B, unambiguous_only=True)) == 1
```

- [ ] **Step 2:** Run tests. Expected: FAIL.
- [ ] **Step 3:** Implement `scripts/brands.py`.
- [ ] **Step 4:** **Labelling (Claude):** build `config/brands.yaml` by reading all 40 answers' sentences. Include every bank named (conventional, digital, sharia, regional). Subsidiaries carry `parent`. Then run `python -m scripts.brands`, review every ambiguous hit in context, and set `decision` to `keep` or `reject` with a short `note`. Rerun until it writes `mentions.csv`.
- [ ] **Step 5:** Add the label-validation test:

```python
def test_brands_yaml_valid_and_all_review_done():
    bs = load_brands(ROOT/"config/brands.yaml")
    names = {b.brand for b in bs}
    assert all(b.parent in names for b in bs if b.parent)
    assert all(set(b.ambiguous_aliases) <= set(b.aliases) for b in bs)
    h = read_csv("data/labels/ambiguous_hits.csv")
    assert h.decision.isin(["keep", "reject"]).all()
```

- [ ] **Step 6:** Run `pytest -v`. Expected: all pass. Post the brand list (brand, parent, mention count) in chat for RG; apply any changes he asks for.
- [ ] **Step 7:** Commit `feat: brand dictionary and mentions`.

### Task 5: Offline page derivation

**Files:**
- Create: `scripts/derive.py`, `config/stopwords.txt`, `tests/fixtures/article.html`, `tests/fixtures/consent.html`, `tests/fixtures/report.pdf` (2 pages of invented text, generated once by `tests/fixtures/make_pdf.py` using `fpdf2`, which goes in `requirements.txt`)
- Test: `tests/test_derive.py`

**Interfaces:**
- Consumes: `Brand`, `find_matches(unambiguous_only=True)`, `credit`
- Produces:
  - `extract_html(html: str, url: str) -> dict` keys `title, text, n_words, published_date, date_source, schema_types` (list), using trafilatura for text, BeautifulSoup for JSON-LD (`@type`, `datePublished`, including inside `@graph`) and `meta[property=article:published_time]`, then `htmldate.find_date(html, original_date=True)`; dates as `YYYY-MM-DD`
  - `extract_pdf(data: bytes, max_pages: int) -> dict` keys `text, n_words, n_pages`
  - `page_row(meta: dict, extracted: dict, min_words: int) -> dict` builds one `pages.csv` row (`is_readable = http_status == 200 and n_words >= min_words`; `has_article_schema` true for Article/NewsArticle/BlogPosting; `has_faq_schema` for FAQPage; `has_org_schema` for Organization/BankOrCreditUnion/FinancialService)
  - `brand_counts(text: str, brands) -> list[dict]` rows `brand, count, first_pos_ratio` credited to parent
  - `tokens(text: str, stop: set[str]) -> list[str]` (lowercase, `[a-z0-9]+` after replacing `,` and `.` inside numbers with nothing)
  - `overlap(sentence: str, page_text: str, stop) -> float` (bigram share; unigram share when the sentence has <3 content tokens; 0.0 for empty)
  - `attribution_scores(sentences: pd.DataFrame, citations: pd.DataFrame, page_texts: dict[str, str]) -> pd.DataFrame` columns `answer_id, sent_idx, best_url, best_score, second_url, second_score`; candidates are that answer's cited URLs present in `page_texts`; ties go to lower `rank`

- [ ] **Step 1: Write failing tests**

```python
def test_html_fields():
    d = extract_html((FIX/"article.html").read_text(), "https://news.example.id/a")
    assert d["published_date"] == "2026-08-07" and d["date_source"] == "jsonld"
    assert "NewsArticle" in d["schema_types"] and d["n_words"] >= 50

def test_consent_wall_not_readable():
    d = extract_html((FIX/"consent.html").read_text(), "https://bank.example.id")
    row = page_row({"url": "u", "final_url": "u", "http_status": 200, "fetch_error": "", "content_kind": "html"}, d, 50)
    assert row["is_readable"] is False

def test_pdf_text():
    d = extract_pdf((FIX/"report.pdf").read_bytes(), 300)
    assert d["n_pages"] == 2 and d["n_words"] > 0

def test_overlap_and_attribution_tie_to_higher_rank():
    pages = {"https://a.id": "bunga tabungan seabank 3,5 persen per tahun tanpa saldo minimum",
             "https://b.id": "bunga tabungan seabank 3,5 persen per tahun tanpa saldo minimum"}
    sents = pd.DataFrame([{"answer_id": "x", "sent_idx": 0, "text": "SeaBank memberi bunga tabungan 3,5 persen per tahun."}])
    cits = pd.DataFrame([{"answer_id": "x", "rank": 2, "url": "https://a.id"}, {"answer_id": "x", "rank": 1, "url": "https://b.id"}])
    r = attribution_scores(sents, cits, pages).iloc[0]
    assert r.best_url == "https://b.id" and r.best_score > 0.5

def test_no_candidates_gives_empty_best():
    r = attribution_scores(pd.DataFrame([{"answer_id": "x", "sent_idx": 0, "text": "abc def ghi"}]),
                           pd.DataFrame([{"answer_id": "x", "rank": 1, "url": "https://a.id"}]), {}).iloc[0]
    assert pd.isna(r.best_url) and r.best_score == 0.0
```

- [ ] **Step 2:** Run tests. Expected: FAIL.
- [ ] **Step 3:** Write fixtures (invented text, no copied pages) and `config/stopwords.txt` (common Indonesian function words such as `yang, dan, di, ke, dari, untuk, dengan, ini, itu, atau, juga, adalah, pada, dalam, bisa, akan, lebih, tidak, ada, kamu, anda` plus common English ones; about 150 words). Implement `scripts/derive.py`.
- [ ] **Step 4:** Run `pytest -v`. Expected: all pass.
- [ ] **Step 5:** Commit `feat: offline page derivation and attribution scoring`.

### Task 6: Crawl workflow and first run

**Files:**
- Create: `scripts/crawl.py`, `.github/workflows/crawl.yml`
- Test: `tests/test_crawl.py` (offline parts only)

**Interfaces:**
- Consumes: `data/interim/citations.csv`, `derive.*`, `config/brands.yaml`
- Produces:
  - `scripts.crawl.fetch_all(urls: list[str], cache: Path, delay: float, timeout: int) -> None` writes `cache/<sha1(url)>.bin` and `.json` (`url, final_url, http_status, fetch_error, content_type, content_kind, fetched_at`); robots-disallowed URLs get `http_status` empty and `fetch_error = "robots_disallowed"` with no `.bin`
  - `scripts.derive.main(cache: Path) -> None` writes `data/interim/pages.csv`, `page_brand_counts.csv`, `attribution_scores.csv`
  - Workflow `crawl.yml`: `on: workflow_dispatch` and `push` with `paths: [crawl/request.txt]`; `permissions: contents: write`; steps: checkout, python 3.11, install, `python -m scripts.crawl`, `python -m scripts.derive`, upload `.cache/` as artifact `crawl-cache` (retention 90 days), commit the three CSVs as `github-actions[bot]` with message `data: crawl results <UTC timestamp>` and push.

- [ ] **Step 1: Write failing tests**

```python
def test_content_kind():
    assert content_kind("application/pdf", "https://x/a") == "pdf"
    assert content_kind("text/html; charset=utf-8", "https://x/a") == "html"
    assert content_kind("", "https://x/a.PDF") == "pdf"

def test_per_domain_delay_scheduler():
    order = schedule(["https://a.id/1", "https://a.id/2", "https://b.id/1"])
    assert order[0][0] != order[1][0]  # interleaves domains so gaps overlap
```

- [ ] **Step 2:** Run tests. Expected: FAIL.
- [ ] **Step 3:** Implement `content_kind(content_type: str, url: str) -> str`, `schedule(urls) -> list[tuple[str, str]]` (domain, url round-robin), `fetch_all`, and the workflow. Use `requests.Session` with the user agent from Global Constraints and `urllib.robotparser` per host (a robots fetch failure means allowed).
- [ ] **Step 4:** Run `pytest -v`. Expected: all pass. Commit `feat: crawl workflow`, push.
- [ ] **Step 5:** Trigger: `gh workflow run crawl.yml -R rgmwnn/geo-bank-visibility`. If dispatch is refused, write the UTC time into `crawl/request.txt`, commit and push. Wait with `gh run watch -R rgmwnn/geo-bank-visibility <run-id>`.
- [ ] **Step 6:** `git pull`. Verify: `pages.csv` has 241 rows; every row has either `http_status` or `fetch_error`; print counts by status and `is_readable`. If more than 25% are unreadable, open `superpowers:systematic-debugging` before going further and report the cause in chat.

### Task 7: Attribution threshold check

**Files:**
- Create: `data/labels/attribution_check.csv`
- Modify: `scripts/derive.py` (add `threshold_agreement`)
- Test: `tests/test_attribution_check.py`

**Interfaces:**
- Consumes: `attribution_scores.csv`, `pages.csv` (titles)
- Produces: `threshold_agreement(scores: pd.DataFrame, labels: pd.DataFrame, t: float) -> int` counts labelled sentences where (`best_score >= t` and `best_url == expected_url`) or (`best_score < t` and `expected_url` is `none`)

- [ ] **Step 1:** **Labelling (Claude):** pick 30 sentences with a fixed seed (15 per engine, `random_state=7`) from sentences with at least 8 words. For each, record `expected_url` (one of that answer's cited URLs whose title and URL best match the sentence's claim, or `none`) and a one-line `note`. Do this before looking at `attribution_scores.csv`.
- [ ] **Step 2: Write failing test**

```python
def test_threshold_meets_bar():
    cfg = load_config()
    n = threshold_agreement(read_csv("data/interim/attribution_scores.csv"),
                            read_csv("data/labels/attribution_check.csv"), cfg["attribution_threshold"])
    assert n >= cfg["attribution_min_agreement"]
```

- [ ] **Step 3:** Implement `threshold_agreement`. Run the test.
- [ ] **Step 4:** If it fails, compute agreement for t in 0.15 to 0.50 step 0.05, set `attribution_threshold` to the best value, and record the full table for the quality report. If no threshold reaches 24/30, keep the best one, mark the test `xfail` with the real number, and say so in chat and in `docs/data-quality.md`.
- [ ] **Step 5:** Commit `data: attribution threshold check`.

### Task 8: Domain and sentiment labels

**Files:**
- Create: `config/domains.csv`, `data/labels/sentiment.csv`
- Test: `tests/test_labels.py`

**Interfaces:**
- Consumes: `citations.csv`, `mentions.csv`, `sentences.csv`
- Produces: the two label files with columns from the spec (`domain, domain_type, authority_tier, note`; `answer_id, brand, label, score, evidence, reason`)

- [ ] **Step 1: Write failing tests**

```python
TYPES = {"regulator","bank_official","news_media","fintech_platform","blog_aggregator","forum_ugc","app_store","other"}
def test_every_domain_labelled():
    d = read_csv("config/domains.csv"); c = read_csv("data/interim/citations.csv")
    assert set(c.domain) <= set(d.domain) and d.domain_type.isin(TYPES).all()
    assert d.authority_tier.isin(["High","Medium","Low"]).all()
    assert (d[d.domain_type == "other"].note.str.len() > 0).all()

def test_every_answer_brand_has_sentiment():
    m = read_csv("data/interim/mentions.csv"); s = read_csv("data/labels/sentiment.csv")
    assert set(map(tuple, m[["answer_id","brand"]].drop_duplicates().values)) == set(map(tuple, s[["answer_id","brand"]].values))
    assert s.label.isin(["positive","neutral","negative","mixed"]).all()
    assert (s.score == s.label.map({"positive":1,"neutral":0,"negative":-1,"mixed":0})).all()
```

- [ ] **Step 2:** Run tests. Expected: FAIL (files missing).
- [ ] **Step 3:** **Labelling (Claude):** label all 99 domains using the spec's type table (subdomains of `go.id` regulators → `regulator`). Label sentiment per answer × parent brand, reading that answer's sentences that mention the brand; `evidence` is the `sent_idx` list joined with `;`.
- [ ] **Step 4:** Run tests. Expected: pass.
- [ ] **Step 5:** Pick 4 answers (2 per engine, `random_state=11`), post their sentiment labels with the evidence sentences in chat for RG to confirm, and record the result (agreed, changed, or not checked) in `data/labels/sentiment_spotcheck.csv`. Commit `data: domain and sentiment labels`.

### Task 9: Metrics

**Files:**
- Create: `scripts/metrics.py`, `tests/fixtures/mini/` (6-answer fixture CSVs: answers, sentences, mentions, citations, pages, page_brand_counts, attribution_scores, domains, sentiment)
- Test: `tests/test_metrics.py`

**Interfaces:**
- Consumes: all interim and label files, `config/metrics.yaml`
- Produces: `brand_engine` / `brand_pillar` / `brand_intent` rows have columns `brand, <cut>, n, mention_rate, ai_sov, pawc, first_mention_pos, sentiment_mean, n_pos, n_neu, n_neg, n_mixed` (plus `diversity` on the overall `vis` table). `pawc_weight(sent_idx: int, n_sents: int) -> float`; `brand_pawc(sentences, mentions) -> DataFrame[answer_id, brand, pawc]` (0 rows for absent brands are added at aggregation); `compute_all(inputs: dict[str, DataFrame], cfg: dict) -> dict[str, DataFrame]` with keys `brand_engine, brand_pillar, brand_intent, no_brand_rate, domains, pages_top, cross_engine_pages, domain_type_mix, authority_mix, concentration, source_pawc_domain, attribution_coverage, source_sov, readability, recency, schema, vis, vis_engine`; `main() -> None` writes each as `data/processed/<key>.csv` and `.json` (records orient).

- [ ] **Step 1: Write failing tests** against the mini fixture, with values computed by hand in comments:

```python
def test_pawc_weight():
    assert pawc_weight(0, 4) == 1.0 and round(pawc_weight(2, 4), 4) == round(math.exp(-0.5), 4)

def test_brand_pawc_hand_value():
    # 4 sentences, words [10,10,10,10]; brand in sentences 0 and 2
    # (10*1 + 10*e^-0.5) / 40 = 0.4016
    assert round(brand_pawc(SENTS4, MENT4).set_index("brand").loc["BCA","pawc"], 4) == 0.4016

def test_mention_rate_sov_and_n(): ...      # exact values for the mini fixture, n == 3 per engine
def test_domains_and_pages_top(): ...       # citations, unique pages, prompts, gpt/gem split, avg rank
def test_source_pawc_uses_threshold(): ...  # a sentence with score below threshold contributes 0
def test_brand_only_in_pages_kept():
    sov = compute_all(MINI, CFG)["source_sov"].set_index("brand")
    assert sov.loc["Krom", "ai_sov"] == 0 and sov.loc["Krom", "sov_gap"] < 0
def test_vis_equal_weights_and_low_n(): ... # hand value; brand in 1 answer has low_n True
def test_unreadable_pages_excluded_everywhere(): ...  # unreadable page adds nothing to source_sov or source_pawc
```

Each `...` test must assert exact numbers worked out by hand from the fixture and written as comments above the assertion.

- [ ] **Step 2:** Run tests. Expected: FAIL.
- [ ] **Step 3:** Implement following the spec's Step 5 tables exactly. Recency groups use `run_date` minus `published_date` with bins from config and an `unknown` group.
- [ ] **Step 4:** Run `pytest -v`. Expected: all pass. Run `python -m scripts.metrics` on the real data.
- [ ] **Step 5:** Sanity check against the earlier preview: top domains by citations start `seabank.co.id 38, jago.com 35, ojk.go.id 30`, and the top page is the akulaku comparison blog with 14. A mismatch means a bug, not a new finding.
- [ ] **Step 6:** Commit `feat: metrics` with processed outputs.

### Task 10: Quality report, runner and README

**Files:**
- Create: `scripts/quality.py`, `scripts/run_all.py`, `README.md`, `docs/data-quality.md` (generated)
- Test: `tests/test_quality.py`

**Interfaces:**
- Consumes: everything above
- Produces: `quality.build_report() -> str` (markdown) and `main()` writing `docs/data-quality.md`; `run_all.main()` runs parse → sentences → brands → derive-free metrics → quality, skipping crawl.

- [ ] **Step 1: Write failing test**

```python
def test_report_sections():
    r = build_report()
    for h in ["## Counts", "## Citations per answer", "## Crawl outcomes", "## Attribution check",
              "## Ambiguous brand hits", "## Sentiment spot-check", "## Known limitations"]:
        assert h in r
    assert "—" not in r and "–" not in r
```

- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement. Every unreadable URL is listed with its status. Limitations copy the spec's Section 6 points in plain words.
- [ ] **Step 4:** Write `README.md`: what the project measures, the 40-answer dataset, how to rerun (`pip install -r requirements.txt && python -m scripts.run_all`; crawl via the workflow), metric definitions table, limitations link. Load `antislop:antislop-copywriting` and run its checklist on README and the report.
- [ ] **Step 5:** Run `python -m scripts.run_all && pytest -q`. Expected: all pass, `git status` shows no changes to processed files (the pipeline is deterministic).
- [ ] **Step 6:** Commit `docs: data-quality report and README`, push, confirm CI green.

### Task 11: Final verification

- [ ] **Step 1:** Load `superpowers:verification-before-completion`. Fresh clone into `/tmp`, install, `python -m scripts.run_all`, `pytest -q`. Expected: green, identical processed outputs (`git diff --stat` empty).
- [ ] **Step 2:** `grep -rIl "<html\|%PDF" data/ config/` returns nothing (no page bodies committed). `grep -rn "sk-\|api_key\|OPENAI" .` returns nothing.
- [ ] **Step 3:** Request a whole-branch review with `superpowers:requesting-code-review`, fix findings, and post a short summary in chat: headline numbers, crawl readability, attribution agreement, anything left open.

# Favoured Banks Deck Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A 32-slide deck of the GEO findings, built from the repo data, imported into RG's Canva account as an editable presentation, plus a PDF export.

**Architecture:** `deck/facts.py` computes every number a slide shows from the repo files. `deck/charts.py` renders each chart to PNG from those facts. `deck/build.py` assembles an editable `.pptx` with python-pptx. LibreOffice renders the file for visual checks, then the file is pushed to the public `deck` branch and imported into Canva with the connector, where pages are read back and repaired.

**Tech Stack:** Python 3.11, pandas, matplotlib, python-pptx, LibreOffice (headless render), Canva MCP (`import-design-from-url`, `read-design`, `edit-design`, `export-design`).

**Spec:** `docs/superpowers/specs/2026-10-09-favoured-banks-deck-design.md`

## Global Constraints

- Canvas 1920 x 1080 px (13.333 x 7.5 in). Letterbox band for evidence slides: 2.39:1, so bars of 138 px top and bottom.
- Palette: background `#0B0C0E`, bars `#000000`, text `#ECE7DD`, secondary `#9A9EA6`, dim `#3A3D43`, ChatGPT `#D07A28`, Gemini `#4790D8`. No other colours.
- Fonts: Work Sans (titles, body), IBM Plex Mono (data labels, slate). Nothing else.
- Slate line on evidence slides: `09.10.2026 · 40 ANSWERS · SCENE NN`.
- ChatGPT is always ember, Gemini always steel blue.
- Every chart footnote names its source file and N.
- Copy: no em dash or en dash, no hype words, hedged wording kept as in the findings doc. Removed points stay out: Source PAWC, "size does not buy AI visibility", the bank-assets finding.
- Charts saved at 2x (3840 px wide for a full-width chart).

## Review Focus

1. **Font substitution on Canva import.** If Canva replaces Work Sans or IBM Plex Mono, lines reflow and overlap. Read back every page after import and compare with the local render (Task 6).
2. **Text overflow at long Indonesian prompts.** Slide 2 and slide 6 show full prompts; the longest is 128 characters. Test that every text box's estimated line count fits its height (Task 4).
3. **Numbers drifting from data.** A hard-coded number in copy can disagree with the CSVs. All slide numbers are formatted from `facts`, and a test greps the built deck for digits not present in `facts` (Task 4).
4. **Contrast on dark ground.** Secondary grey and dim marks used for text must still pass WCAG AA. Tested in Task 2.
5. **Low-sample banks read as rankings.** Banks in fewer than 3 answers are marked `low n` wherever they appear in a ranked chart (Task 3).

---

### Task 1: Facts

**Files:**
- Create: `deck/__init__.py`, `deck/facts.py`
- Test: `tests/test_deck_facts.py`

**Interfaces:**
- Produces: `deck.facts.load() -> dict` with keys used by later tasks: `answers`, `sentences`, `mentions`, `citations`, `pages`, `readable_pages`, `banks_gpt`, `banks_gem`, `mention_rate` (dict brand -> {"ChatGPT","Gemini","All"}), `vis` (DataFrame brand, vis, low_n), `pillar_leaders`, `sentiment_counts`, `intent_named_share`, `source_mix` (engine -> type -> share), `overlap` (sites_both, sites_total, pages_both, pages_total, jaccard_sites, jaccard_pages), `top_sites` (DataFrame domain, gpt, gem), `top_pages`, `concentration`, `sov_gap` (DataFrame brand, ai_sov_weighted, source_sov, sov_gap), `dead_links` (wrapped_dead, wrapped_total, direct_dead, direct_total), `schema_by_type`, `dated_citations`, `readable_citations`, `cold_open` (prompt, english, banks_gpt, banks_gem), `prompt_grid`.

- [ ] **Step 1: Write the failing test** `test_known_counts`: asserts `answers == 40`, `sentences == 857`, `mentions == 427`, `citations == 399`, `pages == 243`, `readable_pages == 195`, `banks_gpt == 11`, `banks_gem == 18`, `sentiment_counts == {"positive": 117, "neutral": 14, "mixed": 6, "negative": 0}`, `dead_links == (13, 21, 0, 179)`, `overlap["sites_both"] == 21`, `overlap["pages_both"] == 11`, `round(mention_rate["BCA"]["All"], 3) == 0.55`.
- [ ] **Step 2:** Run `pytest tests/test_deck_facts.py -v`. Expected: FAIL (module not found).
- [ ] **Step 3:** Implement `load()` reading only `data/interim`, `data/labels`, `data/processed`. Dead links: a Gemini citation is "wrapped" when its raw link line contains `google.com/search`; dead means the page has HTTP 404 or `soft_404`. Cold open uses prompt 13 (decision brief), with an English line written in `facts.py`.
- [ ] **Step 4:** Run the test. Expected: PASS. If a known count differs, the data is the truth: stop and report the difference before changing the expected value.
- [ ] **Step 5:** Commit `feat(deck): facts computed from repo data`.

### Task 2: Theme and contrast

**Files:**
- Create: `deck/theme.py`, `deck/fonts/` (WorkSans-Regular/Bold, IBMPlexMono-Regular/Bold TTF, OFL texts)
- Test: `tests/test_deck_theme.py`

**Interfaces:**
- Produces: `deck.theme.C` (dict of the seven palette colours by role name), `deck.theme.SANS = "Work Sans"`, `deck.theme.MONO = "IBM Plex Mono"`, `deck.theme.contrast(fg_hex, bg_hex) -> float`, `deck.theme.register_fonts() -> None` (adds the TTFs to matplotlib).

- [ ] **Step 1: Write the failing test** `test_text_pairs_pass_aa`: `contrast(C["text"], C["bg"]) >= 4.5`, `contrast(C["secondary"], C["bg"]) >= 4.5`, `contrast(C["secondary"], C["bar"]) >= 4.5`, `contrast(C["gpt"], C["bg"]) >= 4.5`, `contrast(C["gem"], C["bg"]) >= 4.5`, and `contrast(C["dim"], C["bg"]) >= 1.5` (dim is for marks only, never text).
- [ ] **Step 2:** Run it. Expected: FAIL.
- [ ] **Step 3:** Implement with the WCAG 2.1 relative-luminance formula. Copy fonts from the canvas-design font folder; install them to `~/.fonts` for LibreOffice.
- [ ] **Step 4:** Run it. Expected: PASS. If a colour fails, adjust its lightness only, keep its hue, and update the spec table.
- [ ] **Step 5:** Commit `feat(deck): theme, fonts and contrast checks`.

### Task 3: Charts

**Files:**
- Create: `deck/charts.py`
- Test: `tests/test_deck_charts.py`

**Interfaces:**
- Consumes: `facts.load()`, `theme.C`, `theme.register_fonts()`
- Produces: `deck.charts.render_all(facts: dict, out: Path) -> dict[str, Path]` with these keys: `pawc_curve`, `prompt_grid`, `pipeline`, `funnel`, `mention_dots`, `vis_rank`, `wider_field`, `pillar_heatmap`, `often_vs_early`, `sentiment_marks`, `intent_named`, `source_mix`, `overlap`, `mirror_sites`, `top_pages`, `concentration`, `sov_gap`, `dead_links`, `schema`.

Chart rules: background `C["bg"]`, one lit element per chart in bone or the engine colour, everything else `C["dim"]`/`C["secondary"]`, direct labels in IBM Plex Mono, no legend box, footnote text left to the slide (charts carry no title).

- [ ] **Step 1: Write the failing test** `test_render_all_outputs`: every key above exists, each PNG opens, width >= 1600 px, and `vis_rank` and `mention_dots` source data mark every bank with `n_answers < 3` as low n (assert on the DataFrame passed to the chart, exposed as `charts.LAST_DATA["vis_rank"]`).
- [ ] **Step 2:** Run it. Expected: FAIL.
- [ ] **Step 3:** Implement one function per chart, each `def chart_<key>(f: dict, path: Path) -> Path`.
- [ ] **Step 4:** Run it. Expected: PASS. Then open every PNG and look at it: one focal mark, labels not clipped, no overlap. Fix and repeat until all pass by eye.
- [ ] **Step 5:** Commit `feat(deck): charts from data`.

### Task 4: Slides

**Files:**
- Create: `deck/build.py`, `deck/copy.py` (slide copy as functions of `facts`), `deck/design-philosophy.md`
- Test: `tests/test_deck_build.py`

**Interfaces:**
- Consumes: `facts.load()`, `charts.render_all()`, `theme`
- Produces: `deck.build.build(out: Path) -> Path` writing `deck/out/favoured-banks.pptx`; `deck.copy.SLIDES` (list of 32 dicts: `kind` in {"full","letterbox","title_card"}, `title`, `body`, `chart`, `footnote`, `notes`).

- [ ] **Step 1: Write the failing tests:**
  - `test_slide_count_and_kinds`: 32 slides; title cards at positions 5, 10, 18, 27.
  - `test_no_dashes_or_hype`: no `—` or `–` and none of `seamless, revolutionary, cutting edge, next generation, powerful, leverage, unlock` in any slide text or notes.
  - `test_fonts_only_sans_and_mono`: every run's font name is `Work Sans` or `IBM Plex Mono`.
  - `test_numbers_come_from_facts`: every number token in slide text (excluding the date `09.10.2026`, scene numbers and year mentions) appears in a set built from formatting `facts` values.
  - `test_text_fits`: for each text box, estimated lines (chars per line from box width and font size, 0.52 em average glyph width) times line height fit the box height.
  - `test_letterbox_slides_have_slate`: every letterbox slide has the slate text with its own scene number.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Write `design-philosophy.md` (canvas-design step one), then implement `copy.py` from the findings doc and `build.py` with helpers `frame(slide, kind)`, `slate(slide, n)`, `text(slide, box, runs)`, `image(slide, path, box)`, `notes(slide, text)`.
- [ ] **Step 4:** Run them. Expected: PASS.
- [ ] **Step 5:** Commit `feat(deck): editable pptx`.

### Task 5: Local render check

**Files:**
- Create: `deck/render.sh` (pptx to PDF with `soffice --headless`, PDF to PNG per page with `pdftoppm -r 60`)

- [ ] **Step 1:** Run `bash deck/render.sh`. Expected: 32 PNGs in `deck/out/render/`.
- [ ] **Step 2:** Look at every page. Record each defect (overlap, clipping, wrong font, empty space that reads as a mistake) in `deck/out/qa.md`, fix in code, re-run Tasks 4 and 5 until `qa.md` has no open item.
- [ ] **Step 3:** Commit `chore(deck): local render pass` (render PNGs are not committed; `deck/out/render/` goes in `.gitignore`; the `.pptx` is committed for the import).

### Task 6: Canva import and repair

- [ ] **Step 1:** Push the `deck` branch. Raw URL: `https://raw.githubusercontent.com/rgmwnn/geo-bank-visibility/deck/deck/out/favoured-banks.pptx`.
- [ ] **Step 2:** `import-design-from-url` with that URL, name `Favoured Banks in ChatGPT and Gemini`, type `presentation`. Expected: a design_id.
- [ ] **Step 3:** `read-design` with thumbnails for all pages. Compare each with the local render. List differences (fonts, bar positions, chart crops, notes).
- [ ] **Step 4:** Fix what the import broke: in the `.pptx` when the cause is the file (then re-import), or with `edit-design` on the Canva design when it is a Canva-side change. Show RG the previews and save Canva edits only after his approval.
- [ ] **Step 5:** `export-design` as PDF and keep the Canva link.

### Task 7: Delivery gate

- [ ] **Step 1:** Run the antislop Delivery Gate on the Canva deck (copy, contrast, purpose of each technique, dials, identity motif) and write the report to `anti-slop/deck-gate-2026-10-09.md`.
- [ ] **Step 2:** Request a whole-branch review with superpowers:requesting-code-review; fix findings.
- [ ] **Step 3:** Report to RG: Canva link, PDF, the gate report, and anything left open.

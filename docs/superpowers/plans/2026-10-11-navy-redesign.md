# Navy Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the 33-slide Favoured Banks deck in the approved "Navy night" system (sample C) with futuristic Nolan line motifs, then place the tower photo in Canva.

**Architecture:** Same pipeline as before: `deck/theme.py` holds colours and fonts, `deck/charts.py` draws PNG charts, `deck/build.py` lays out python-pptx slides from `deck/copy.py`. The photo cannot be downloaded, so the .pptx carries named `photo-slot` shapes that Canva fills after import.

**Tech Stack:** Python 3, python-pptx, matplotlib, Pillow, fontTools, LibreOffice (render check), Canva MCP (import, update_fill, crop_media).

**Spec:** `docs/superpowers/specs/2026-10-11-navy-redesign-design.md`

## Global Constraints

- Ground #0F2747 on every slide; panels #0A1C36; no #000000 fill anywhere.
- Text #F4F6FA; secondary #AFC0D8; decorative lines #3B5A85; motif highlight #7FC0F5 at reduced weight.
- ChatGPT #F2A541, Gemini #7FC0F5. Amber appears only as ChatGPT data and the cover rule; single-series lit marks are white.
- Fonts: Plus Jakarta Sans (Regular, Bold) and IBM Plex Mono only.
- Content, numbers and copy unchanged except fitting text to layouts; audit 002 rules stay (no tracked caps, no middle-dot chains, no em dashes).
- Chart readability: smallest chart text at least 24 px on the slide; no clipped or overlapping chart labels.
- Every decorative shape is named `motif-*` and never crosses a text box.

## Review Focus

1. Plus Jakarta Sans has a different line pitch from Work Sans: wrapped text could overlap in Canva unless `measure.LINE` is re-measured from a LibreOffice render (Task 1 test).
2. Photo-slot stacking: the fade and corridor must sit above the slot or Canva's fill hides them (Task 3 test on shape order).
3. Text over the photo: every text box on the cover and title cards must sit inside the fade's fully opaque region, so contrast never depends on the photo (Task 3 test).
4. Amber leaking into single-series charts would read as ChatGPT (Task 2 pixel test).
5. Long section titles in the narrower title-card text column (Task 3 overlap test covers it).

---

### Task 1: Theme, fonts and text measurement

**Files:**
- Modify: `deck/theme.py`, `deck/measure.py`
- Create: `deck/fonts/PlusJakartaSans-Regular.ttf`, `deck/fonts/PlusJakartaSans-Bold.ttf`, `deck/fonts/PlusJakartaSans-OFL.txt` (from the npm @fontsource/plus-jakarta-sans package, woff converted with fontTools)
- Test: `tests/test_deck_theme.py`, `tests/test_deck_final_review.py::test_line_factor_covers_the_rendered_pitch`, `tests/test_deck_build.py::test_fonts_only_sans_and_mono`

**Interfaces:**
- Produces: `C` keys `bg`=#0F2747, `panel`=#0A1C36, `text`=#F4F6FA, `secondary`=#AFC0D8, `line`=#3B5A85, `glow`=#7FC0F5, `gpt`=#F2A541, `gem`=#7FC0F5; `SANS`="Plus Jakarta Sans"; `MONO`="IBM Plex Mono"; `measure.LINE` re-measured.

- [ ] **Step 1:** Rewrite theme tests: `test_text_pairs_pass_aa` (text and secondary ≥ 4.5 on bg and on panel), `test_engine_colours_are_the_navy_pair` (`(C["gpt"], C["gem"]) == ("#F2A541", "#7FC0F5")`, each ≥ 3.0 on bg), `test_no_black_in_palette` (no value == "#000000"). Update the pitch test to the Plus Jakarta Sans pitch measured from a LibreOffice render of a 3-line 22 pt paragraph (record the measured value and its provenance in the test comment).
- [ ] **Step 2:** Run `python3 -m pytest -q tests/test_deck_theme.py tests/test_deck_final_review.py -k "pairs or navy or black or pitch"`. Expected: FAIL.
- [ ] **Step 3:** Update `theme.py`, add font files, point `measure._font` at Plus Jakarta Sans, set `LINE` from the measured pitch with the same margin rule as before.
- [ ] **Step 4:** Same command. Expected: PASS.
- [ ] **Step 5:** Commit `feat(deck): navy theme and Plus Jakarta Sans`.

### Task 2: Charts on navy

**Files:**
- Modify: `deck/charts.py`
- Test: `tests/test_deck_charts.py`, `tests/test_deck_readable.py`

**Interfaces:**
- Consumes: Task 1 `C`, `SANS`, `MONO`.
- Produces: same `CHARTS` keys and `render_all(facts, out) -> dict[str, Path]`; `LAST_DATA` keys unchanged.

- [ ] **Step 1:** Add `test_single_series_charts_carry_no_amber`: for `vis_rank, intent_named, sov_gap, dead_links, schema, funnel, pawc_curve, pipeline, sentiment_marks, pillar_heatmap`, no pixel within distance 30 of #F2A541 in RGB with alpha > 0.
- [ ] **Step 2:** Run it. Expected: FAIL (old `gpt` is #D07A28; the test is written against the new colour, so it fails only after theme changes if a chart uses `gpt` for non-engine marks; if it passes immediately, confirm by temporarily colouring one lit mark amber and seeing it fail, then revert).
- [ ] **Step 3:** Recolour: grids and tracks `line`, lit marks `text`, unlit `secondary`, heatmap fill from `glow` at alpha 0.08 to 0.45, source-mix and engine charts keep `gpt`/`gem`. Body font SANS, numbers MONO.
- [ ] **Step 4:** Run `python3 -m pytest -q tests/test_deck_charts.py tests/test_deck_readable.py tests/test_deck_lines.py -k "chart or readable or bars or clipped"`. Expected: PASS.
- [ ] **Step 5:** Commit `feat(deck): charts recoloured for navy`.

### Task 3: Slide system and motifs

**Files:**
- Modify: `deck/build.py`
- Test: `tests/test_deck_lines.py` (rewritten for the navy system), `tests/test_deck_build.py` (band and slate tests replaced)

**Interfaces:**
- Consumes: Tasks 1 and 2.
- Produces: shapes named `photo-slot` (cover and 4 title cards), `motif-fade`, `motif-line-corridor-*`, `motif-line-depth-{i}-{side}`, `motif-bracket-*`, `motif-line-tick-NN`, `motif-gauge-{n}`, `motif-horizon`, `motif-line-rail`, `motif-line-stop-*`; chart pictures still `chart-<key>`.

- [ ] **Step 1:** Write tests:
  - `test_every_slide_is_navy`: every slide background is #0F2747 and no shape fill is #000000.
  - `test_photo_slots_sit_behind_fade_and_motifs`: slides 1, 5, 10, 18, 27 each have exactly one `photo-slot`, and its index in the shape tree is lower than every `motif-*` and text shape.
  - `test_photo_page_text_sits_on_the_opaque_fade`: on those slides every text box's right edge ≤ the fade's opaque edge (fade width minus ramp).
  - `test_title_cards_recede_one_more_frame_per_part` (kept, updated names).
  - `test_chart_panels_have_four_corner_brackets`: every slide with a `chart-*` picture has 4 `motif-bracket-*` shapes enclosing the picture.
  - `test_gauges_encode_their_values`: slide 3 has `motif-gauge-1` and `motif-gauge-2`; `build.GAUGES` records sweep degrees equal to 0.24×360 and 0.12×360 (±1).
  - Keep `test_no_motif_touches_text`, `test_text_boxes_never_overlap`, `test_lists_hang_on_a_rail`, `test_open_frames_have_a_horizon_below_all_text` (close only), ruler test (evidence slides, ticks below all text).
  - Replace the letterbox band test with `test_content_stays_inside_the_safe_area`: non-motif shapes within x 100 to 1820 and y 80 to 1000, footer excluded.
- [ ] **Step 2:** Run `python3 -m pytest -q tests/test_deck_lines.py tests/test_deck_build.py`. Expected: FAIL on the new tests.
- [ ] **Step 3:** Implement in `build.py`: navy `frame()`; `photo_slot(slide, box)`; `fade_png(width, ramp) -> Path`; cover as sample C; title cards with a per-part crop box for the slot, fade, then the corridor; `panel(slide, box)` with corner brackets; footer with source (MONO), page number and progress ruler; `gauge_png(value) -> Path` and `GAUGES` dict; horizon on close; lists keep the rail. Drop letterbox bars, the ring and the old slate.
- [ ] **Step 4:** Run the full suite `python3 -m pytest -q`. Expected: all pass.
- [ ] **Step 5:** Build and render (`python3 -m deck.build && bash deck/render.sh`), look at all 33 slides, fix what the eye finds with a test first. Commit `feat(deck): navy slide system with Nolan motifs`.

### Task 4: Canva import, photo and verification

**Files:**
- Modify: `anti-slop/deck-gate-2026-10-09.md`, `deck/out/qa.md`, `deck/design-philosophy.md`

- [ ] **Step 1:** Push, import the pptx from its raw URL as a new design.
- [ ] **Step 2:** In one Canva transaction, `update_fill` each `photo-slot` with MAHXrwF8Nbc; set a different `crop_media` on each title card (top, upper third, lower third, base of the tower). Read thumbnails of slides 1, 3, 5, 10, 18, 27, 33 and compare with the local render.
- [ ] **Step 3:** Check worst-spot contrast on the photo pages (text sits on the opaque fade by test; confirm by eye), commit the transaction.
- [ ] **Step 4:** Re-run the antislop and antislop-human Delivery Gate, record it, update QA notes and the design philosophy. Commit and push.

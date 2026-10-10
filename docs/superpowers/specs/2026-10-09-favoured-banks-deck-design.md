# Favoured Banks deck: design

**Owner:** Rahmananda Ridho Gamawan (RG)
**Date:** 2026-10-09
**Source of content:** the findings doc (Claude Docs, "Favoured Banks in ChatGPT and Gemini: Findings") and the tables in `data/processed/` and `data/interim/`.

## 1. Goal

A presentation deck of the GEO findings, built in RG's Canva account through the Canva connector, that four audiences can read without a presenter:

| Audience | What they should take away |
| --- | --- |
| LinkedIn network | A clear story with one finding per slide |
| Recruiters | How RG works: question, method, data quality, judgement |
| People in banking | Which banks the engines favour, which sources feed them, what to act on |
| GEO practitioners | The method, the metrics and the mechanics found in the data |

Success means:

- Every number on a slide traces to a row in the repo, and each chart names its source table and N.
- Nothing from the findings doc's removed points comes back (Source PAWC, the "size does not buy AI visibility" insight, finding 2 on bank assets).
- The deck opens in Canva with editable text, the chosen fonts, and no broken layout.
- All copy passes the antislop rules (no em dashes, no hype words, claims no stronger than the evidence).

No slide limit. Currently 32 slides, including four title cards.

## 2. Build route

1. A Python script under `deck/` renders every chart from the repo data with matplotlib.
2. The same script assembles an editable `.pptx` with python-pptx: real text boxes, the chart images, speaker notes.
3. Local check: convert the `.pptx` to images with LibreOffice and inspect every slide.
4. Push the `.pptx` to a `deck` branch of the public repo `rgmwnn/geo-bank-visibility`.
5. Import it into Canva with `import-design-from-url`, using the file's raw GitHub URL.
6. Read every Canva page back (`read-design` with thumbnails), fix what the import broke with `edit-design`, and save only after RG approves the preview.
7. Export a PDF from Canva.

Why this route: the Canva connector cannot set font families when editing, and Canva's own generator picks its own layouts and does not chart RG's data. Building the file first keeps full control of layout, type and charts, and Canva keeps the text editable.

## 3. Visual system

Design read: a data story for professional and technical readers, in a cinematic, restrained language drawn from Christopher Nolan's visual principles. Dials: ENERGY 2 / RHYTHM 3 / MOTION 1 (static slides, no animation).

The Nolan references are principles only. No film stills, logos, titles, characters or poster layouts.

| Principle | Rule in the deck | Reason |
| --- | --- | --- |
| Aspect ratio as meaning | Evidence slides sit in a 2.39:1 letterbox (black bars top and bottom). Title cards and hero numbers use the full 16:9 frame. | Nolan opens up to IMAX for the big moments. Here the frame opens when the slide makes its main claim. |
| One light source | Each chart lights only the mark the slide is about. Everything else is dim grey. | Gives every slide one focal point. |
| Two timelines | ChatGPT is always ember amber, Gemini always steel blue. Slides that compare the two are symmetrical. | The engines are the two storylines of the deck, and the colour never changes meaning. |
| Scale | One subject per frame, often small against a large empty field. Hero numbers are very large with a short caption. | Empty space sets the rhythm and keeps the eye on the subject. |
| Title cards | Each part opens on a full-frame card with a short wide-tracked label and one line. | Marks the four parts the way an intertitle marks a time or place. Wide tracking is used only here and in the slate. |

**Palette** (two core colours plus neutrals):

| Role | Hex |
| --- | --- |
| Background | `#0B0C0E` |
| Letterbox bars | `#000000` |
| Primary text | `#ECE7DD` (bone) |
| Secondary text | `#9A9EA6` |
| Dim marks, rules | `#3A3D43` |
| ChatGPT | `#D07A28` (ember) |
| Gemini | `#4790D8` (steel blue) |

The dark background is a choice, not a default: the deck reads as a screening, charts behave like lit objects, and LinkedIn document posts show dark slides well. All text pairs are checked for WCAG AA contrast before build.

**Type:** Work Sans (titles and body) and IBM Plex Mono (data labels, axis labels, the slate line). Both are Google fonts available in Canva. Charts use the same two fonts, so slides and charts match.

**Identity mark:** a slate line in the bottom letterbox bar on evidence slides: `09.10.2026 · 40 ANSWERS · SCENE 07`. It records the snapshot date and keeps the reader oriented.

**Charts:** thin rules, no gridlines unless a value must be read off, direct labels instead of legends, values in IBM Plex Mono, source and N in a footnote. Rendered at 2x for sharp import.

## 4. Slides

Each slide states one claim. Numbers come from the files named.

**Cold open**

1. **Cover.** Title, one-line subtitle, RG's name, the run date.
2. **One prompt, two answers.** One real prompt in Indonesian with its English meaning, and the banks each engine named in that answer, side by side. (`data/interim/mentions.csv`)
3. **Why it matters.** Information-seeking grew from 14% to 24% of ChatGPT conversations in a year (OpenAI study via Search Engine Journal). About 12% of URLs cited by AI assistants rank in Google's top 10 for the same query (Ahrefs). Full frame, two hero numbers.
4. **Three questions.** Which banks, which sources, where the two differ.

**Part I · Method**

5. **Title card.**
6. **Prompt design.** 20 prompts placed on a 5 pillars by 5 intents grid, Indonesian, unbranded except the comparisons. (`data/interim/answers.csv`)
7. **Pipeline.** Six steps drawn as descending levels with the count at each: 40 answers, 857 sentences, 427 mentions, 399 citations, 243 pages, 195 readable.
8. **Metrics.** Definitions of mention rate, AI-SOV, brand PAWC, Source-SOV, SOV gap and VIS, with the brand PAWC weight curve `exp(-position / sentence count)` drawn for a 10-sentence answer. Cites Aggarwal et al. 2024.
9. **Data and limits.** Funnel of citations to readable pages, plus the seven limits from the findings doc.

**Part II · The answers**

10. **Title card.**
11. **Three banks in more than half of answers.** Dot chart, top 10 banks, one dot per engine. (`brand_engine.csv`)
12. **Visibility score.** VIS for every bank, ranked, low-sample banks marked. (`vis.csv`)
13. **Gemini names a wider field.** 18 banks against 11, and the banks only Gemini named. (`brand_engine.csv`)
14. **Each need has its own leader.** Heatmap of pillars by top banks, leader outlined. (`brand_pillar.csv`)
15. **Named often against named early.** Mention rate against brand PAWC per bank. (`brand_engine.csv`)
16. **No answer was negative.** 137 answer and bank pairs as marks: 117 positive, 14 neutral, 6 mixed, 0 negative. (`data/labels/sentiment.csv`)
17. **How-to answers rarely name a bank.** Share of answers that name a bank, by intent. (`no_brand_rate.csv`)

**Part III · The sources**

18. **Title card.**
19. **Two engines, two webs.** Source mix by site type, ChatGPT 89% banks and regulators, Gemini 61% fintech, blog and news. (`domain_type_mix.csv`)
20. **Little overlap.** 21 of 97 sites and 11 of 243 pages cited by both. Jaccard 0.22 (sites) and 0.05 (pages), with Writesonic's 0.119 as a single outside reference. (`domains.csv`, `cross_engine_pages.csv`)
21. **Most cited sites.** Mirror bar chart, ChatGPT left and Gemini right, top sites by total citations. (`domains.csv`)
22. **Comparison articles in Gemini's answers.** Akulaku article in 14 of 20 Gemini answers, Zaipad 12, Fazz 20 citations across 15 answers, none cited by ChatGPT. Note: Akulaku held 27.24% of Bank Neo Commerce (Bisnis, May 2023), and the article has not been checked for bias. (`pages_top.csv`)
23. **Concentration.** Share of citations held by each engine's top five sites: 50% and 36%. (`concentration.csv`)
24. **SOV gap.** Answer share minus source share per bank: Bank Jago +6.6 pts, BCA +5.5 pts, Bank Mandiri the reverse. (`source_sov.csv`)
25. **Dead links.** 13 of Gemini's 21 Google-wrapped links are dead, 0 of its 179 direct links. Tow Center quote as the outside reference. (`data/interim/citations.csv`, `pages.csv`)
26. **Schema and dates.** Schema share by site type against share of citations, and how few cited pages state a publish date. Google Search Central quote. (`schema.csv`, `recency.csv`)

**Part IV · What it means**

27. **Title card.**
28. **For banks.** The six key insights from the findings doc.
29. **For GEO practitioners.** Lessons from building the pipeline: count only the listed sources, unwrap redirects, render pages built with JavaScript, weight pages equally in Source-SOV, measure answers per answer not per mention, and per-source PAWC needs inline citation markers.
30. **One run is a snapshot.** SparkToro's repeat-run result and what it means for these ranks.
31. **Next steps.**
32. **Close.** Sources, repo link, RG's name.

## 5. Copy rules

- Plain English, short sentences, one claim per slide title.
- Hedged wording stays hedged ("appear in", "likely", "suggests"), as fixed in the findings doc.
- Indonesian prompts are shown in Indonesian with an English line under them.
- Every outside figure carries its source on the slide.
- Speaker notes hold the longer explanation, so slides stay sparse.

## 6. Checks before delivery

- **Numbers.** A script recomputes every number used on a slide from the repo files and fails on any mismatch.
- **Local render.** Every slide is inspected as an image: no overlap, nothing outside the frame, no font fallback.
- **Contrast.** Every text colour pair meets WCAG AA (4.5:1 for small text, 3:1 for large).
- **Canva.** Every imported page is read back and compared with the local render. Fonts, letterbox bars and charts must survive the import.
- **antislop.** The Delivery Gate runs on the final deck, and its report goes with the delivery.

## 7. Out of scope

Animation and transitions, a portrait LinkedIn carousel version, an Indonesian translation of the deck, and the dashboard. Each can follow.

## Revision 2026-10-10: line language (Interstellar)

RG asked for line visuals in the spirit of Interstellar after the first version read as an empty background. Every line has a job, and none crosses text (tested).

| Element | Where | Job |
| --- | --- | --- |
| Ring with two disk lines (ember, steel) | Cover | Opens the record; the disk is the two engine threads |
| Corridor to a far wall, one more receding frame per part | Title cards 5, 10, 18, 27 | Depth: the viewer moves further into the study each part |
| Horizon arc, ember over steel | Hero (3), close (32) | Grounds the open frames; the two threads bent into one arc |
| Scene ruler, 32 ticks, current lit | Bottom bar of letterbox slides | Position in the deck, read like an instrument |
| Bar edge hairlines | Letterbox slides | Marks the screen edge between bars and image |
| Rail with a stop per item | List slides | Order of the items |
| Value lines ending in a point, empty track behind | Charts 8, 9, 12, 17, 21, 22, 23, 24, 25, 26 | Length carries the value; replaces filled bars |

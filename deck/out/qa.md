# Local render QA (LibreOffice, 2026-10-09)

All 32 slides inspected as images after each pass.

Found and fixed:
- Charts read small at slide scale: charts now draw on a smaller canvas (SHRINK 1.3) so type reads larger once placed.
- Chart backgrounds showed as faint boxes: charts are saved with transparent backgrounds.
- Prompt on slide 2 overlapped its English line: layout now measures text with the real font files (deck/measure.py).
- Left labels clipped in six charts (prompt grid, dots, VIS, heatmap, SOV gap, dead links, schema): margins widened.
- Pipeline numbers overlapped their step labels; funnel labels overflowed; Venn labels crossed circle edges: respaced.
- Heatmap labels had low contrast on mid-grey cells: fill capped so bone labels stay at 4.5:1 or better.
- Source-mix labels did not fit narrow segments: narrow segments are labelled under the bar.
- Slide 29 list ran into the bottom bar: list slides now shrink type to stay in the band (test added).
- Side charts sat high in their area: centred vertically and given more width.

Open: none.

# Canva import check (2026-10-09)

Design DAHXhYnEu0c, 32 pages, imported from the deck branch. Every page read back as a thumbnail and compared with the local render: Work Sans and IBM Plex Mono survived, letterbox bars, slates and transparent charts match, speaker notes present (checked pages 2 and 24). No repairs needed in Canva.

Note: the two thin engine-colour lines on the cover, hero and title cards read faintly in Canva's small thumbnails; at full size they render as drawn.

## Final-review fix pass

Re-rendered after the fixes. Slides checked by eye: 2 (prompt and translation now 24 px apart), 9, 12, 14 (unbranded prompts, row n), 17, 19 (Gemini third-party segments lit), 20, 21 (Gemini-only sites lit), 22, 24 (Bank Mandiri lit, alias caveat), 26, 28. Every chart footnote carries its n and stays on one line above the bar.

## Line-language revision (2026-10-10)

All 32 slides re-rendered and checked by eye: cover ring, title-card corridors (1 to 4 receding frames), horizon arcs on 3 and 32, scene ruler on every letterbox slide, list rails, and the ten charts redrawn as value lines. Two layout faults found and fixed by test: the cover title wrapped onto its subtitle, and slide 8 terms were 3 px taller than their slot. The closing title now flows from its measured height.

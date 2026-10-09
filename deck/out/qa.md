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

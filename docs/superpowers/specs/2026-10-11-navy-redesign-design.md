# Favoured Banks deck: navy redesign

Date: 2026-10-11. Owner: RG. Supersedes the visual system in `2026-10-09-favoured-banks-deck-design.md`; content, numbers and tests from that spec and its fix passes stay.

## Intent

RG rejected the pitch-black, thin-line version: it read as empty and "designed by AI". From three samples he chose C, "Navy night" (pages 5 and 6 of Canva design DAHXrxJ1WWM). The redesign carries C across all 33 slides and adds Nolan motifs again, this time as visible, futuristic line and shape work on navy, not as faint hairlines on black. Audience is unchanged: LinkedIn readers, recruiters, bank website teams (SEO, content, web) and GEO practitioners.

## Goals

- Every slide in the C system: deep navy ground, Plus Jakarta Sans, amber and light-blue data colours.
- The tower photo (Canva media MAHXrwF8Nbc, generated for this deck, no logos) on the cover and the four section title cards, cropped differently each time.
- Nolan motifs that read as futuristic and technical, each with a job (table below).
- Charts readable at slide size (existing tests: smallest chart text 24 px on the slide, no clipped or overlapping labels).
- Built through the existing pipeline (python-pptx, LibreOffice check, GitHub raw URL, Canva import), then the photo placed in Canva.

## Non-goals

- No new findings, numbers or copy changes beyond fitting text to the new layouts.
- No other photos: Canva image credits ran out and RG chose the tower only.

## Anti-goals (a failure even if it builds)

- Pitch black anywhere, or slides that read as empty.
- Fonts Canva does not have (Instrument Sans and Outfit were swapped for wrong faces in the first sample import).
- Decoration that crosses text, background grids with no job, glow, gradients on text.
- Tracked all-caps labels, middle-dot chains, film jargon in visible text (audit 002 rules stay, with their tests).

## Decided

| Item | Decision | Reason |
| --- | --- | --- |
| Ground | #0F2747 navy on every slide; panels #0A1C36 | RG chose dark blue, not black |
| Text | #F4F6FA titles and body; #AFC0D8 secondary | 13.85:1 and 8.10:1 on navy |
| Data colours | ChatGPT #F2A541 amber, Gemini #7FC0F5 light blue | 7.30:1 and 7.68:1 on navy; carried from sample C |
| Accent | Amber, used as data colour for ChatGPT and once on the cover rule | One deliberate accent, never confused with data |
| Line colour | #3B5A85 steel for decorative lines, #7FC0F5 at reduced weight for motif highlights | Lines carry no data on their own |
| Type | Plus Jakarta Sans Bold for titles, Regular for text; IBM Plex Mono for small measurements (page numbers, axis ticks, source lines) | Both render correctly in Canva (font test DAHXrxmW5HQ); Plus Jakarta Sans was designed in Jakarta |
| Cover | Sample C page 5 as is: full-bleed tower, navy fade from the left, amber rule | RG approved it |
| Section cards | Tower photo, a different crop per part, navy fade, a perspective corridor of lines over the photo that gains one frame per part | Nolan tesseract, shows depth into the study |
| Evidence slides | Title and text left, chart right in a framed panel with corner brackets; footer with source and a progress ruler | Instrument (HUD) feel; brackets mark the evidence area |
| Hero (slide 3) | 24% and 12% drawn as ring gauges whose arc length is the value | Interstellar ring, and the shape carries the number |
| Lists | Numbered rail with stops, kept | Order of items |
| Close | Horizon arc in amber over light blue along the bottom, kept | The two engine threads |
| Charts | Same 19 charts, recoloured for navy; lit marks white unless the mark is an engine | Existing readability tests stay |

## Photo placement (answered from the sample build)

The workspace cannot download the photo (image hosts are blocked), so the .pptx carries a named `photo-slot` shape on the cover and the four title cards, drawn first so it sits at the back. After the Canva import, the photo goes in with `update_fill` on that shape, which keeps the stacking order: the fade and the corridor lines stay on top (shown on sample C page 5). Each card's crop is set with `crop_media`. The worst-spot contrast check on the photo pages runs on the Canva thumbnails after placement; the navy fade is fully opaque under all text, so text contrast does not depend on the photo.

## Calls I made (RG can overrule)

- Layouts keep their current types: `side` slides keep the chart on the right, `stack` slides keep the full-width chart. Every chart, either layout, sits in the bracketed panel. This keeps the readability tests passable without redrawing wide charts for half width.
- Amber means ChatGPT and nothing else in charts. Single-series charts light their mark in white, never amber. The only amber outside data is the short rule on the cover. The slide 3 gauges are white on steel, so neither engine colour is implied. The lit progress tick is white.
- Canva: the rebuilt deck imports as a new design, as before. Older designs stay until RG deletes them; no manual edits have been made in them.

## Left to the builder

- Exact crop offsets for the four title-card photos.
- Bracket length, line weights and spacing, within the colours above.
- Whether the progress ruler lives in the footer or the top edge, as long as it never crosses text.

## Checks

- Full test suite green; tests that pin the old black design (bars, letterbox band) are rewritten to the new system, never deleted without a replacement.
- Contrast for every text pair on navy and on the photo fade (worst spot, not best).
- LibreOffice render looked at slide by slide; Canva import read back with thumbnails.
- antislop and antislop-human Delivery Gate re-run and recorded.

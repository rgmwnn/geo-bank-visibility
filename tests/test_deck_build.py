import re

import pytest
from pptx import Presentation
from pptx.util import Emu

from deck import build, copy
from deck.facts import load

PX = 6350  # EMU per slide pixel (1920 px wide)


@pytest.fixture(scope="module")
def deck(tmp_path_factory):
    path = build.build(tmp_path_factory.mktemp("deck") / "favoured-banks.pptx")
    return Presentation(str(path))


def _texts(deck):
    for i, s in enumerate(deck.slides, start=1):
        for sh in s.shapes:
            if sh.has_text_frame:
                yield i, sh, sh.text_frame.text
        yield i, None, s.notes_slide.notes_text_frame.text


def test_slide_count_and_kinds(deck):
    assert len(deck.slides) == 32
    kinds = [s["kind"] for s in copy.slides(load())]
    assert [i + 1 for i, k in enumerate(kinds) if k == "title_card"] == [5, 10, 18, 27]


def test_no_dashes_or_hype(deck):
    banned = ["seamless", "revolutionary", "cutting edge", "next generation", "powerful", "leverage", "unlock",
              "game-changer", "elevate", "delve"]
    for i, _, t in _texts(deck):
        assert "—" not in t and "–" not in t, i
        low = t.lower()
        assert not [w for w in banned if w in low], (i, t)


def test_fonts_only_sans_and_mono(deck):
    for s in deck.slides:
        for sh in s.shapes:
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    for r in p.runs:
                        assert r.font.name in ("Work Sans", "IBM Plex Mono"), r.text


def test_numbers_come_from_facts(deck):
    allowed = copy.allowed_numbers(load())
    for i, _, t in _texts(deck):
        t = t.replace("09.10.2026", "")
        t = re.sub(r"SCENE \d+", "", t)
        for tok in re.findall(r"\d[\d,.]*\d|\d", t):
            assert tok.rstrip(".,") in allowed, (i, tok, t[:80])


def test_text_fits(deck):
    from deck.measure import height
    for i, sh, _ in _texts(deck):
        if sh is None:
            continue
        w_px, h_px = sh.width / PX, sh.height / PX
        need = 0.0
        for p in sh.text_frame.paragraphs:
            if not p.runs:
                continue
            r = p.runs[0]
            need += height("".join(x.text for x in p.runs), w_px, r.font.size.pt, r.font.name == "IBM Plex Mono")
        assert need <= h_px + 2, (i, sh.text_frame.text[:60], round(need), round(h_px))


def test_letterbox_slides_have_slate(deck):
    kinds = [s["kind"] for s in copy.slides(load())]
    for n, (k, s) in enumerate(zip(kinds, deck.slides), start=1):
        texts = [sh.text_frame.text for sh in s.shapes if sh.has_text_frame]
        has = any(t == f"09.10.2026  ·  40 ANSWERS  ·  SCENE {n:02d}" for t in texts)
        assert has == (k == "letterbox"), (n, k)


def test_letterbox_content_stays_inside_the_band(deck):
    kinds = [s["kind"] for s in copy.slides(load())]
    for n, (k, s) in enumerate(zip(kinds, deck.slides), start=1):
        if k != "letterbox":
            continue
        for sh in s.shapes:
            top, bottom = sh.top / PX, (sh.top + sh.height) / PX
            is_footnote = sh.has_text_frame and round(top) == 902
            if 150 <= top < 942 and not is_footnote:  # content, not bars, slate or footnote
                assert bottom <= 895, (n, sh.shape_type, round(top), round(bottom))

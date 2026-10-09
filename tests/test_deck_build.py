import math
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
    for i, sh, _ in _texts(deck):
        if sh is None:
            continue
        w_px, h_px = sh.width / PX, sh.height / PX
        need = 0.0
        for p in sh.text_frame.paragraphs:
            if not p.runs:
                continue
            size_px = p.runs[0].font.size.pt * 2
            em = 0.62 if p.runs[0].font.name == "IBM Plex Mono" else 0.52
            cpl = max(1, int(w_px / (em * size_px)))
            text = "".join(r.text for r in p.runs)
            lines = sum(max(1, math.ceil(len(part) / cpl)) for part in text.split("\v"))
            need += lines * size_px * 1.25
        assert need <= h_px + 2, (i, text[:60], round(need), round(h_px))


def test_letterbox_slides_have_slate(deck):
    kinds = [s["kind"] for s in copy.slides(load())]
    for n, (k, s) in enumerate(zip(kinds, deck.slides), start=1):
        texts = [sh.text_frame.text for sh in s.shapes if sh.has_text_frame]
        has = any(t == f"09.10.2026  ·  40 ANSWERS  ·  SCENE {n:02d}" for t in texts)
        assert has == (k == "letterbox"), (n, k)

"""Line-language motifs (deck/design-philosophy.md, Event Horizon): present where the spec puts them, never over text."""
import pytest
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from deck import build, charts, copy
from deck.facts import load

PX = 6350


@pytest.fixture(scope="module")
def deck(tmp_path_factory):
    return Presentation(str(build.build(tmp_path_factory.mktemp("deck") / "d.pptx")))


@pytest.fixture(scope="module")
def specs():
    return copy.slides(load())


def _box(sh):
    return sh.left / PX, sh.top / PX, (sh.left + sh.width) / PX, (sh.top + sh.height) / PX


def _texts(slide):
    return [_box(sh) for sh in slide.shapes if sh.has_text_frame and sh.text_frame.text.strip()]


def _motifs(slide, prefix="motif"):
    return [sh for sh in slide.shapes if sh.name.startswith(prefix)]


def _crosses(sh, rect, pad=4):
    x0, y0, x1, y1 = rect[0] - pad, rect[1] - pad, rect[2] + pad, rect[3] + pad
    if sh.shape_type == MSO_SHAPE_TYPE.LINE or sh.name.startswith("motif-line"):
        bx, by, ex, ey = sh.begin_x / PX, sh.begin_y / PX, sh.end_x / PX, sh.end_y / PX
        for i in range(201):
            t = i / 200
            x, y = bx + (ex - bx) * t, by + (ey - by) * t
            if x0 < x < x1 and y0 < y < y1:
                return True
        return False
    a = _box(sh)
    return a[0] < x1 and a[2] > x0 and a[1] < y1 and a[3] > y0


def test_no_motif_touches_text(deck):
    for n, s in enumerate(deck.slides, start=1):
        texts = _texts(s)
        for m in _motifs(s):
            for t in texts:
                assert not _crosses(m, t), (n, m.name, [round(v) for v in t])


def test_cover_has_ring_and_disk(deck):
    names = [m.name for m in _motifs(deck.slides[0])]
    assert sum(x.startswith("motif-ring") for x in names) >= 3
    assert sum(x.startswith("motif-line-disk") for x in names) == 2


def test_title_cards_recede_one_more_frame_per_part(deck, specs):
    cards = [i for i, s in enumerate(specs) if s["kind"] == "title_card"]
    for part, i in enumerate(cards, start=1):
        names = [m.name for m in _motifs(deck.slides[i])]
        frames = {x.split("-")[3] for x in names if x.startswith("motif-line-depth")}
        assert len(frames) == part, (i + 1, part)
        assert sum(x.startswith("motif-line-corridor") for x in names) >= 8


def test_letterbox_slides_carry_the_scene_ruler(deck, specs):
    total = len(specs)
    for n, (s, sl) in enumerate(zip(specs, deck.slides), start=1):
        ticks = sorted((m for m in _motifs(sl, "motif-line-tick")), key=lambda m: m.begin_x)
        if s["kind"] != "letterbox":
            assert not ticks, n
            continue
        assert len(ticks) == total, n
        lit = [k for k, m in enumerate(ticks, start=1) if abs(m.end_y - m.begin_y) / PX > 20]
        assert lit == [n], (n, lit)
        for m in ticks:
            assert m.begin_y / PX >= 942, (n, "ruler must sit in the bottom bar")


def test_open_frames_have_a_horizon_below_all_text(deck, specs):
    for n, (s, sl) in enumerate(zip(specs, deck.slides), start=1):
        if s["layout"] not in ("hero", "close"):
            continue
        hz = [m for m in _motifs(sl, "motif-horizon")]
        assert len(hz) == 1, n
        assert hz[0].top / PX >= max(t[3] for t in _texts(sl)), n


def test_lists_hang_on_a_rail(deck, specs):
    for n, (s, sl) in enumerate(zip(specs, deck.slides), start=1):
        if s["layout"] != "list":
            continue
        assert len(_motifs(sl, "motif-line-rail")) == 1, n
        assert len(_motifs(sl, "motif-line-stop")) == len(s["body"]), n


LINE_CHARTS = ["pawc_curve", "funnel", "vis_rank", "intent_named", "mirror_sites", "top_pages", "concentration",
               "sov_gap", "dead_links", "schema"]


def test_quantities_are_drawn_as_lines_not_bars(tmp_path):
    charts.render_all(load(), tmp_path)
    bars = charts.LAST_DATA["bars"]
    for k in LINE_CHARTS:
        assert bars[k] == 0, k


def test_text_boxes_never_overlap(deck):
    from deck.measure import height
    for n, s in enumerate(deck.slides, start=1):
        boxes = []
        for sh in s.shapes:
            if not (sh.has_text_frame and sh.text_frame.text.strip()):
                continue
            x0, y0, x1, _ = _box(sh)
            need = sum(height("".join(r.text for r in p.runs), x1 - x0, p.runs[0].font.size.pt,
                              p.runs[0].font.name == "IBM Plex Mono") for p in sh.text_frame.paragraphs if p.runs)
            boxes.append((x0, y0, x1, y0 + need, sh.text_frame.text[:30]))
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                assert not (a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]), (n, a[4], b[4])

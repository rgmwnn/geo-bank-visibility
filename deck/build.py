"""Assemble the editable deck (deck/out/favoured-banks.pptx) from facts, charts and copy."""
import math
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Pt

from deck import charts, copy
from deck.facts import load
from deck.theme import C, MONO, SANS

ROOT = Path(__file__).resolve().parent
PX = 6350
W, H, BAR = 1920, 1080, 138
LEFT = 120
OUT = ROOT / "out" / "favoured-banks.pptx"


def _rgb(hex_color: str) -> RGBColor:
    return RGBColor.from_string(hex_color.lstrip("#"))


def est_h(text: str, w: float, pt: float, mono: bool = False) -> float:
    size = pt * 2
    cpl = max(1, int(w / ((0.62 if mono else 0.52) * size)))
    return max(1, math.ceil(len(text) / cpl)) * size * 1.3


def rect(slide, x, y, w, h, color):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(int(x * PX)), Emu(int(y * PX)), Emu(int(w * PX)), Emu(int(h * PX)))
    s.fill.solid()
    s.fill.fore_color.rgb = _rgb(color)
    s.line.fill.background()
    s.shadow.inherit = False
    return s


def hline(slide, x0, x1, y, color, weight=1.5):
    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(int(x0 * PX)), Emu(int(y * PX)), Emu(int(x1 * PX)), Emu(int(y * PX)))
    ln.line.color.rgb = _rgb(color)
    ln.line.width = Pt(weight)
    return ln


def text(slide, x, y, w, h, paras, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    """paras: list of (text, pt, color, font, bold, tracking) tuples, one paragraph each."""
    tb = slide.shapes.add_textbox(Emu(int(x * PX)), Emu(int(y * PX)), Emu(int(w * PX)), Emu(int(h * PX)))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, (t, pt, color, font, bold, track) in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = 1.15
        r = p.add_run()
        r.text = t
        r.font.name = font
        r.font.size = Pt(pt)
        r.font.bold = bold
        r.font.color.rgb = _rgb(color)
        if track:
            r._r.get_or_add_rPr().set("spc", str(track))
    return tb


def P(t, pt, color=C["text"], font=SANS, bold=False, track=0):
    return (t, pt, color, font, bold, track)


def picture(slide, path: Path, box):
    x, y, w, h = box
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    slide.shapes.add_picture(str(path), Emu(int((x + (w - pw) / 2) * PX)), Emu(int(y * PX)),
                             Emu(int(pw * PX)), Emu(int(ph * PX)))


def timelines(slide, x0, x1, y):
    hline(slide, x0, x1, y, C["gpt"], 1.25)
    hline(slide, x0, x1, y + 12, C["gem"], 1.25)


def frame(slide, kind: str):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = _rgb(C["bar"] if kind == "title_card" else C["bg"])
    if kind == "letterbox":
        rect(slide, 0, 0, W, BAR, C["bar"])
        rect(slide, 0, H - BAR, W, BAR, C["bar"])


def chrome(slide, n: int, s: dict):
    text(slide, LEFT, 58, 700, 26, [P("FAVOURED BANKS", 9, C["secondary"], MONO, track=200)])
    text(slide, W - LEFT - 800, 58, 800, 26, [P(s.get("part", ""), 9, C["secondary"], MONO, track=200)], align=PP_ALIGN.RIGHT)
    text(slide, LEFT, H - BAR + 54, 900, 26,
         [P(f"{copy.SLATE_DATE}  ·  40 ANSWERS  ·  SCENE {n:02d}", 9, C["secondary"], MONO, track=150)])
    if s.get("foot"):
        text(slide, LEFT, H - BAR - 40, W - 2 * LEFT, 26, [P(s["foot"], 9, C["secondary"], MONO)])


def _title(slide, s, x, y, w, pt=26):
    h = est_h(s["title"], w, pt)
    text(slide, x, y, w, h, [P(s["title"], pt)])
    return y + h


def _body(slide, paras, x, y, w, pt=14, gap=14, color=C["secondary"], bullets=False):
    for b in paras:
        t = ("·  " + b) if bullets else b
        h = est_h(t, w, pt)
        text(slide, x, y, w, h, [P(t, pt, color)])
        y += h + gap
    return y


def lay_cover(slide, s, n, art):
    text(slide, LEFT, 300, 1600, 30, [P(s["kicker"], 11, C["secondary"], MONO, track=200)])
    text(slide, LEFT, 340, 1680, 210, [P(s["title"], 80)])
    text(slide, LEFT, 560, 1150, est_h(s["body"][0], 1150, 20), [P(s["body"][0], 20, C["secondary"])])
    timelines(slide, LEFT, W - LEFT, 760)
    text(slide, LEFT, 860, 1000, 34, [P(s["byline"], 12, C["text"], MONO)])


def lay_hero(slide, s, n, art):
    text(slide, LEFT, 170, 1500, est_h(s["title"], 1500, 26), [P(s["title"], 26)])
    for i, (big, cap, src) in enumerate(s["heroes"]):
        x = LEFT + i * 860
        text(slide, x, 390, 820, 200, [P(big, 72)])
        text(slide, x, 600, 720, est_h(cap, 720, 16), [P(cap, 16, C["secondary"])])
        text(slide, x, 720, 720, 30, [P(src, 9, C["secondary"], MONO)])
    timelines(slide, LEFT, LEFT + 240, 900)


def lay_card(slide, s, n, art):
    text(slide, 0, 400, W, 34, [P(s["part"], 12, C["secondary"], MONO, track=400)], align=PP_ALIGN.CENTER)
    text(slide, 0, 450, W, 150, [P(s["title"], 60)], align=PP_ALIGN.CENTER)
    text(slide, 0, 600, W, 50, [P(s["body"][0], 18, C["secondary"])], align=PP_ALIGN.CENTER)
    timelines(slide, W / 2 - 80, W / 2 + 80, 700)


def lay_side(slide, s, n, art):
    y = _title(slide, s, LEFT, 190, 620)
    _body(slide, s["body"], LEFT, y + 26, 620, bullets=s.get("bullets", False))
    if s.get("chart"):
        picture(slide, art[s["chart"]], (790, 190, 1010, 680))


def lay_stack(slide, s, n, art):
    y = _title(slide, s, LEFT, 186, 1680)
    y = _body(slide, s["body"], LEFT, y + 14, 1350, gap=8)
    picture(slide, art[s["chart"]], (LEFT, y + 10, W - 2 * LEFT, H - BAR - 60 - (y + 10)))


def lay_list(slide, s, n, art):
    y = _title(slide, s, LEFT, 200, 1500, pt=30) + 34
    for i, item in enumerate(s["body"], start=1):
        h = est_h(item, 1360, 17)
        if s.get("numbered"):
            text(slide, LEFT, y + 4, 90, 34, [P(f"{i:02d}", 13, C["secondary"], MONO)])
        text(slide, LEFT + 110, y, 1360, h, [P(item, 17)])
        y += h + 22


def lay_metrics(slide, s, n, art):
    y = _title(slide, s, LEFT, 190, 1680) + 26
    for term, definition in s["body"]:
        text(slide, LEFT, y, 760, 40, [P(term, 15)])
        h = est_h(definition, 760, 12)
        text(slide, LEFT, y + 38, 760, h, [P(definition, 12, C["secondary"])])
        y += 38 + h + 16
    picture(slide, art[s["chart"]], (960, 300, 840, 520))


def lay_cold_open(slide, s, n, art):
    y = _title(slide, s, LEFT, 190, 1680) + 30
    prompt = f"“{s['prompt']}”"
    h = est_h(prompt, 1500, 22)
    text(slide, LEFT, y, 1500, h, [P(prompt, 22)])
    y += h + 10
    h = est_h(s["english"], 1500, 14)
    text(slide, LEFT, y, 1500, h, [P(s["english"], 14, C["secondary"])])
    y += h + 60
    for i, (head, banks, key) in enumerate(s["cols"]):
        x = LEFT + i * 760
        rect(slide, x, y + 8, 14, 14, C[key])
        text(slide, x + 30, y, 600, 30, [P(head.upper(), 11, C["secondary"], MONO, track=200)])
        names = banks.split("\n")
        text(slide, x, y + 50, 680, len(names) * 62, [P(b, 24) for b in names])


def lay_close(slide, s, n, art):
    text(slide, LEFT, 170, 1600, 104, [P(s["title"], 40)])
    text(slide, LEFT, 290, 1600, 40, [P(s["body"][0], 16, C["text"], MONO)])
    y = 400
    text(slide, LEFT, y, 400, 28, [P("SOURCES", 10, C["secondary"], MONO, track=300)])
    y += 44
    for src in s["sources"]:
        text(slide, LEFT, y, 1500, 28, [P(src, 11, C["secondary"], MONO)])
        y += 36
    timelines(slide, LEFT, W - LEFT, 820)
    text(slide, LEFT, 880, 1300, 34, [P(s["byline"], 12, C["text"], MONO)])


LAYOUTS = {"cover": lay_cover, "hero": lay_hero, "card": lay_card, "side": lay_side, "stack": lay_stack,
           "list": lay_list, "metrics": lay_metrics, "cold_open": lay_cold_open, "close": lay_close}


def build(out: Path = OUT) -> Path:
    f = load()
    art = charts.render_all(f, ROOT / "out" / "charts")
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(W * PX), Emu(H * PX)
    blank = prs.slide_layouts[6]
    for n, s in enumerate(copy.slides(f), start=1):
        slide = prs.slides.add_slide(blank)
        frame(slide, s["kind"])
        LAYOUTS[s["layout"]](slide, s, n, art)
        if s["kind"] == "letterbox":
            chrome(slide, n, s)
        if s.get("notes"):
            slide.notes_slide.notes_text_frame.text = s["notes"]
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    return out


if __name__ == "__main__":
    print(build())

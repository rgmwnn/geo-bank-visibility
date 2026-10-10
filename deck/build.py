"""Assemble the editable deck (deck/out/favoured-banks.pptx) from facts, charts and copy."""
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Pt

from deck import charts, copy, measure
from deck.facts import load
from deck.theme import C, MONO, SANS

ROOT = Path(__file__).resolve().parent
PX = 6350
W, H, BAR = 1920, 1080, 138
LEFT = 120
OUT = ROOT / "out" / "favoured-banks.pptx"


def _rgb(hex_color: str) -> RGBColor:
    return RGBColor.from_string(hex_color.lstrip("#"))


def est_h(t: str, w: float, pt: float, mono: bool = False) -> float:
    return measure.height(t, w, pt, mono)


def rect(slide, x, y, w, h, color):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(int(x * PX)), Emu(int(y * PX)), Emu(int(w * PX)), Emu(int(h * PX)))
    s.fill.solid()
    s.fill.fore_color.rgb = _rgb(color)
    s.line.fill.background()
    s.shadow.inherit = False
    return s


def seg(slide, x0, y0, x1, y1, color, weight=1.0, name=None):
    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(int(x0 * PX)), Emu(int(y0 * PX)),
                                    Emu(int(x1 * PX)), Emu(int(y1 * PX)))
    ln.line.color.rgb = _rgb(color)
    ln.line.width = Pt(weight)
    if name:
        ln.name = name
    return ln


def hline(slide, x0, x1, y, color, weight=1.5, name=None):
    return seg(slide, x0, y, x1, y, color, weight, name)


def oval(slide, cx, cy, w, h, color, weight, name, fill=None):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, Emu(int((cx - w / 2) * PX)), Emu(int((cy - h / 2) * PX)),
                               Emu(int(w * PX)), Emu(int(h * PX)))
    if fill:
        s.fill.solid()
        s.fill.fore_color.rgb = _rgb(fill)
    else:
        s.fill.background()
    s.line.color.rgb = _rgb(color)
    s.line.width = Pt(weight)
    s.shadow.inherit = False
    s.name = name
    return s


# Line language (deck/design-philosophy.md, Event Horizon). Every motif is named motif-*; none may cross text.

def ring(slide, cx, cy, r):
    """A dark body with thin orbits behind it and the two engine threads crossing in front as its disk."""
    oval(slide, cx, cy, r * 2.9, r * 0.62, C["dim"], 1.0, "motif-ring-orbit-wide")
    oval(slide, cx, cy, r * 2.3, r * 0.44, C["dim"], 1.0, "motif-ring-orbit-near")
    oval(slide, cx, cy, r * 2.75, r * 2.75, C["dim"], 0.75, "motif-ring-halo")
    oval(slide, cx, cy, r * 2, r * 2, C["text"], 1.5, "motif-ring-photon", fill=C["bar"])
    oval(slide, cx, cy, r * 1.86, r * 1.86, C["dim"], 0.75, "motif-ring-inner")
    half = r * 1.6
    seg(slide, cx - half, cy - 6, cx + half, cy - 6, C["gpt"], 1.5, "motif-line-disk-gpt")
    seg(slide, cx - half, cy + 6, cx + half, cy + 6, C["gem"], 1.5, "motif-line-disk-gem")


WALL = (440, 330, 1480, 790)  # the corridor's far wall, where a title card's text stands
DEPTHS = [0.5, 0.75, 0.875, 0.9375]


def corridor(slide, frames: int):
    """Perspective lines from the frame to the far wall, plus one receding frame per part of the deck."""
    x0, y0, x1, y1 = WALL

    def at(t):
        return x0 * t, y0 * t, W - (W - x1) * t, H - (H - y1) * t

    for k, (ax, ay, bx, by) in enumerate([(0, 0, x0, y0), (W, 0, x1, y0), (0, H, x0, y1), (W, H, x1, y1)]):
        seg(slide, ax, ay, bx, by, C["dim"], 1.0, f"motif-line-corridor-corner-{k}")
    for k in range(1, 6):
        u = k / 6
        seg(slide, W * u, 0, x0 + (x1 - x0) * u, y0, C["dim"], 0.75, f"motif-line-corridor-top-{k}")
        seg(slide, W * u, H, x0 + (x1 - x0) * u, y1, C["dim"], 0.75, f"motif-line-corridor-floor-{k}")
    for k in range(1, 4):
        v = k / 4
        seg(slide, 0, H * v, x0, y0 + (y1 - y0) * v, C["dim"], 0.75, f"motif-line-corridor-left-{k}")
        seg(slide, W, H * v, x1, y0 + (y1 - y0) * v, C["dim"], 0.75, f"motif-line-corridor-right-{k}")
    for i, t in enumerate(DEPTHS[:frames], start=1):
        a, b, c, d = at(t)
        for side, (p, q, r_, s_) in zip("tblr", [(a, b, c, b), (a, d, c, d), (a, b, a, d), (c, b, c, d)]):
            seg(slide, p, q, r_, s_, C["secondary"] if i == frames else C["dim"], 1.0, f"motif-line-depth-{i}-{side}")


def ruler(slide, n: int, total: int):
    """One tick per scene in the bottom bar; the current scene is lit."""
    x0, step, y = 1240, 18, 1006
    for k in range(1, total + 1):
        x = x0 + (k - 1) * step
        if k == n:
            seg(slide, x, y - 16, x, y + 16, C["text"], 2.0, f"motif-line-tick-{k:02d}")
        else:
            seg(slide, x, y - 6, x, y + 6, C["secondary"] if k < n else C["dim"], 1.0, f"motif-line-tick-{k:02d}")


def bar_edges(slide):
    hline(slide, 0, W, BAR, C["dim"], 0.75, "motif-line-edge-top")
    hline(slide, 0, W, H - BAR, C["dim"], 0.75, "motif-line-edge-bottom")


def horizon(slide, top: float = 868):
    """A planet's horizon along the bottom edge: the two engine threads bent into one arc."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    path = ROOT / "out" / "charts" / "motif-horizon.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    h = H - top
    if True:  # cheap to redraw; keeps the image in step with `top`
        R = 2600
        fig = plt.figure(figsize=(W / 100, h / 100), dpi=200)
        ax = fig.add_axes([0, 0, 1, 1])
        xs = np.linspace(0, W, 1200)
        for off, col, lw in ((4, C["gpt"], 1.6), (18, C["gem"], 1.6)):
            ys = top + off + R - np.sqrt(R ** 2 - (xs - W / 2) ** 2)
            ax.plot(xs, ys, color=col, lw=lw, solid_capstyle="butt")
        ax.set_xlim(0, W)
        ax.set_ylim(H, top)
        ax.axis("off")
        fig.savefig(path, transparent=True)
        plt.close(fig)
    pic = slide.shapes.add_picture(str(path), 0, Emu(int(top * PX)), Emu(int(W * PX)), Emu(int(h * PX)))
    pic.name = "motif-horizon"
    return pic


def text(slide, x, y, w, h, paras, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    """paras: list of (text, pt, color, font, bold, tracking) tuples, one paragraph each.
    The box grows to the measured height of its text, so nothing overflows."""
    h = max(h, sum(est_h(t, w, pt, font == MONO) for t, pt, _, font, _, _ in paras))
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


def picture(slide, path: Path, box, valign: str = "top"):
    x, y, w, h = box
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    top = y + (h - ph) / 2 if valign == "middle" else y
    slide.shapes.add_picture(str(path), Emu(int((x + (w - pw) / 2) * PX)), Emu(int(top * PX)),
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
        bar_edges(slide)


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
    ring(slide, 1560, 440, 200)  # its disk runs level with the title
    text(slide, LEFT, 300, 940, 30, [P(s["kicker"], 11, C["secondary"], MONO, track=200)])
    th = est_h(s["title"], 1110, 68)
    text(slide, LEFT, 340, 1110, th, [P(s["title"], 68)])
    y = 340 + th + 20
    text(slide, LEFT, y, 1060, est_h(s["body"][0], 1060, 20), [P(s["body"][0], 20, C["secondary"])])
    text(slide, LEFT, 860, 940, 34, [P(s["byline"], 12, C["text"], MONO)])


def lay_hero(slide, s, n, art):
    text(slide, LEFT, 170, 1500, est_h(s["title"], 1500, 26), [P(s["title"], 26)])
    for i, (big, cap, src) in enumerate(s["heroes"]):
        x = LEFT + i * 860
        text(slide, x, 390, 820, 200, [P(big, 72)])
        text(slide, x, 600, 720, est_h(cap, 720, 16), [P(cap, 16, C["secondary"])])
        text(slide, x, 720, 720, 30, [P(src, 9, C["secondary"], MONO)])
    horizon(slide)


CARD_PARTS = {"PART I": 1, "PART II": 2, "PART III": 3, "PART IV": 4}


def lay_card(slide, s, n, art):
    corridor(slide, CARD_PARTS[s["part"]])
    x0, _, x1, _ = WALL
    w = x1 - x0 - 60
    text(slide, x0 + 30, 400, w, 34, [P(s["part"], 12, C["secondary"], MONO, track=400)], align=PP_ALIGN.CENTER)
    text(slide, x0 + 30, 440, w, 150, [P(s["title"], 60)], align=PP_ALIGN.CENTER)
    text(slide, x0 + 30, 620, w, 50, [P(s["body"][0], 18, C["secondary"])], align=PP_ALIGN.CENTER)
    timelines(slide, W / 2 - 80, W / 2 + 80, 720)


def lay_side(slide, s, n, art):
    y = _title(slide, s, LEFT, 190, 600)
    bullets = s.get("bullets", False)
    _body(slide, s["body"], LEFT, y + 26, 600, gap=10 if bullets else 14, bullets=bullets)
    if s.get("chart"):
        picture(slide, art[s["chart"]], (770, 180, 1060, 700), valign="middle")


def lay_stack(slide, s, n, art):
    y = _title(slide, s, LEFT, 186, 1680)
    y = _body(slide, s["body"], LEFT, y + 14, 1350, gap=8)
    picture(slide, art[s["chart"]], (LEFT, y + 10, W - 2 * LEFT, H - BAR - 60 - (y + 10)))


RAIL_X = LEFT + 82


def lay_list(slide, s, n, art):
    y0 = _title(slide, s, LEFT, 200, 1680, pt=30) + 34
    numbered = s.get("numbered", False)
    x, w = LEFT + 120, 1360
    pt, gap = 17, 22
    while pt > 13 and y0 + sum(est_h(i, w, pt) + gap for i in s["body"]) > 880:
        pt, gap = pt - 1, gap - 2
    y = y0
    stops = []
    for i, item in enumerate(s["body"], start=1):
        h = est_h(item, w, pt)
        if numbered:
            text(slide, LEFT, y + 4, 50, 34, [P(f"{i:02d}", 13, C["secondary"], MONO)])
        text(slide, x, y, w, h, [P(item, pt)])
        stops.append(y + pt * measure.LINE)
        y += h + gap
    seg(slide, RAIL_X, stops[0] - 18, RAIL_X, stops[-1] + 18, C["dim"], 1.0, "motif-line-rail")
    for k, sy in enumerate(stops, start=1):
        seg(slide, RAIL_X - 7, sy, RAIL_X + 7, sy, C["secondary"], 1.25, f"motif-line-stop-{k}")


def lay_metrics(slide, s, n, art):
    y = _title(slide, s, LEFT, 186, 1680) + 18
    for term, definition in s["body"]:
        th = est_h(term, 820, 14)
        text(slide, LEFT, y, 820, th, [P(term, 14)])
        h = est_h(definition, 820, 12)
        text(slide, LEFT, y + th + 2, 820, h, [P(definition, 12, C["secondary"])])
        y += th + 2 + h + 10
    picture(slide, art[s["chart"]], (1000, 300, 800, 500))


def lay_cold_open(slide, s, n, art):
    y = _title(slide, s, LEFT, 190, 1680) + 30
    prompt = f"“{s['prompt']}”"
    h = est_h(prompt, 1500, 22)
    text(slide, LEFT, y, 1500, h, [P(prompt, 22)])
    y += h + 24
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
    th = est_h(s["title"], 1680, 40)
    text(slide, LEFT, 170, 1680, th, [P(s["title"], 40)])
    text(slide, LEFT, 170 + th + 10, 1600, 40, [P(s["body"][0], 16, C["text"], MONO)])
    y = 400
    text(slide, LEFT, y, 400, 28, [P("SOURCES", 10, C["secondary"], MONO, track=300)])
    y += 44
    for src in s["sources"]:
        text(slide, LEFT, y, 1500, 28, [P(src, 11, C["secondary"], MONO)])
        y += 36
    text(slide, LEFT, 780, 1300, 34, [P(s["byline"], 12, C["text"], MONO)])
    horizon(slide)


LAYOUTS = {"cover": lay_cover, "hero": lay_hero, "card": lay_card, "side": lay_side, "stack": lay_stack,
           "list": lay_list, "metrics": lay_metrics, "cold_open": lay_cold_open, "close": lay_close}


def build(out: Path = OUT) -> Path:
    f = load()
    art = charts.render_all(f, ROOT / "out" / "charts")
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(W * PX), Emu(H * PX)
    blank = prs.slide_layouts[6]
    specs = copy.slides(f)
    for n, s in enumerate(specs, start=1):
        slide = prs.slides.add_slide(blank)
        frame(slide, s["kind"])
        LAYOUTS[s["layout"]](slide, s, n, art)
        if s["kind"] == "letterbox":
            chrome(slide, n, s)
            ruler(slide, n, len(specs))
        if s.get("notes"):
            slide.notes_slide.notes_text_frame.text = s["notes"]
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    return out


if __name__ == "__main__":
    print(build())

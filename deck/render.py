"""Render the deck's charts and backgrounds as PNGs from data/processed.

Style: dark cinematic (see deck/design-philosophy.md). ChatGPT is always the
cool blue, Gemini always the warm orange. Charts are transparent so the slide
background shows through.
"""
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle
from PIL import Image, ImageFilter

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deck" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
FONTS = Path("/root/.claude/skills/synced/b369ceb5-0d4a-4716-a1b3-86b472a951f3_aa0f57f0-748c-4347-98c2-db2d72546fb6/canvas-design/canvas-fonts")
for f in ["InstrumentSans-Regular.ttf", "InstrumentSans-Bold.ttf", "DMMono-Regular.ttf"]:
    font_manager.fontManager.addfont(str(FONTS / f))
SANS, MONO = "Instrument Sans", "DM Mono"

BG = "#0B0C0E"
INK = "#ECE8E1"
SEC = "#A19D95"
MUTE = "#7E7A73"
HAIR = "#2A2B2E"
GREY = "#4A4946"
GPT = "#4F86E8"
GEM = "#E0643C"

plt.rcParams.update({"font.family": SANS, "text.color": INK, "axes.edgecolor": HAIR,
                     "savefig.transparent": True})
P = ROOT / "data" / "processed"
I = ROOT / "data" / "interim"


def canvas(w, h):
    """Figure in display pixels (rendered at 2x). Axes cover the full figure in pixel units."""
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")
    return fig, ax


def save(fig, name):
    fig.savefig(OUT / name, dpi=200, transparent=True)
    plt.close(fig)


def t(ax, x, y, s, size=20, color=INK, font=SANS, ha="left", va="center", weight="normal", alpha=1):
    ax.text(x, y, s, fontsize=size * 0.72, color=color, family=font, ha=ha, va=va,
            fontweight=weight, alpha=alpha)


def pct(v):
    return f"{int(v * 100 + 0.5)}%"


# ---------- backgrounds ----------
def grain_background(name, arc=False):
    w, h = 1920, 1080
    rng = np.random.default_rng(9)
    base = np.zeros((h, w, 3), np.float32) + np.array([11, 12, 14], np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    base *= (1 - 0.35 * np.clip(r - 0.55, 0, 1))[..., None]
    if arc:
        cx, cy, R = 1500, 2350, 1700
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) - R
        limb = np.exp(-np.abs(d) / 1.2) * 205 + np.exp(-np.clip(-d, 0, None) / 40) * (d < 0) * 10
        halo = np.exp(-np.clip(d, 0, None) / 90) * (d >= 0) * 16
        light = np.clip((xx - 300) / 1600, 0, 1) ** 1.6
        add = (limb + halo) * light
        base += add[..., None] * np.array([0.93, 0.91, 0.88], np.float32)
        inside = d < -1.5
        base[inside] = base[inside] * 0.35
    noise = rng.normal(0, 5.0, (h, w, 1)).astype(np.float32)
    img = np.clip(base + noise, 0, 255).astype(np.uint8)
    Image.fromarray(img).filter(ImageFilter.GaussianBlur(0.35)).save(OUT / name)


# ---------- charts ----------
def dumbbell():
    rows = [("BCA", .45, .65), ("Bank Jago", .50, .60), ("SeaBank", .50, .55), ("BRI", .30, .30),
            ("Bank Mandiri", .15, .40), ("Krom Bank", .15, .35), ("BNI", .15, .25),
            ("Bank Neo Commerce", .20, .20), ("Bank BTPN (Jenius)", 0, .25), ("Superbank", 0, .20)]
    w, h = 1560, 720
    fig, ax = canvas(w, h)
    x0, x1, vmax, y0, step = 330, 1500, 0.7, 120, 58
    X = lambda v: x0 + v / vmax * (x1 - x0)
    for tk in [0, .2, .4, .6]:
        ax.plot([X(tk)] * 2, [y0 - 30, y0 + step * 9 + 24], color=HAIR, lw=1)
        t(ax, X(tk), y0 - 52, f"{int(tk*100)}%", 19, MUTE, MONO, "center")
    ax.scatter([20], [30], s=110, color=GPT, zorder=3)
    t(ax, 40, 30, "ChatGPT", 19, SEC)
    ax.scatter([190], [30], s=110, facecolor="none", edgecolor=GEM, lw=2.4, zorder=3)
    t(ax, 210, 30, "Gemini", 19, SEC)
    t(ax, 380, 30, "share of each engine's 20 answers that name the bank", 19, MUTE)
    for i, (b, c, g) in enumerate(rows):
        y = y0 + i * step
        top = i < 3
        t(ax, 0, y, b, 22, INK if top else SEC)
        ax.plot([X(c), X(g)], [y, y], color=SEC if top else GREY, lw=1.6, solid_capstyle="round")
        ax.scatter([X(g)], [y], s=200, facecolor=BG, edgecolor=GEM, lw=2.6, zorder=3)
        ax.scatter([X(c)], [y], s=140, color=GPT, zorder=4)
        if c == g:
            t(ax, X(c) + 26, y, f"{pct(c)} in both", 19, MUTE, MONO)
        elif top:
            t(ax, X(g) + 26, y, pct(g), 19, GEM, MONO)
            t(ax, X(c) - 26, y, pct(c), 19, GPT, MONO, "right")
    save(fig, "c01_mentions_by_engine.png")


def general_prompts():
    a = pd.read_csv(I / "answers.csv")
    m = pd.read_csv(I / "mentions.csv")
    digital = {1, 4, 10, 11, 17, 20, 3, 9, 13, 14}
    g = a[~a.prompt_no.isin(digital)]
    r = (m[m.answer_id.isin(g.answer_id)].drop_duplicates(["answer_id", "brand"]).brand.value_counts() / len(g))
    r = r[r.index.isin(["BCA", "Bank Jago", "SeaBank", "BRI", "BNI", "Bank Mandiri"])].sort_values(ascending=False)
    w, h = 1100, 470
    fig, ax = canvas(w, h)
    x0, x1, y0, step = 230, 1000, 40, 72
    for i, (b, v) in enumerate(r.items()):
        y = y0 + i * step
        hi = b in ("Bank Jago", "SeaBank")
        t(ax, 0, y, b, 22, INK if hi else SEC)
        ax.add_patch(Rectangle((x0, y - 9), (x1 - x0), 18, color=HAIR, lw=0))
        ax.add_patch(Rectangle((x0, y - 9), (x1 - x0) * v, 18, color=INK if hi else GREY, lw=0))
        t(ax, x0 + (x1 - x0) * v + 16, y, pct(v), 20, INK if hi else SEC, MONO)
    t(ax, 0, h - 20, "20 answers to the 10 prompts that do not mention digital banks or apps", 19, MUTE)
    save(fig, "c02_general_prompts.png")


def heatmap():
    b = pd.read_csv(P / "brand_pillar.csv")
    b = b[b.engine == "All"]
    banks = ["BCA", "Bank Jago", "SeaBank", "BRI", "Bank Mandiri", "Krom Bank", "BNI", "Bank Neo Commerce"]
    short = {"Bank Jago": "Jago", "Bank Mandiri": "Mandiri", "Krom Bank": "Krom", "Bank Neo Commerce": "Neo Commerce"}
    pill = ["Fees & rates", "Digital experience", "Safety & security", "Service", "Trust"]
    names = {"Fees & rates": "Fees and rates", "Digital experience": "Digital experience",
             "Safety & security": "Safety and security", "Service": "Service", "Trust": "Trust"}
    pv = b.pivot(index="pillar", columns="brand", values="mention_rate")
    nn = b.groupby("pillar").n.first()
    w, h = 1640, 560
    fig, ax = canvas(w, h)
    x0, y0, cw, ch, gap = 330, 70, 160, 86, 4
    for j, bk in enumerate(banks):
        t(ax, x0 + j * cw + cw / 2, 26, short.get(bk, bk), 19, SEC, ha="center")
    for i, p in enumerate(pill):
        y = y0 + i * ch
        t(ax, 0, y + ch / 2, names[p], 21, INK)
        t(ax, 0, y + ch / 2 + 26, f"{nn[p]} answers", 19, MUTE, MONO)
        row = pv.loc[p, banks]
        lead = row.max()
        for j, bk in enumerate(banks):
            v = row[bk]
            x = x0 + j * cw
            ax.add_patch(Rectangle((x + gap / 2, y + gap / 2), cw - gap, ch - gap, color=INK, alpha=0.06 + 0.8 * v, lw=0))
            if v == lead:
                ax.add_patch(Rectangle((x + gap / 2, y + gap / 2), cw - gap, ch - gap, fill=False, ec=INK, lw=2.2))
            t(ax, x + cw / 2, y + ch / 2, pct(v), 20, BG if v >= 0.5 else INK, MONO, "center")
    save(fig, "c03_pillar_heatmap.png")


def venn():
    w, h = 1200, 640
    fig, ax = canvas(w, h)
    only_g, both, only_m = 25, 21, 51
    rl, rr = 215 * np.sqrt((only_g + both) / 72), 215
    cy, cxl, cxr = 330, 430, 430 + rl + rr - 150
    ax.add_patch(Circle((cxl, cy), rl, fill=False, ec=GPT, lw=2.4))
    ax.add_patch(Circle((cxr, cy), rr, fill=False, ec=GEM, lw=2.4))
    mid = (cxl + rl + cxr - rr) / 2
    t(ax, cxl - rl * 0.38, cy - 8, str(only_g), 66, INK, MONO, "center")
    t(ax, cxl - rl * 0.38, cy + 52, "ChatGPT only", 18, SEC, ha="center")
    t(ax, mid, cy - 8, str(both), 66, INK, MONO, "center")
    t(ax, mid, cy + 52, "both", 18, SEC, ha="center")
    t(ax, cxr + rr * 0.32, cy - 8, str(only_m), 66, INK, MONO, "center")
    t(ax, cxr + rr * 0.32, cy + 52, "Gemini only", 18, SEC, ha="center")
    t(ax, w / 2, h - 22, "97 cited sites, counted once each", 19, MUTE, ha="center")
    save(fig, "c04_site_overlap.png")


def source_mix():
    d = pd.read_csv(P / "domain_type_mix.csv")
    d = d[(d.pillar == "All") & (d.engine != "All")]
    groups = [("Bank websites", ["bank_official"], 0.92), ("Regulators", ["regulator"], 0.62),
              ("Fintech platforms", ["fintech_platform"], 0.40), ("Blogs and comparison", ["blog_aggregator"], 0.28),
              ("News", ["news_media"], 0.18), ("Other", ["forum_ugc", "other", "app_store"], 0.10)]
    w, h = 1640, 470
    fig, ax = canvas(w, h)
    x0, W, bh = 200, 1420, 60
    for k, (e, col) in enumerate([("ChatGPT", GPT), ("Gemini", GEM)]):
        y = 90 + k * 170
        ax.scatter([10], [y + bh / 2], s=120, color=col)
        t(ax, 32, y + bh / 2, e, 24, INK)
        sub = d[d.engine == e]
        tot = sub.citations.sum()
        acc = 0
        for name, types, a in groups:
            v = sub[sub.domain_type.isin(types)].citations.sum() / tot
            ww = v * W
            if ww > 0:
                ax.add_patch(Rectangle((x0 + acc + 1.5, y), max(ww - 3, 0.5), bh, color=INK, alpha=a, lw=0))
                if v >= 0.05:
                    t(ax, x0 + acc + ww / 2, y - 22, pct(v), 18, INK, MONO, "center")
            acc += ww
    for i, (name, _, a) in enumerate(groups):
        x = i * 274
        ax.add_patch(Rectangle((x, h - 46), 20, 20, color=INK, alpha=a, lw=0))
        t(ax, x + 30, h - 36, name, 19, SEC)
    save(fig, "c05_source_mix.png")


def third_party_sites():
    rows = [("fazz.com", 15, 0), ("akulaku.com", 14, 0), ("zaipad.com", 13, 0), ("kawula.id", 6, 1),
            ("finance.detik.com", 5, 0), ("vida.id", 4, 0), ("keuangan.kontan.co.id", 4, 2)]
    c = pd.read_csv(I / "citations.csv")
    x = c.groupby(["domain", "engine"]).answer_id.nunique().unstack(fill_value=0)
    rows = [(d, int(x.loc[d, "Gemini"]), int(x.loc[d, "ChatGPT"])) for d, _, _ in rows]
    w, h = 1560, 640
    fig, ax = canvas(w, h)
    x0, x1, y0, step = 380, 1440, 70, 78
    X = lambda v: x0 + v / 20 * (x1 - x0)
    for tk in [0, 5, 10, 15, 20]:
        ax.plot([X(tk)] * 2, [y0 - 30, y0 + step * 6 + 34], color=HAIR, lw=1)
        t(ax, X(tk), y0 - 50, str(tk), 19, MUTE, MONO, "center")
    for i, (d, gm, gp) in enumerate(rows):
        y = y0 + i * step
        top = i < 3
        t(ax, 0, y, d, 21, INK if top else SEC, MONO)
        ax.add_patch(Rectangle((x0, y - 16), X(gm) - x0, 14, color=GEM, lw=0))
        t(ax, X(gm) + 14, y - 9, str(gm), 19, INK if top else SEC, MONO)
        if gp:
            ax.add_patch(Rectangle((x0, y + 4), X(gp) - x0, 14, color=GPT, lw=0))
            t(ax, X(gp) + 14, y + 11, str(gp), 19, SEC, MONO)
        else:
            t(ax, x0 + 4, y + 11, "0", 19, GPT, MONO)
    t(ax, x0, h - 22, "number of answers (out of 20 per engine) that cite the site", 19, MUTE)
    ax.add_patch(Rectangle((x1 - 330, h - 30), 18, 14, color=GEM, lw=0))
    t(ax, x1 - 305, h - 23, "Gemini", 19, SEC)
    ax.add_patch(Rectangle((x1 - 190, h - 30), 18, 14, color=GPT, lw=0))
    t(ax, x1 - 165, h - 23, "ChatGPT", 19, SEC)
    save(fig, "c06_third_party_sites.png")


def sov_gap():
    s = pd.read_csv(P / "source_sov.csv").set_index("brand")
    banks = ["Bank Jago", "BCA", "BRI", "Bank Neo Commerce", "SeaBank", "BNI", "Krom Bank", "Bank Mandiri"]
    w, h = 1300, 640
    fig, ax = canvas(w, h)
    xm, scale, y0, step = 760, 62, 60, 70
    ax.plot([xm, xm], [y0 - 40, y0 + step * 7 + 30], color=SEC, lw=1.2)
    t(ax, xm - 16, y0 - 52, "sources mention it more", 19, MUTE, ha="right")
    t(ax, xm + 16, y0 - 52, "answers mention it more", 19, MUTE)
    for i, b in enumerate(banks):
        y = y0 + i * step
        v = s.loc[b, "sov_gap"] * 100
        hi = b in ("Bank Jago", "BCA", "Bank Mandiri")
        t(ax, 0, y, b, 22, INK if hi else SEC)
        x = xm if v >= 0 else xm + v * scale
        ax.add_patch(Rectangle((x, y - 15), abs(v) * scale, 30, color=INK if v >= 0 else GREY,
                               alpha=1 if hi else 0.55, lw=0))
        lab = f"{v:+.1f} pts"
        if v >= 0:
            t(ax, xm + v * scale + 14, y, lab, 19, INK if hi else SEC, MONO)
        else:
            t(ax, xm + v * scale - 14, y, lab, 19, INK if hi else SEC, MONO, "right")
    save(fig, "c07_sov_gap.png")


def intents():
    rows = [("Best", 1.0, 16), ("Decision brief", 1.0, 8), ("Compare", .75, 8), ("Informational", .5, 2), ("How-to", 1 / 6, 6)]
    w, h = 1150, 470
    fig, ax = canvas(w, h)
    x0, x1, y0, step = 250, 1000, 40, 82
    for i, (n, v, k) in enumerate(rows):
        y = y0 + i * step
        hi = n == "How-to"
        t(ax, 0, y, n, 22, INK if hi else SEC)
        t(ax, 0, y + 28, f"{k} answers", 19, MUTE, MONO)
        ax.add_patch(Rectangle((x0, y - 9), x1 - x0, 18, color=HAIR, lw=0))
        ax.add_patch(Rectangle((x0, y - 9), (x1 - x0) * v, 18, color=INK if hi else GREY, lw=0))
        t(ax, x1 + 20, y, pct(v), 22, INK if hi else SEC, MONO)
    t(ax, 0, h - 16, "share of answers that name at least one bank", 19, MUTE)
    save(fig, "c08_intents.png")


def sentiment_strip():
    counts = [("positive", 117, INK, 1.0), ("neutral", 14, GREY, 1.0), ("mixed", 6, SEC, 0.0), ("negative", 0, INK, 0)]
    w, h = 1640, 210
    fig, ax = canvas(w, h)
    per_row, size, gapx = 46, 26, 9
    k = 0
    for name, n, col, fill in counts:
        for _ in range(n):
            r, c = divmod(k, per_row)
            x, y = c * (size + gapx), 10 + r * (size + gapx)
            if fill:
                ax.add_patch(Rectangle((x, y), size, size, color=col, lw=0))
            else:
                ax.add_patch(Rectangle((x + 1, y + 1), size - 2, size - 2, fill=False, ec=col, lw=1.6))
            k += 1
    lx = 0
    for name, n, col, fill in counts:
        if fill:
            ax.add_patch(Rectangle((lx, h - 40), 20, 20, color=col, lw=0))
        else:
            ax.add_patch(Rectangle((lx + 1, h - 39), 18, 18, fill=False, ec=col if n else MUTE, lw=1.4))
        t(ax, lx + 32, h - 30, f"{n} {name}", 21, SEC, MONO)
        lx += 280
    save(fig, "c09_sentiment.png")


def dead_links():
    w, h = 1640, 340
    fig, ax = canvas(w, h)
    size, gap = 22, 8

    def block(x0, n, dead, cols, label, sub, hi):
        for i in range(n):
            r, c = divmod(i, cols)
            x, y = x0 + c * (size + gap), 90 + r * (size + gap)
            if i < dead:
                ax.add_patch(Rectangle((x, y), size, size, color=INK, lw=0))
            else:
                ax.add_patch(Rectangle((x, y), size, size, color=GREY, alpha=0.75, lw=0))
        t(ax, x0, 22, label, 22, INK)
        t(ax, x0, 58, sub, 21, INK if hi else SEC, MONO)

    block(0, 179, 0, 30, "179 direct links", "0 dead", False)
    block(1110, 21, 13, 7, "21 links wrapped in google.com/search", "13 dead", True)
    ax.add_patch(Rectangle((1110, h - 36), 20, 20, color=INK, lw=0))
    t(ax, 1140, h - 26, "dead", 19, SEC)
    ax.add_patch(Rectangle((1240, h - 36), 20, 20, color=GREY, alpha=0.75, lw=0))
    t(ax, 1270, h - 26, "live", 19, SEC)
    save(fig, "c10_dead_links.png")


def schema():
    sc = pd.read_csv(P / "schema.csv").set_index("domain_type")
    mix = pd.read_csv(P / "domain_type_mix.csv")
    mix = mix[(mix.engine == "All") & (mix.pillar == "All")].set_index("domain_type")
    rows = [("News", "news_media"), ("Fintech platforms", "fintech_platform"), ("Blogs and comparison", "blog_aggregator"),
            ("Bank websites", "bank_official"), ("Regulators", "regulator")]
    w, h = 1640, 520
    fig, ax = canvas(w, h)
    a0, a1, b0, b1, y0, step = 330, 900, 1050, 1620, 90, 80
    t(ax, a0, 20, "pages that carry schema markup", 18, MUTE)
    t(ax, b0, 20, "share of all citations", 18, MUTE)
    for i, (n, k) in enumerate(rows):
        y = y0 + i * step
        hi = k in ("bank_official", "regulator")
        t(ax, 0, y, n, 22, INK if hi else SEC)
        v = sc.loc[k, "any_jsonld"]
        u = mix.loc[k, "share"]
        ax.plot([a0, a1], [y, y], color=HAIR, lw=1.2)
        ax.scatter([a0 + (a1 - a0) * v], [y], s=170, color=INK if hi else GREY, zorder=3)
        t(ax, a0 + (a1 - a0) * v + (22 if v < .8 else -22), y - 30, pct(v), 18, INK if hi else SEC, MONO,
          "left" if v < .8 else "right")
        ax.add_patch(Rectangle((b0, y - 9), (b1 - b0), 18, color=HAIR, lw=0))
        ax.add_patch(Rectangle((b0, y - 9), (b1 - b0) * u / 0.5, 18, color=INK if hi else GREY, lw=0))
        t(ax, b0 + (b1 - b0) * u / 0.5 + 14, y, pct(u), 18, INK if hi else SEC, MONO)
    t(ax, b0, h - 18, "scale ends at 50%", 19, MUTE)
    save(fig, "c11_schema.png")


def dates():
    r = pd.read_csv(P / "recency.csv")
    r = r[(r.cut == "engine") & (r.value == "All") & (r.basis == "structured dates only")].set_index("group")
    order = [("0-30", "0 to 30 days"), ("31-180", "1 to 6 months"), ("181-365", "6 to 12 months"), (">365", "over a year"),
             ("unknown", "no structured date")]
    alphas = [0.95, 0.7, 0.5, 0.32, 0.0]
    w, h = 1640, 200
    fig, ax = canvas(w, h)
    acc, tot = 0, r.citations.sum()

    def swatch(x, y, a):
        if a:
            ax.add_patch(Rectangle((x, y), 22, 22, color=INK, alpha=a, lw=0))
        else:
            ax.add_patch(Rectangle((x, y), 22, 22, fill=False, ec=GREY, lw=1.4, hatch="////"))

    for (k, lab), a in zip(order, alphas):
        ww = r.loc[k, "citations"] / tot * w
        if a:
            ax.add_patch(Rectangle((acc + 1.5, 10), ww - 3, 60, color=INK, alpha=a, lw=0))
        else:
            ax.add_patch(Rectangle((acc + 1.5, 10), ww - 3, 60, fill=False, ec=GREY, lw=1.4, hatch="////"))
        acc += ww
    for i, ((k, lab), a) in enumerate(zip(order, alphas)):
        x = i * 328
        swatch(x, 112, a)
        t(ax, x + 34, 123, f"{int(r.loc[k, 'citations'])}", 22, INK, MONO)
        t(ax, x + 34, 160, lab, 19, SEC)
    save(fig, "c12_dates.png")


def funnel():
    rows = [("citations", 399), ("unique pages", 243), ("readable pages", 195), ("pages that name a bank", 148)]
    w, h = 1640, 400
    fig, ax = canvas(w, h)
    W, step = 1180, 92
    for i, (n, v) in enumerate(rows):
        y = 20 + i * step
        ax.add_patch(Rectangle((0, y), W * v / 399, 54, color=INK, alpha=0.92 - i * 0.2, lw=0))
        t(ax, W * v / 399 + 18, y + 27, f"{v}", 30, INK, MONO)
        t(ax, W * v / 399 + 108, y + 27, n, 20, SEC)
    save(fig, "c13_funnel.png")


def vis_gauges():
    v = pd.read_csv(P / "vis.csv")
    v = v[v.engine == "All"].sort_values("vis", ascending=False).head(4)
    w, h = 1640, 420
    fig, ax = canvas(w, h)
    x0, x1 = 300, 1500
    X = lambda s: x0 + (s - 50) / 50 * (x1 - x0)
    for tk in [50, 60, 70, 80, 90, 100]:
        ax.plot([X(tk)] * 2, [36, 380], color=HAIR, lw=1)
        t(ax, X(tk), 14, str(tk), 19, MUTE, MONO, "center")
    for i, r in enumerate(v.itertuples()):
        y = 80 + i * 92
        t(ax, 0, y, r.brand, 24, INK if i == 0 else SEC)
        ax.plot([x0, X(r.vis)], [y, y], color=INK if i == 0 else GREY, lw=3, solid_capstyle="butt")
        ax.plot([X(r.vis)] * 2, [y - 20, y + 20], color=INK, lw=2.4)
        t(ax, X(r.vis) + 20, y, f"{r.vis:.1f}", 26, INK if i == 0 else SEC, MONO)
    t(ax, x0, h - 12, "axis starts at 50; scores run from 0 to 100", 19, MUTE)
    save(fig, "c14_vis.png")


def overlap_benchmark():
    rows = [("0.05  our pages", 0.045, INK), ("0.119  Writesonic, ChatGPT vs Gemini", 0.119, SEC), ("0.22  our sites", 0.216, INK)]
    w, h = 1640, 300
    fig, ax = canvas(w, h)
    x0, x1 = 40, 1600
    X = lambda v: x0 + v / 0.25 * (x1 - x0)
    ax.plot([x0, x1], [150, 150], color=SEC, lw=1.2)
    for tk in [0, .05, .1, .15, .2, .25]:
        ax.plot([X(tk)] * 2, [143, 157], color=SEC, lw=1)
        t(ax, X(tk), 190, f"{tk:.2f}", 19, MUTE, MONO, "center")
    for i, (n, v, col) in enumerate(rows):
        ax.scatter([X(v)], [150], s=260, color=col if col == INK else BG, edgecolor=col, lw=2.4, zorder=3)
        t(ax, X(v), 100 if i != 1 else 230, n, 21, INK if col == INK else SEC, MONO, "center")
    t(ax, x0, h - 14, "Jaccard overlap: shared items divided by all items cited by either engine", 19, MUTE)
    save(fig, "c15_overlap_benchmark.png")


def pipeline():
    steps = [("01", "Parse", "40 answers"), ("02", "Sentences", "857 sentences"), ("03", "Bank mentions", "427 mentions"),
             ("04", "Crawl", "243 pages"), ("05", "Labels", "137 sentiment pairs"), ("06", "Metrics", "16 tables")]
    w, h = 1640, 260
    fig, ax = canvas(w, h)
    cw = 1640 / 6
    ax.plot([0, 1640], [70, 70], color=HAIR, lw=1.2)
    for i, (n, s, c) in enumerate(steps):
        x = i * cw
        ax.scatter([x + 6], [70], s=60, color=INK, zorder=3)
        t(ax, x, 26, n, 19, MUTE, MONO)
        t(ax, x, 122, s, 26, INK)
        t(ax, x, 168, c, 18, SEC, MONO)
    save(fig, "c16_pipeline.png")


def shift():
    w, h = 900, 420
    fig, ax = canvas(w, h)
    for i, (lab, v) in enumerate([("one year earlier", .14), ("in the study", .24)]):
        x = 60 + i * 380
        bh = v / .3 * 300
        ax.add_patch(Rectangle((x, 340 - bh), 200, bh, color=INK, alpha=0.45 + i * 0.5, lw=0))
        t(ax, x + 100, 340 - bh - 34, pct(v), 34, INK, MONO, "center")
        t(ax, x + 100, 380, lab, 18, SEC, ha="center")
    save(fig, "c17_info_seeking.png")


if __name__ == "__main__":
    grain_background("bg_grain.png")
    grain_background("bg_horizon.png", arc=True)
    for f in [dumbbell, general_prompts, heatmap, venn, source_mix, third_party_sites, sov_gap, intents,
              sentiment_strip, dead_links, schema, dates, funnel, vis_gauges, overlap_benchmark, pipeline, shift]:
        f()
    print(sorted(p.name for p in OUT.iterdir()))

"""Deck charts. One lit subject per chart, everything else recessive (deck/design-philosophy.md)."""
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle  # noqa: E402

from deck.fmt import num, pct  # noqa: E402
from deck.theme import C, MONO, SANS, register_fonts  # noqa: E402

LAST_DATA: dict = {}
DPI_SCALE = 2
ENGINE_COLOR = {"ChatGPT": C["gpt"], "Gemini": C["gem"]}
TYPE_LABEL = {"bank_official": "Bank websites", "regulator": "Regulators", "fintech_platform": "Fintech platforms",
              "blog_aggregator": "Blogs and comparison sites", "news_media": "News media",
              "forum_ugc": "Forums", "app_store": "App stores", "other": "Other"}
PAGE_LABEL = {
    "https://akulaku.com/blog/perbandingan-bank-digital-terbaik-2026": "akulaku.com  ·  digital bank comparison 2026",
    "https://seabank.co.id/produk-layanan/digital/tabungan": "seabank.co.id  ·  savings product page",
    "https://zaipad.com/bank-digital-terbaik-di-indonesia": "zaipad.com  ·  best digital banks in Indonesia",
    "https://seabank.co.id": "seabank.co.id  ·  home page",
    "https://lps.go.id": "lps.go.id  ·  home page",
    "https://kawula.id/rekomendasi-bank-digital-terbaik": "kawula.id  ·  digital bank recommendations",
    "https://fazz.com/id/newsroom/fazza/bank-digital-tanpa-biaya-admin": "fazz.com  ·  digital banks with no admin fee",
    "https://fazz.com/id/newsroom/fazza/daftar-bank-digital-dengan-bunga-tertinggi-2026":
        "fazz.com  ·  digital banks with the highest rates",
}


def _setup() -> None:
    register_fonts()
    plt.rcParams.update({
        "font.family": SANS, "font.size": 13, "text.color": C["text"],
        "axes.facecolor": C["bg"], "figure.facecolor": C["bg"], "savefig.facecolor": C["bg"],
        "axes.edgecolor": C["dim"], "axes.labelcolor": C["secondary"],
        "xtick.color": C["secondary"], "ytick.color": C["secondary"],
    })


def _fig(w_px: int, h_px: int, **kw):
    return plt.subplots(figsize=(w_px / 100, h_px / 100), dpi=100, **kw)


def _bare(ax) -> None:
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])


def _save(fig, path: Path) -> Path:
    fig.savefig(path, dpi=100 * DPI_SCALE)
    plt.close(fig)
    return path


def _mono(ax, x, y, s, **kw):
    kw.setdefault("color", C["secondary"])
    kw.setdefault("fontsize", 12)
    return ax.text(x, y, s, fontfamily=MONO, **kw)


def _top_banks(f: dict, k: int) -> list[str]:
    be = f["brand_engine"]
    a = be[(be.engine == "All") & (be.n_answers_mentioning > 0)]
    return list(a.sort_values(["mention_rate", "brand"], ascending=[False, True]).brand.head(k))


def chart_pawc_curve(f: dict, path: Path) -> Path:
    n = 10
    w = [math.exp(-i / n) for i in range(n)]
    fig, ax = _fig(1000, 500)
    fig.subplots_adjust(left=0.04, right=0.98, top=0.86, bottom=0.16)
    ax.bar(range(n), w, width=0.62, color=C["dim"])
    ax.bar([0], [w[0]], width=0.62, color=C["text"])
    xs = np.linspace(-0.3, n - 0.7, 200)
    ax.plot(xs, [math.exp(-max(x, 0) / n) for x in xs], color=C["secondary"], lw=1.2, ls=(0, (2, 3)))
    for i in (0, n - 1):
        _mono(ax, i, w[i] + 0.04, f"{w[i]:.2f}", ha="center", color=C["text"] if i == 0 else C["secondary"], fontsize=14)
    for i in range(n):
        _mono(ax, i, -0.09, f"s{i + 1}", ha="center", fontsize=12)
    _mono(ax, -0.4, 1.17, "weight = exp( - position / sentence count )", fontsize=14, color=C["text"])
    ax.set_xlim(-0.6, n - 0.4)
    ax.set_ylim(-0.14, 1.12)
    _bare(ax)
    return _save(fig, path)


def chart_prompt_grid(f: dict, path: Path) -> Path:
    g = f["prompt_grid"]
    pillars = ["Fees & rates", "Digital experience", "Safety & security", "Service", "Trust"]
    intents = ["Best", "Compare", "Decision brief", "How-to", "Informational"]
    fig, ax = _fig(1200, 560)
    fig.subplots_adjust(left=0.2, right=0.98, top=0.88, bottom=0.04)
    for j, it in enumerate(intents):
        ax.text(j, len(pillars) - 0.35, it, ha="center", va="bottom", fontsize=15, color=C["secondary"])
    for i, p in enumerate(pillars):
        y = len(pillars) - 1 - i
        ax.text(-0.62, y, p, ha="right", va="center", fontsize=15, color=C["secondary"])
        ax.plot([-0.5, len(intents) - 0.5], [y - 0.5, y - 0.5], color=C["dim"], lw=0.8)
        for j, it in enumerate(intents):
            nos = list(g[(g.pillar == p) & (g.intent == it)].prompt_no)
            for k, no in enumerate(nos):
                x = j + (k - (len(nos) - 1) / 2) * 0.3
                lit = no == 13
                ax.scatter([x], [y], s=620, facecolor=C["text"] if lit else C["bg"],
                           edgecolor=C["text"] if lit else C["secondary"], linewidth=1.2, zorder=2)
                _mono(ax, x, y, str(no), ha="center", va="center", fontsize=12,
                      color=C["bg"] if lit else C["text"], zorder=3)
    ax.set_xlim(-0.6, len(intents) - 0.4)
    ax.set_ylim(-0.6, len(pillars) - 0.1)
    ax.set_aspect("auto")
    _bare(ax)
    return _save(fig, path)


def chart_pipeline(f: dict, path: Path) -> Path:
    steps = [("answers", f["answers"]), ("sentences", f["sentences"]), ("bank mentions", f["mentions"]),
             ("citations", f["citations"]), ("unique pages", f["pages"]), ("readable pages", f["readable_pages"])]
    labels = ["Parse", "Split", "Match banks", "Extract sources", "Deduplicate", "Crawl"]
    fig, ax = _fig(1680, 600)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02)
    n = len(steps)
    for i, ((name, val), lab) in enumerate(zip(steps, labels)):
        x0, y = i * 1.0, n - 1 - i
        lit = i == n - 1
        ax.plot([x0, x0 + 0.84], [y, y], color=C["text"] if lit else C["secondary"], lw=2.4 if lit else 1.2)
        if i < n - 1:
            ax.plot([x0 + 0.84, x0 + 1.0], [y, y - 1], color=C["dim"], lw=1)
        _mono(ax, x0, y + 0.86, f"{i + 1:02d}  {lab.upper()}", fontsize=11.5)
        ax.text(x0, y + 0.14, f"{val:,}", fontsize=32, va="bottom", color=C["text"], alpha=1 if lit else 0.8,
                fontweight="bold" if lit else "normal")
        _mono(ax, x0, y - 0.34, name, fontsize=13, color=C["text"] if lit else C["secondary"])
    ax.set_xlim(-0.05, n)
    ax.set_ylim(-0.75, n + 0.1)
    _bare(ax)
    return _save(fig, path)


def chart_funnel(f: dict, path: Path) -> Path:
    rows = [("citations", f["citations"]), ("unique pages", f["pages"]), ("readable pages", f["readable_pages"]),
            ("readable pages that name a bank", f["readable_pages_with_bank"])]
    fig, ax = _fig(1000, 480)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.96, bottom=0.04)
    top = rows[0][1]
    for i, (name, v) in enumerate(rows):
        y = len(rows) - 1 - i
        w = v / top
        lit = i == len(rows) - 1
        ax.add_patch(Rectangle((-w / 2, y - 0.3), w, 0.6, facecolor=C["text"] if lit else C["dim"], lw=0))
        _mono(ax, 0.56, y, f"{v:,}", va="center", fontsize=18, color=C["text"])
        _mono(ax, 0.7, y, name, va="center", fontsize=13)
    ax.set_xlim(-0.55, 1.45)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    _bare(ax)
    return _save(fig, path)


def chart_mention_dots(f: dict, path: Path) -> Path:
    banks = _top_banks(f, 10)
    mr = f["mention_rate"]
    fig, ax = _fig(1180, 640)
    fig.subplots_adjust(left=0.25, right=0.97, top=0.86, bottom=0.04)
    for i, b in enumerate(banks):
        y = len(banks) - 1 - i
        g, m = mr[b].get("ChatGPT", 0), mr[b].get("Gemini", 0)
        lit = i < 3
        ax.text(-0.02, y, b, ha="right", va="center", fontsize=16, color=C["text"] if lit else C["secondary"])
        ax.plot([g, m], [y, y], color=C["dim"], lw=2, zorder=1)
        ax.scatter([m], [y], s=150, facecolor=C["bg"], edgecolor=C["gem"], linewidth=2.4, zorder=3)
        ax.scatter([g], [y], s=110, color=C["gpt"], zorder=4, edgecolor=C["bg"], linewidth=1.5)
        if g == m:
            _mono(ax, g + 0.025, y, f"{pct(g)} in both", va="center", fontsize=11)
    for t in (0, 0.2, 0.4, 0.6):
        ax.plot([t, t], [-0.6, len(banks) - 0.4], color=C["dim"], lw=0.6, zorder=0)
        _mono(ax, t, len(banks) - 0.1, f"{pct(t)}", ha="center", fontsize=12)
    ax.scatter([0.0], [len(banks) + 0.75], s=110, color=C["gpt"], clip_on=False)
    _mono(ax, 0.015, len(banks) + 0.75, "ChatGPT", va="center", color=C["text"], fontsize=13)
    ax.scatter([0.13], [len(banks) + 0.75], s=150, facecolor=C["bg"], edgecolor=C["gem"], linewidth=2.4, clip_on=False)
    _mono(ax, 0.145, len(banks) + 0.75, "Gemini", va="center", color=C["text"], fontsize=13)
    ax.set_xlim(-0.01, 0.72)
    ax.set_ylim(-0.6, len(banks) + 0.2)
    _bare(ax)
    return _save(fig, path)


def chart_vis_rank(f: dict, path: Path) -> Path:
    v = f["vis"].sort_values("vis", ascending=False).reset_index(drop=True)
    LAST_DATA["vis_rank"] = v
    fig, ax = _fig(1180, 700)
    fig.subplots_adjust(left=0.2, right=0.9, top=0.97, bottom=0.03)
    n = len(v)
    for i, r in v.iterrows():
        y = n - 1 - i
        lit = i == 0
        if r.low_n:
            ax.barh(y, r.vis, height=0.56, facecolor="none", edgecolor=C["secondary"], lw=1, ls=(0, (2, 2)))
        else:
            ax.barh(y, r.vis, height=0.56, color=C["text"] if lit else C["secondary"], alpha=1 if lit else 0.55)
        ax.text(-1.2, y, r.brand, ha="right", va="center", fontsize=13.5,
                color=C["text"] if lit else C["secondary"])
        _mono(ax, r.vis + 1, y, num(r.vis, 1), va="center", fontsize=12, color=C["text"] if lit else C["secondary"])
        if r.low_n:
            _mono(ax, 76, y, f"low n · {int(r.n_answers)} answer{'s' if r.n_answers > 1 else ''}",
                  va="center", fontsize=11, color=C["secondary"])
    ax.set_xlim(0, 112)
    ax.set_ylim(-0.6, n - 0.4)
    _bare(ax)
    return _save(fig, path)


def chart_wider_field(f: dict, path: Path) -> Path:
    be = f["brand_engine"]
    a = be[(be.engine == "All") & (be.n_answers_mentioning > 0)].sort_values(["mention_rate", "brand"], ascending=[False, True])
    banks = list(a.brand)
    named = {e: set(be[(be.engine == e) & (be.n_answers_mentioning > 0)].brand) for e in ("ChatGPT", "Gemini")}
    fig, ax = _fig(1680, 430)
    fig.subplots_adjust(left=0.08, right=0.99, top=0.98, bottom=0.36)
    for j, b in enumerate(banks):
        only_gem = b in named["Gemini"] and b not in named["ChatGPT"]
        only_gpt = b in named["ChatGPT"] and b not in named["Gemini"]
        for row, e in ((1, "ChatGPT"), (0, "Gemini")):
            on = b in named[e]
            lit = (only_gem and e == "Gemini") or (only_gpt and e == "ChatGPT")
            col = ENGINE_COLOR[e]
            ax.add_patch(Circle((j, row), 0.2, facecolor=col if on else C["bg"],
                                edgecolor=col if on else C["dim"], lw=1.2, alpha=1 if (lit or not on) else 0.5))
        ax.text(j, -0.45, b, rotation=40, ha="right", va="top", fontsize=12.5,
                color=C["text"] if (only_gem or only_gpt) else C["secondary"])
    _mono(ax, -0.6, 1, f"ChatGPT  {f['banks_gpt']}", ha="right", va="center", fontsize=13, color=C["text"])
    _mono(ax, -0.6, 0, f"Gemini  {f['banks_gem']}", ha="right", va="center", fontsize=13, color=C["text"])
    ax.set_xlim(-2.6, len(banks) - 0.4)
    ax.set_ylim(-0.5, 1.5)
    ax.set_aspect("equal")
    _bare(ax)
    return _save(fig, path)


def chart_pillar_heatmap(f: dict, path: Path) -> Path:
    banks = _top_banks(f, 8)
    pillars = ["Fees & rates", "Digital experience", "Safety & security", "Service", "Trust"]
    pr = f["pillar_rates"].pivot(index="pillar", columns="brand", values="mention_rate").reindex(index=pillars, columns=banks).fillna(0)
    top = pr.max(axis=1)
    fig, ax = _fig(1680, 560)
    fig.subplots_adjust(left=0.13, right=0.99, top=0.86, bottom=0.03)
    for i, p in enumerate(pillars):
        y = len(pillars) - 1 - i
        ax.text(-0.6, y, p, ha="right", va="center", fontsize=15, color=C["secondary"])
        for j, b in enumerate(banks):
            v = pr.loc[p, b]
            lead = v == top[p]
            ax.add_patch(FancyBboxPatch((j - 0.44, y - 0.4), 0.88, 0.8, boxstyle="round,pad=0,rounding_size=0.04",
                                        facecolor=C["text"], alpha=0.06 + 0.8 * v, lw=0))
            if lead:
                ax.add_patch(FancyBboxPatch((j - 0.44, y - 0.4), 0.88, 0.8, boxstyle="round,pad=0,rounding_size=0.04",
                                            facecolor="none", edgecolor=C["text"], lw=2))
            _mono(ax, j, y, f"{pct(v)}" if v else "·", ha="center", va="center", fontsize=14,
                  color=C["bg"] if v >= 0.5 else C["text"])
    for j, b in enumerate(banks):
        ax.text(j, len(pillars) - 0.35, b, ha="center", va="bottom", fontsize=14, color=C["secondary"])
    ax.set_xlim(-0.55, len(banks) - 0.45)
    ax.set_ylim(-0.5, len(pillars) - 0.1)
    _bare(ax)
    return _save(fig, path)


def chart_often_vs_early(f: dict, path: Path) -> Path:
    be = f["brand_engine"]
    a = be[(be.engine == "All") & (be.n_answers_mentioning >= 3)]
    fig, ax = _fig(1180, 640)
    fig.subplots_adjust(left=0.1, right=0.96, top=0.95, bottom=0.12)
    lit = set(a.sort_values("pawc", ascending=False).brand.head(1))
    for r in a.itertuples():
        on = r.brand in lit
        ax.scatter(r.mention_rate, r.pawc, s=130 if on else 80, color=C["text"] if on else C["secondary"],
                   edgecolor=C["bg"], linewidth=1.5, zorder=3, alpha=1 if on else 0.8)
        dx, dy, ha = {"Bank Jago": (-0.012, 0.0018, "right"), "Bank Saqu": (-0.012, -0.0035, "right"),
                      "Superbank": (0.0, 0.0028, "center"), "Bank BTPN": (0.012, -0.0032, "left")
                      }.get(r.brand, (0.012, 0.0018, "left"))
        ax.text(r.mention_rate + dx, r.pawc + dy, r.brand, fontsize=13, ha=ha,
                color=C["text"] if on else C["secondary"])
    for t in (0, 0.2, 0.4, 0.6):
        ax.axvline(t, color=C["dim"], lw=0.6, zorder=0)
        _mono(ax, t, -0.0085, f"{pct(t)}", ha="center", fontsize=12)
    for t in (0, 0.02, 0.04, 0.06):
        ax.axhline(t, color=C["dim"], lw=0.6, zorder=0)
        _mono(ax, -0.012, t, f"{t:.2f}", ha="right", va="center", fontsize=12)
    _mono(ax, 0.6, -0.0145, "named in this share of answers", ha="right", fontsize=12)
    _mono(ax, -0.058, 0.0735, "brand PAWC (how much, how early)", fontsize=12)
    ax.set_xlim(-0.06, 0.63)
    ax.set_ylim(-0.016, 0.076)
    _bare(ax)
    return _save(fig, path)


def chart_sentiment_marks(f: dict, path: Path) -> Path:
    sc = f["sentiment_counts"]
    seq = ["positive"] * sc["positive"] + ["neutral"] * sc["neutral"] + ["mixed"] * sc["mixed"]
    fig, ax = _fig(1680, 380)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0.03)
    per_row, fw, fh, gap_y = 46, 0.72, 1.3, 0.45
    rows = math.ceil(len(seq) / per_row)
    for i, s_ in enumerate(seq):
        x, y = i % per_row, (rows - 1 - i // per_row) * (fh + gap_y)
        if s_ == "positive":
            ax.add_patch(Rectangle((x, y), fw, fh, facecolor=C["secondary"], alpha=0.5, lw=0))
        elif s_ == "neutral":
            ax.add_patch(Rectangle((x, y), fw, fh, facecolor=C["dim"], lw=0))
        else:
            ax.add_patch(Rectangle((x + 0.05, y + 0.05), fw - 0.1, fh - 0.1, facecolor="none", edgecolor=C["secondary"], lw=1.2))
    total_h = rows * fh + (rows - 1) * gap_y
    x0 = per_row + 1.6
    ax.add_patch(Rectangle((x0, 0), 7.5, total_h, facecolor="none", edgecolor=C["text"], lw=1.6, ls=(0, (4, 3))))
    ax.text(x0 + 3.75, total_h / 2 + 0.35, "0", ha="center", va="center", fontsize=40, color=C["text"])
    _mono(ax, x0 + 3.75, total_h / 2 - 1.15, "negative", ha="center", va="center", fontsize=14, color=C["text"])
    _mono(ax, 0, -0.9, f"{sc['positive']} positive   ·   {sc['neutral']} neutral   ·   {sc['mixed']} mixed (outlined)",
          fontsize=13)
    ax.set_xlim(-0.4, x0 + 8)
    ax.set_ylim(-1.5, total_h + 0.3)
    ax.set_aspect("equal")
    _bare(ax)
    return _save(fig, path)


def chart_intent_named(f: dict, path: Path) -> Path:
    order = ["Best", "Decision brief", "Compare", "Informational", "How-to"]
    d = f["intent_named_share"]
    fig, ax = _fig(1100, 480)
    fig.subplots_adjust(left=0.2, right=0.9, top=0.96, bottom=0.04)
    for i, it in enumerate(order):
        y = len(order) - 1 - i
        share, n = d[it]
        lit = it == "How-to"
        ax.barh(y, 1, height=0.5, color=C["dim"], alpha=0.5)
        ax.barh(y, share, height=0.5, color=C["text"] if lit else C["secondary"])
        ax.text(-0.02, y, it, ha="right", va="center", fontsize=16, color=C["text"] if lit else C["secondary"])
        _mono(ax, 1.02, y, f"{pct(share)}  of {n}", va="center", fontsize=13, color=C["text"] if lit else C["secondary"])
    ax.set_xlim(0, 1.22)
    ax.set_ylim(-0.6, len(order) - 0.4)
    _bare(ax)
    return _save(fig, path)


def chart_source_mix(f: dict, path: Path) -> Path:
    order = ["bank_official", "regulator", "fintech_platform", "blog_aggregator", "news_media", "forum_ugc", "app_store", "other"]
    fig, ax = _fig(1680, 460)
    fig.subplots_adjust(left=0.09, right=0.99, top=0.9, bottom=0.04)
    for row, e in ((1.25, "ChatGPT"), (0, "Gemini")):
        mix = f["source_mix"][e]
        x = 0.0
        ax.text(-0.012, row, e, ha="right", va="center", fontsize=17, color=C["text"])
        for t in order:
            w = mix.get(t, 0)
            if not w:
                continue
            first_party = t in ("bank_official", "regulator")
            col = ENGINE_COLOR[e] if first_party else C["secondary"]
            alpha = (1 if t == "bank_official" else 0.6) if first_party else {"fintech_platform": 0.55, "blog_aggregator": 0.38,
                                                                               "news_media": 0.24}.get(t, 0.12)
            ax.add_patch(Rectangle((x, row - 0.28), w, 0.56, facecolor=col, alpha=alpha, edgecolor=C["bg"], lw=2))
            if w >= 0.06:
                _mono(ax, x + w / 2, row + 0.4, f"{pct(w)}", ha="center", fontsize=15, color=C["text"])
                ax.text(x + w / 2, row - 0.02, TYPE_LABEL[t], ha="center", va="center", fontsize=13.5,
                        color=C["bg"] if (first_party and t == "bank_official") else C["text"])
            x += w
        small = [f"{TYPE_LABEL[t].lower()} {pct(mix[t])}" for t in order if 0 < mix.get(t, 0) < 0.06]
        if small:
            _mono(ax, 1.0, row - 0.44, "smaller:  " + "  ·  ".join(small), ha="right", fontsize=11.5)
    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.6, 1.9)
    _bare(ax)
    return _save(fig, path)


def chart_overlap(f: dict, path: Path) -> Path:
    o = f["overlap"]
    fig, ax = _fig(1100, 560)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    r = 1.0
    ax.add_patch(Circle((-0.62, 0), r, facecolor="none", edgecolor=C["gpt"], lw=2.2))
    ax.add_patch(Circle((0.62, 0), r * 1.22, facecolor="none", edgecolor=C["gem"], lw=2.2))
    ax.text(-1.15, 0, str(o["sites_gpt_only"]), ha="center", va="center", fontsize=40, color=C["secondary"])
    ax.text(1.32, 0, str(o["sites_gem_only"]), ha="center", va="center", fontsize=40, color=C["secondary"])
    ax.text(-0.11, 0.08, str(o["sites_both"]), ha="center", va="center", fontsize=52, color=C["text"], fontweight="bold")
    _mono(ax, -0.11, -1.52, "cited by both", ha="center", va="center", fontsize=13, color=C["text"])
    ax.plot([-0.11, -0.11], [-0.45, -1.36], color=C["text"], lw=0.8)
    _mono(ax, -1.15, -0.42, "ChatGPT only", ha="center", fontsize=13)
    _mono(ax, 1.32, -0.42, "Gemini only", ha="center", fontsize=13)
    ax.set_xlim(-1.9, 2.1)
    ax.set_ylim(-1.7, 1.35)
    ax.set_aspect("equal")
    _bare(ax)
    return _save(fig, path)


def chart_mirror_sites(f: dict, path: Path) -> Path:
    t = f["top_sites"]
    fig, ax = _fig(1680, 660)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.02)
    n = len(t)
    gap = 9.0
    for i, r in t.iterrows():
        y = n - 1 - i
        ax.barh(y, -r.gpt, left=-gap, height=0.58, color=C["gpt"])
        ax.barh(y, r.gem, left=gap, height=0.58, color=C["gem"])
        ax.text(0, y, r.domain, ha="center", va="center", fontsize=14, color=C["text"])
        if r.gpt:
            _mono(ax, -gap - r.gpt - 0.6, y, str(r.gpt), ha="right", va="center", fontsize=12, color=C["text"])
        else:
            _mono(ax, -gap - 0.6, y, "0", ha="right", va="center", fontsize=12)
        if r.gem:
            _mono(ax, gap + r.gem + 0.6, y, str(r.gem), va="center", fontsize=12, color=C["text"])
        else:
            _mono(ax, gap + 0.6, y, "0", va="center", fontsize=12)
    _mono(ax, -gap, n - 0.1, "ChatGPT  citations", ha="right", fontsize=13, color=C["text"])
    _mono(ax, gap, n - 0.1, "Gemini  citations", fontsize=13, color=C["text"])
    ax.axvline(-gap, color=C["dim"], lw=0.8)
    ax.axvline(gap, color=C["dim"], lw=0.8)
    ax.set_xlim(-gap - 32, gap + 32)
    ax.set_ylim(-0.6, n + 0.5)
    _bare(ax)
    return _save(fig, path)


def chart_top_pages(f: dict, path: Path) -> Path:
    t = f["top_pages"]
    fig, ax = _fig(1680, 600)
    fig.subplots_adjust(left=0.38, right=0.97, top=0.95, bottom=0.04)
    n = len(t)
    for i, r in t.iterrows():
        y = n - 1 - i
        lit = r.gpt == 0
        ax.barh(y, r.gpt, height=0.56, color=C["gpt"], alpha=1)
        ax.barh(y, r.gem, left=r.gpt, height=0.56, color=C["gem"], alpha=1)
        ax.text(-0.3, y, PAGE_LABEL.get(r.url, r.url), ha="right", va="center", fontsize=14,
                color=C["text"] if lit else C["secondary"])
        _mono(ax, r.citations + 0.25, y, str(r.citations), va="center", fontsize=12, color=C["text"])
    for x, e in ((0, "ChatGPT"), (2.6, "Gemini")):
        ax.add_patch(Rectangle((x, n - 0.25), 0.35, 0.36, facecolor=ENGINE_COLOR[e], clip_on=False))
        _mono(ax, x + 0.5, n - 0.07, e, va="center", fontsize=12.5, color=C["text"])
    ax.set_xlim(0, 16)
    ax.set_ylim(-0.6, n + 0.2)
    _bare(ax)
    return _save(fig, path)


def chart_concentration(f: dict, path: Path) -> Path:
    fig, ax = _fig(1100, 360)
    fig.subplots_adjust(left=0.13, right=0.86, top=0.96, bottom=0.08)
    for row, e in ((1, "ChatGPT"), (0, "Gemini")):
        s = f["concentration"][e]
        ax.barh(row, 1, height=0.42, color=C["dim"], alpha=0.5)
        ax.barh(row, s, height=0.42, color=ENGINE_COLOR[e])
        ax.text(-0.02, row, e, ha="right", va="center", fontsize=17, color=C["text"])
        _mono(ax, 1.02, row, f"{pct(s)}", va="center", fontsize=22, color=C["text"])
    _mono(ax, 0, -0.55, "share of each engine's citations held by its top five sites", fontsize=12)
    ax.set_xlim(0, 1.15)
    ax.set_ylim(-0.7, 1.5)
    _bare(ax)
    return _save(fig, path)


def chart_sov_gap(f: dict, path: Path) -> Path:
    d = f["sov_gap"].copy()
    d["pts"] = d.sov_gap * 100
    d = d.sort_values("pts", ascending=False).reset_index(drop=True)
    fig, ax = _fig(1180, 600)
    fig.subplots_adjust(left=0.2, right=0.96, top=0.88, bottom=0.04)
    lit = {"Bank Jago", "BCA", "Bank Mandiri"}
    n = len(d)
    for i, r in d.iterrows():
        y = n - 1 - i
        on = r.brand in lit
        ax.barh(y, r.pts, height=0.56, color=C["text"] if (on and r.pts > 0) else (C["secondary"] if on else C["dim"]))
        ax.text(-10.2, y, r.brand, ha="right", va="center", fontsize=15, color=C["text"] if on else C["secondary"])
        lab = f"{r.pts:+.1f} pts"
        _mono(ax, r.pts + (0.25 if r.pts >= 0 else -0.25), y, lab, va="center", ha="left" if r.pts >= 0 else "right",
              fontsize=12.5, color=C["text"] if on else C["secondary"])
    ax.axvline(0, color=C["secondary"], lw=1)
    _mono(ax, 0.3, n - 0.05, "answers mention it more", fontsize=12)
    _mono(ax, -0.3, n - 0.05, "sources mention it more", ha="right", fontsize=12)
    ax.set_xlim(-10, 9)
    ax.set_ylim(-0.6, n + 0.3)
    _bare(ax)
    return _save(fig, path)


def chart_dead_links(f: dict, path: Path) -> Path:
    wd, wt, dd, dt = f["dead_links"]
    fig, ax = _fig(1180, 380)
    fig.subplots_adjust(left=0.33, right=0.86, top=0.95, bottom=0.08)
    rows = [("Wrapped in a Google redirect", wd, wt), ("Direct links", dd, dt)]
    for i, (name, d, t) in enumerate(rows):
        y = 1 - i
        ax.barh(y, 1, height=0.46, color=C["gem"], alpha=0.35)
        ax.barh(y, d / t, height=0.46, color=C["text"])
        ax.text(-0.02, y, name, ha="right", va="center", fontsize=16, color=C["text"])
        _mono(ax, 1.02, y, f"{d} of {t} dead", va="center", fontsize=14, color=C["text"])
    _mono(ax, 0, -0.62, "Gemini citations  ·  dead = HTTP 404 or an error page", fontsize=12)
    ax.set_xlim(0, 1.25)
    ax.set_ylim(-0.8, 1.5)
    _bare(ax)
    return _save(fig, path)


def chart_schema(f: dict, path: Path) -> Path:
    s = f["schema_by_type"]
    share = f["citation_share_by_type"]
    keep = ["bank_official", "regulator", "news_media", "blog_aggregator", "fintech_platform"]
    s = s[s.domain_type.isin(keep)].set_index("domain_type").reindex(keep)
    fig, ax = _fig(1180, 520)
    fig.subplots_adjust(left=0.28, right=0.95, top=0.86, bottom=0.04)
    for i, t in enumerate(keep):
        y = len(keep) - 1 - i
        lit = t == "bank_official"
        ax.barh(y, share[t], height=0.36, color=C["text"] if lit else C["secondary"], alpha=1 if lit else 0.55)
        ax.scatter([s.loc[t, "any_jsonld"]], [y], s=120, facecolor=C["bg"], edgecolor=C["text"] if lit else C["secondary"],
                   linewidth=2, zorder=3)
        ax.text(-0.02, y, TYPE_LABEL[t], ha="right", va="center", fontsize=15, color=C["text"] if lit else C["secondary"])
        _mono(ax, s.loc[t, "any_jsonld"] + 0.025, y + 0.22, f"schema {pct(s.loc[t, 'any_jsonld'])}", fontsize=11.5,
              color=C["text"] if lit else C["secondary"])
        _mono(ax, share[t] + 0.01, y - 0.32, f"cited {pct(share[t])}", fontsize=11.5, color=C["text"] if lit else C["secondary"])
    ax.add_patch(Rectangle((0.0, len(keep) + 0.05), 0.03, 0.22, facecolor=C["secondary"], clip_on=False))
    _mono(ax, 0.045, len(keep) + 0.08, "share of all citations", fontsize=12)
    ax.scatter([0.4], [len(keep) + 0.16], s=110, facecolor=C["bg"], edgecolor=C["secondary"], linewidth=2, clip_on=False)
    _mono(ax, 0.425, len(keep) + 0.08, "share of its readable pages with schema", fontsize=12)
    ax.set_xlim(0, 1.12)
    ax.set_ylim(-0.6, len(keep) - 0.3)
    _bare(ax)
    return _save(fig, path)


CHARTS = {
    "pawc_curve": chart_pawc_curve, "prompt_grid": chart_prompt_grid, "pipeline": chart_pipeline,
    "funnel": chart_funnel, "mention_dots": chart_mention_dots, "vis_rank": chart_vis_rank,
    "wider_field": chart_wider_field, "pillar_heatmap": chart_pillar_heatmap, "often_vs_early": chart_often_vs_early,
    "sentiment_marks": chart_sentiment_marks, "intent_named": chart_intent_named, "source_mix": chart_source_mix,
    "overlap": chart_overlap, "mirror_sites": chart_mirror_sites, "top_pages": chart_top_pages,
    "concentration": chart_concentration, "sov_gap": chart_sov_gap, "dead_links": chart_dead_links,
    "schema": chart_schema,
}


def render_all(facts: dict, out: Path) -> dict[str, Path]:
    _setup()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    return {k: fn(facts, out / f"{k}.png") for k, fn in CHARTS.items()}

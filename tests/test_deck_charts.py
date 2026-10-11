from PIL import Image

from deck import charts
from deck.facts import load

KEYS = ["pawc_curve", "prompt_grid", "pipeline", "funnel", "mention_dots", "vis_rank", "wider_field",
        "pillar_heatmap", "often_vs_early", "sentiment_marks", "intent_named", "source_mix", "overlap",
        "mirror_sites", "top_pages", "concentration", "sov_gap", "dead_links", "schema"]


def test_render_all_outputs(tmp_path):
    out = charts.render_all(load(), tmp_path)
    assert sorted(out) == sorted(KEYS)
    for k, p in out.items():
        w, h = Image.open(p).size
        assert w >= 1600, (k, w)


def test_low_sample_banks_are_marked(tmp_path):
    charts.render_all(load(), tmp_path)
    v = charts.LAST_DATA["vis_rank"]
    assert set(v[v.n_answers < 3].brand) == set(v[v.low_n].brand)
    assert v.low_n.sum() == 7


SINGLE_SERIES = ["vis_rank", "intent_named", "sov_gap", "dead_links", "schema", "funnel", "pawc_curve",
                 "pipeline", "sentiment_marks", "pillar_heatmap"]


def _amber_pixels(path, amber=(0xF2, 0xA5, 0x41), dist=30):
    import numpy as np
    a = np.asarray(Image.open(path).convert("RGBA")).astype(int)
    rgb, alpha = a[..., :3], a[..., 3]
    near = ((rgb - np.array(amber)) ** 2).sum(axis=-1) <= dist ** 2
    return int((near & (alpha > 0)).sum())


def test_single_series_charts_carry_no_amber(tmp_path):
    # Amber means ChatGPT. A single-series chart lights its mark in white, never amber.
    out = charts.render_all(load(), tmp_path)
    found = {k: _amber_pixels(out[k]) for k in SINGLE_SERIES}
    assert not any(found.values()), found


def test_engine_charts_still_use_amber(tmp_path):
    out = charts.render_all(load(), tmp_path)
    assert _amber_pixels(out["mention_dots"]) > 0

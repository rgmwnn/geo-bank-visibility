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

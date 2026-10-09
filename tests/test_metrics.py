import math

import pytest

from scripts.metrics import brand_pawc, compute_all, pawc_weight
from tests.mini import CFG, MINI

R = compute_all(MINI, CFG)


def row(table, **keys):
    df = R[table]
    for k, v in keys.items():
        df = df[df[k] == v]
    assert len(df) == 1, (table, keys, len(df))
    return df.iloc[0]


def test_pawc_weight():
    assert pawc_weight(0, 4) == 1.0 and pawc_weight(2, 4) == pytest.approx(math.exp(-0.5))


def test_brand_pawc_hand_value():
    # gpt-01 BCA in sentences 0 and 2: (10*1 + 10*e^-0.5) / 40 = 0.4016
    p = brand_pawc(MINI["sentences"], MINI["mentions"]).set_index(["answer_id", "brand"]).pawc
    assert p["gpt-01", "BCA"] == pytest.approx(0.40163, abs=1e-4)
    # gem-01 Jago twice in sentence 0 counts the sentence once: 10/40
    assert p["gem-01", "Bank Jago"] == pytest.approx(0.25)


def test_mention_rate_sov_pawc_by_engine():
    r = row("brand_engine", brand="BCA", engine="ChatGPT")
    assert (r.n, r.mention_rate, r.ai_sov) == (3, pytest.approx(2 / 3), pytest.approx(0.75))
    # (0.4016 + 0.25 + 0) / 3
    assert r.pawc == pytest.approx(0.21721, abs=1e-4)
    j = row("brand_engine", brand="Bank Jago", engine="Gemini")
    assert (j.mention_rate, j.ai_sov) == (pytest.approx(2 / 3), pytest.approx(0.6))
    # gem-01: first mention at sentence 0 -> 0/4; gem-02: 1/4 -> mean 0.125
    assert j.first_mention_pos == pytest.approx(0.125)
    assert (j.n_pos, j.n_mixed, j.sentiment_mean) == (1, 1, pytest.approx(0.5))


def test_pillar_and_intent_cuts():
    assert row("brand_pillar", brand="BCA", engine="All", pillar="Fees").n == 4
    assert row("brand_pillar", brand="BCA", engine="All", pillar="Fees").mention_rate == pytest.approx(0.75)
    assert row("brand_intent", brand="BCA", engine="ChatGPT", intent="Compare").mention_rate == 1.0


def test_no_brand_rate():
    assert row("no_brand_rate", engine="ChatGPT", intent="How-to").no_brand_rate == 1.0
    assert row("no_brand_rate", engine="Gemini", intent="How-to").no_brand_rate == 0.0


def test_domains_and_pages():
    a = row("domains", domain="a.id")
    assert (a.citations, a.gpt, a.gem, a.unique_pages, a.prompts) == (5, 3, 2, 2, 3)
    assert a.avg_rank == pytest.approx(1.2)
    top = R["pages_top"].iloc[0]
    assert (top.url, top.citations, top.engines) == ("https://a.id/1", 4, "ChatGPT+Gemini")
    assert set(R["cross_engine_pages"].url) == {"https://a.id/1", "https://b.id/1", "https://c.id/1"}
    assert row("authority_mix", engine="ChatGPT", authority_tier="High").citations == 3


def test_source_pawc_uses_threshold():
    # gpt-01 s1 (0.2) is below 0.30 and adds nothing; s0 and s2 go to a.id/1: 0.4016
    assert row("source_pawc_domain", domain="a.id", engine="ChatGPT").source_pawc == pytest.approx(0.40163, abs=1e-4)
    assert row("attribution_coverage", engine="ChatGPT").coverage == pytest.approx(2 / 12)


def test_unreadable_pages_excluded_everywhere():
    # gem-01 s1 points at the unreadable a.id/2, so Gemini coverage is 1/12 and a.id has no Gemini source PAWC
    assert row("attribution_coverage", engine="Gemini").coverage == pytest.approx(1 / 12)
    assert R["source_pawc_domain"].query("domain == 'a.id' and engine == 'Gemini'").empty
    # a.id/2's 10 Jago mentions are not counted. Page-weighted shares over the 4 readable pages with brands:
    # a1 BCA 1 | b1 BCA 0.2, Krom 0.8 | b2 Jago 1 | c1 Jago 1  ->  Jago (1 + 1) / 4 = 0.5
    j = row("source_sov", brand="Bank Jago")
    assert j.source_sov == pytest.approx(0.5) and j.source_sov_raw == pytest.approx(3 / 11)


def test_brand_only_in_pages_kept():
    k = row("source_sov", brand="Krom Bank")
    assert k.ai_sov == 0 and k.source_sov == pytest.approx(0.2) and k.sov_gap == pytest.approx(-0.2)


def test_long_document_does_not_dominate_source_sov():
    import copy
    inp = copy.deepcopy(MINI)
    inp["page_brand_counts"].loc[0, "count"] = 1000  # a.id/1 now mentions BCA 1000 times
    sov = compute_all(inp, CFG)["source_sov"].set_index("brand")
    assert sov.loc["BCA", "source_sov"] == pytest.approx(0.3)


def test_recency_groups():
    # ChatGPT readable citations: a1 (8 days) x2, b1 (161 days) x2, c1 (>365) x1
    assert row("recency", engine="ChatGPT", group="0-30").citations == 2
    assert row("recency", engine="ChatGPT", group="31-180").citations == 2
    assert row("recency", engine="ChatGPT", group=">365").citations == 1


def test_vis_equal_weights_and_low_n():
    b = row("vis", brand="BCA")
    # PAWC_norm 1, authority 6.2/8, sentiment (0.5+1)/2, diversity 1
    assert b.authority == pytest.approx(0.775) and b.sentiment_norm == pytest.approx(0.75)
    assert b.vis == pytest.approx(100 * (1 + 0.775 + 0.75 + 1) / 4)
    assert bool(b.low_n) is False
    v = row("vis_engine", brand="Bank Jago", engine="ChatGPT")
    assert v.n_answers == 1 and bool(v.low_n) is True


def test_soft_404_reason_reported():
    import copy
    inp = copy.deepcopy(MINI)
    inp["pages"] = inp["pages"].assign(soft_404=[False, False, False, True, False])
    inp["pages"].loc[3, "is_readable"] = False
    rd = compute_all(inp, CFG)["readability"]
    assert rd.query("cut == 'domain_type' and value == 'All' and reason == 'soft_404'").pages.iloc[0] == 1

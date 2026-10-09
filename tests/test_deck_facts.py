from deck.facts import load

F = load()


def test_known_counts():
    assert (F["answers"], F["sentences"], F["mentions"], F["citations"]) == (40, 857, 427, 399)
    assert (F["pages"], F["readable_pages"]) == (243, 195)
    assert (F["banks_gpt"], F["banks_gem"]) == (11, 18)
    assert F["sentiment_counts"] == {"positive": 117, "neutral": 14, "mixed": 6, "negative": 0}
    assert F["dead_links"] == (13, 21, 0, 179)
    assert F["overlap"]["sites_both"] == 21 and F["overlap"]["pages_both"] == 11
    assert round(F["mention_rate"]["BCA"]["All"], 3) == 0.55


def test_cold_open_prompt_13_has_banks_from_both_engines():
    c = F["cold_open"]
    assert c["prompt"].startswith("Saya freelancer")
    assert c["banks_gpt"] and c["banks_gem"]


def test_readable_pages_naming_a_bank():
    assert F["readable_pages_with_bank"] == 148

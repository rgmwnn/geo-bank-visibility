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


def test_prompt_design_counts():
    assert (F["prompts"], F["pillars"], F["intents"], F["citations_per_answer"]) == (20, 5, 5, 10)
    assert F["branded_prompts"] == 3
    assert len(F["digital_prompts"]) == 10


def test_bank_website_facts_for_the_web_team():
    from deck.facts import load
    w = load()["bank_site"]
    assert w["pages"] == 121
    assert w["dead_pages"] == 2 and w["dead_citations"] == 4
    assert w["rendered"] == 12 and "https://seabank.co.id/fees-rates" in w["rendered_urls"]
    assert w["robots_disallowed"] == 2 and w["robots_unreachable"] == 3
    assert w["fee_page_citations_gpt"] == {"seabank.co.id": 5, "blubybcadigital.id": 4}
    assert round(w["share_gpt"], 2) == 0.64 and round(w["share_gem"], 2) == 0.29

from deck.theme import C, contrast


def test_text_pairs_pass_aa():
    for fg in ["text", "secondary"]:
        assert contrast(C[fg], C["bg"]) >= 4.5, fg
    for mark in ["gpt", "gem"]:
        assert contrast(C[mark], C["bg"]) >= 3.0, mark


def test_engine_colours_are_the_validated_pair():
    assert (C["gpt"], C["gem"]) == ("#D07A28", "#4790D8")
    assert contrast(C["secondary"], C["bar"]) >= 4.5
    assert contrast(C["dim"], C["bg"]) >= 1.5


def test_contrast_reference_values():
    assert round(contrast("#FFFFFF", "#000000"), 1) == 21.0
    assert round(contrast("#777777", "#FFFFFF"), 2) == 4.48

from deck.theme import C, SANS, contrast


def test_text_pairs_pass_aa():
    for fg in ["text", "secondary"]:
        for ground in ["bg", "panel"]:
            assert contrast(C[fg], C[ground]) >= 4.5, (fg, ground)


def test_engine_colours_are_the_navy_pair():
    assert (C["gpt"], C["gem"]) == ("#F2A541", "#7FC0F5")
    for mark in ["gpt", "gem"]:
        assert contrast(C[mark], C["bg"]) >= 3.0, mark


def test_navy_ground_and_lines():
    assert (C["bg"], C["panel"], C["line"], C["glow"]) == ("#0F2747", "#0A1C36", "#3B5A85", "#7FC0F5")
    assert SANS == "Plus Jakarta Sans"


def test_no_black_in_palette():
    assert "#000000" not in {v.upper() for v in C.values()}


def test_contrast_reference_values():
    assert round(contrast("#FFFFFF", "#000000"), 1) == 21.0
    assert round(contrast("#777777", "#FFFFFF"), 2) == 4.48

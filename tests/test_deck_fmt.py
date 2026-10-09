from deck.fmt import num, pct


def test_half_up_rounding():
    assert pct(0.625) == "63%" and pct(0.605) == "61%" and pct(0.355) == "36%" and pct(0.875) == "88%"
    assert pct(0.525, 1) == "52.5%" and num(93.226961, 1) == "93.2" and num(1234) == "1,234"

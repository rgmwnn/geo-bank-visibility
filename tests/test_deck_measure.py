from deck.measure import lines


def test_wraps_by_words_with_real_font_widths():
    assert lines("short", 1000, 14) == 1
    long = "\u201cSaya freelancer dengan penghasilan tidak tetap, butuh rekening tanpa saldo minimum dan bisa pisah kantong. Bank apa yang cocok?\u201d"
    assert lines(long, 1500, 22) == 3
    assert lines("word " * 40, 400, 14, mono=True) > lines("word " * 40, 400, 14)

from deck.measure import lines


def test_wraps_by_words_with_real_font_widths():
    assert lines("short", 1000, 14) == 1
    long = "\u201cSaya freelancer dengan penghasilan tidak tetap, butuh rekening tanpa saldo minimum dan bisa pisah kantong. Bank apa yang cocok?\u201d"
    assert lines(long, 1500, 22) == 2  # 2775 px wide in Plus Jakarta Sans at 22 pt
    assert lines(long, 1200, 22) == 3
    assert lines("word " * 40, 400, 14, mono=True) > lines("word " * 40, 400, 14)


def test_bold_text_is_measured_with_the_bold_face():
    t = "Bank Jago and SeaBank lead the digital answers " * 3
    assert lines(t, 900, 40, bold=True) >= lines(t, 900, 40)
    from deck.measure import _font
    assert _font(80, False, True).getlength(t) > _font(80, False, False).getlength(t)


def test_a_word_wider_than_the_box_counts_as_wrapping():
    # Eye check 2026-10-11: "24%" at 110 pt in a 460 px box broke before the % sign in LibreOffice.
    assert lines("24%", 460, 110, bold=True) == 2
    assert lines("24%", 560, 110, bold=True) == 1

"""Text measurement with the real font files, so layout matches what renderers draw."""
from functools import lru_cache

from PIL import ImageFont

from deck.theme import FONT_DIR

LINE = 1.4  # line height as a multiple of font size; LibreOffice draws Work Sans at 1.15 spacing with a 1.379 em pitch
SAFETY = 0.96  # renderers (LibreOffice, Canva) wrap slightly earlier than raw glyph widths


@lru_cache(maxsize=None)
def _font(px: int, mono: bool):
    name = "IBMPlexMono-Regular.ttf" if mono else "WorkSans-Regular.ttf"
    return ImageFont.truetype(str(FONT_DIR / name), px)


def lines(text: str, width_px: float, pt: float, mono: bool = False) -> int:
    font = _font(round(pt * 2), mono)
    n, cur = 0, ""
    for para in text.split("\n"):
        n += 1
        cur = ""
        for word in para.split(" "):
            trial = f"{cur} {word}".strip()
            if cur and font.getlength(trial) > width_px * SAFETY:
                n += 1
                cur = word
            else:
                cur = trial
    return n


def height(text: str, width_px: float, pt: float, mono: bool = False) -> float:
    return lines(text, width_px, pt, mono) * pt * 2 * LINE

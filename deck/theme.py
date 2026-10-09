from pathlib import Path

C = {
    "bg": "#0B0C0E",
    "bar": "#000000",
    "text": "#ECE7DD",
    "secondary": "#9A9EA6",
    "dim": "#3A3D43",
    "gpt": "#E39B45",
    "gem": "#6FA3D2",
}
SANS = "Work Sans"
MONO = "IBM Plex Mono"
FONT_DIR = Path(__file__).parent / "fonts"


def _luminance(hex_color: str) -> float:
    rgb = [int(hex_color.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(fg_hex: str, bg_hex: str) -> float:
    hi, lo = sorted([_luminance(fg_hex), _luminance(bg_hex)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def register_fonts() -> None:
    from matplotlib import font_manager
    for ttf in FONT_DIR.glob("*.ttf"):
        font_manager.fontManager.addfont(str(ttf))

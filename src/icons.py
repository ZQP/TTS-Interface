"""
Modern, pixel-perfect icon provider for Gemini TTS Studio.
Generates and caches crisp, anti-aliased vector-style CTkImage icons
without relying on font emojis or external icon fonts.
Guarantees mathematical vertical alignment and crisp DPI rendering.
"""

import math
from typing import Dict, Tuple
from PIL import Image, ImageDraw
import customtkinter as ctk

# Color constants matching ZQP brand theme
COLOR_TEAL_DARK = (23, 83, 74, 255)       # M3_PRIMARY Light (#17534A)
COLOR_TEAL_LIGHT = (82, 219, 202, 255)    # M3_PRIMARY Dark (#52DBCA)
COLOR_WHITE = (255, 255, 255, 255)
COLOR_MUTED_DARK = (63, 73, 70, 255)      # Slate Teal (#3F4946)
COLOR_MUTED_LIGHT = (162, 178, 174, 255)  # (#A2B2AE)
COLOR_RED = (186, 26, 26, 255)

_ICON_CACHE: Dict[str, ctk.CTkImage] = {}


def _create_canvas(size: int = 64) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    return img, draw


def _draw_gear(color: Tuple[int, int, int, int], size: int = 64) -> Image.Image:
    img, draw = _create_canvas(size)
    cx, cy = size / 2, size / 2
    teeth = 8
    for i in range(teeth):
        angle = i * math.pi / 4
        x0 = cx + 22 * math.cos(angle - 0.20)
        y0 = cy + 22 * math.sin(angle - 0.20)
        x1 = cx + 28 * math.cos(angle - 0.14)
        y1 = cy + 28 * math.sin(angle - 0.14)
        x2 = cx + 28 * math.cos(angle + 0.14)
        y2 = cy + 28 * math.sin(angle + 0.14)
        x3 = cx + 22 * math.cos(angle + 0.20)
        y3 = cy + 22 * math.sin(angle + 0.20)
        draw.polygon([(x0, y0), (x1, y1), (x2, y2), (x3, y3)], fill=color)
    draw.ellipse((cx - 20, cy - 20, cx + 20, cy + 20), fill=color)
    draw.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=(0, 0, 0, 0))
    return img


def _draw_folder(color: Tuple[int, int, int, int], size: int = 64) -> Image.Image:
    img, draw = _create_canvas(size)
    # Folder tab
    draw.rounded_rectangle((10, 16, 26, 26), radius=3, fill=color)
    # Folder back
    draw.rounded_rectangle((10, 22, 54, 50), radius=5, fill=color)
    # Folder cutout / outline for crisp look
    draw.rounded_rectangle((15, 27, 49, 45), radius=3, fill=(0, 0, 0, 0))
    draw.rounded_rectangle((13, 26, 51, 47), radius=3, outline=color, width=4)
    return img


def _draw_globe(color: Tuple[int, int, int, int], size: int = 64) -> Image.Image:
    img, draw = _create_canvas(size)
    cx, cy = size / 2, size / 2
    # Outer circle
    draw.ellipse((cx - 20, cy - 20, cx + 20, cy + 20), outline=color, width=4)
    # Equator line
    draw.line((cx - 20, cy, cx + 20, cy), fill=color, width=4)
    # Longitude ellipse
    draw.ellipse((cx - 10, cy - 20, cx + 10, cy + 20), outline=color, width=4)
    return img


def _draw_play(color: Tuple[int, int, int, int], size: int = 64) -> Image.Image:
    img, draw = _create_canvas(size)
    cx, cy = size / 2, size / 2
    pts = [(cx - 11, cy - 16), (cx + 17, cy), (cx - 11, cy + 16)]
    draw.polygon(pts, fill=color)
    return img


def _draw_pause(color: Tuple[int, int, int, int], size: int = 64) -> Image.Image:
    img, draw = _create_canvas(size)
    cx, cy = size / 2, size / 2
    draw.rounded_rectangle((cx - 12, cy - 16, cx - 4, cy + 16), radius=2, fill=color)
    draw.rounded_rectangle((cx + 4, cy - 16, cx + 12, cy + 16), radius=2, fill=color)
    return img


def _draw_stop(color: Tuple[int, int, int, int], size: int = 64) -> Image.Image:
    img, draw = _create_canvas(size)
    cx, cy = size / 2, size / 2
    draw.rounded_rectangle((cx - 14, cy - 14, cx + 14, cy + 14), radius=3, fill=color)
    return img


def _draw_download(color: Tuple[int, int, int, int], size: int = 64) -> Image.Image:
    img, draw = _create_canvas(size)
    cx, cy = size / 2, size / 2
    # Arrow stem
    draw.line((cx, cy - 18, cx, cy + 6), fill=color, width=4)
    # Arrow head
    draw.polygon([(cx - 11, cy), (cx + 11, cy), (cx, cy + 12)], fill=color)
    # Tray
    draw.line((cx - 18, cy + 12, cx - 18, cy + 20), fill=color, width=4)
    draw.line((cx - 18, cy + 20, cx + 18, cy + 20), fill=color, width=4)
    draw.line((cx + 18, cy + 12, cx + 18, cy + 20), fill=color, width=4)
    return img


def _draw_plus(color: Tuple[int, int, int, int], size: int = 64) -> Image.Image:
    img, draw = _create_canvas(size)
    cx, cy = size / 2, size / 2
    draw.line((cx, cy - 18, cx, cy + 18), fill=color, width=5)
    draw.line((cx - 18, cy, cx + 18, cy), fill=color, width=5)
    return img


def _draw_trash(color: Tuple[int, int, int, int], size: int = 64) -> Image.Image:
    img, draw = _create_canvas(size)
    cx, cy = size / 2, size / 2
    # Lid handle and bar
    draw.line((cx - 18, cy - 14, cx + 18, cy - 14), fill=color, width=4)
    draw.rounded_rectangle((cx - 6, cy - 20, cx + 6, cy - 14), radius=2, outline=color, width=3)
    # Bin body
    draw.polygon([(cx - 14, cy - 10), (cx + 14, cy - 10), (cx + 10, cy + 18), (cx - 10, cy + 18)], outline=color, width=4)
    draw.line((cx - 4, cy - 6, cx - 3, cy + 14), fill=color, width=3)
    draw.line((cx + 4, cy - 6, cx + 3, cy + 14), fill=color, width=3)
    return img


def _draw_sparkles(color: Tuple[int, int, int, int], size: int = 64) -> Image.Image:
    img, draw = _create_canvas(size)
    cx, cy = size / 2, size / 2
    # Central 4-pointed star
    pts = [
        (cx, cy - 18), (cx + 5, cy - 5), (cx + 18, cy), (cx + 5, cy + 5),
        (cx, cy + 18), (cx - 5, cy + 5), (cx - 18, cy), (cx - 5, cy - 5)
    ]
    draw.polygon(pts, fill=color)
    # Small satellite star
    sx, sy = cx + 14, cy - 14
    pts_s = [
        (sx, sy - 7), (sx + 2, sy - 2), (sx + 7, sy), (sx + 2, sy + 2),
        (sx, sy + 7), (sx - 2, sy + 2), (sx - 7, sy), (sx - 2, sy - 2)
    ]
    draw.polygon(pts_s, fill=color)
    return img


def _draw_moon(color: Tuple[int, int, int, int], size: int = 64) -> Image.Image:
    img, draw = _create_canvas(size)
    cx, cy = size / 2, size / 2
    draw.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=color)
    # Cutout circle offset to top-right
    draw.ellipse((cx - 10, cy - 24, cx + 26, cy + 12), fill=(0, 0, 0, 0))
    return img


def _draw_sun(color: Tuple[int, int, int, int], size: int = 64) -> Image.Image:
    img, draw = _create_canvas(size)
    cx, cy = size / 2, size / 2
    # Center circle
    draw.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=color)
    # 8 rays
    for i in range(8):
        angle = i * math.pi / 4
        x0 = cx + 16 * math.cos(angle)
        y0 = cy + 16 * math.sin(angle)
        x1 = cx + 22 * math.cos(angle)
        y1 = cy + 22 * math.sin(angle)
        draw.line((x0, y0, x1, y1), fill=color, width=3)
    return img


def _draw_book(color: Tuple[int, int, int, int], size: int = 64) -> Image.Image:
    img, draw = _create_canvas(size)
    cx, cy = size / 2, size / 2
    # Open book spine and two pages
    draw.line((cx, cy - 14, cx, cy + 16), fill=color, width=3)
    draw.polygon([(cx - 18, cy - 12), (cx, cy - 14), (cx, cy + 16), (cx - 18, cy + 14)], outline=color, width=3)
    draw.polygon([(cx, cy - 14), (cx + 18, cy - 12), (cx + 18, cy + 14), (cx, cy + 16)], outline=color, width=3)
    return img


def _draw_music(color: Tuple[int, int, int, int], size: int = 64) -> Image.Image:
    img, draw = _create_canvas(size)
    cx, cy = size / 2, size / 2
    # Dual eighth notes
    draw.ellipse((cx - 16, cy + 6, cx - 6, cy + 16), fill=color)
    draw.ellipse((cx + 6, cy + 2, cx + 16, cy + 12), fill=color)
    draw.line((cx - 7, cy + 10, cx - 7, cy - 14), fill=color, width=3)
    draw.line((cx + 15, cy + 6, cx + 15, cy - 18), fill=color, width=3)
    draw.polygon([(cx - 7, cy - 14), (cx + 15, cy - 18), (cx + 15, cy - 12), (cx - 7, cy - 8)], fill=color)
    return img


def _draw_subtitles(color: Tuple[int, int, int, int], size: int = 64) -> Image.Image:
    img, draw = _create_canvas(size)
    cx, cy = size / 2, size / 2
    draw.rounded_rectangle((cx - 20, cy - 15, cx + 20, cy + 15), radius=4, outline=color, width=3)
    draw.line((cx - 12, cy + 4, cx + 12, cy + 4), fill=color, width=3)
    draw.line((cx - 8, cy + 9, cx + 8, cy + 9), fill=color, width=3)
    return img


def _draw_compare(color: Tuple[int, int, int, int], size: int = 64) -> Image.Image:
    img, draw = _create_canvas(size)
    cx, cy = size / 2, size / 2
    # Two cards side by side
    draw.rounded_rectangle((cx - 19, cy - 14, cx - 3, cy + 14), radius=3, outline=color, width=3)
    draw.rounded_rectangle((cx + 3, cy - 14, cx + 19, cy + 14), radius=3, outline=color, width=3)
    return img


def get_ui_icon(name: str, variant: str = "theme", size: int = 16) -> ctk.CTkImage:
    """
    Returns a cached CTkImage for the requested icon name.
    Variants:
    - 'theme': Dark teal in light mode, mint teal in dark mode.
    - 'white': Solid white in both modes (e.g. for primary CTA buttons).
    - 'muted': Muted slate in light mode, off-white in dark mode.
    - 'danger': Red in both modes.
    """
    cache_key = f"{name}_{variant}_{size}"
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    draw_map = {
        "gear": _draw_gear,
        "settings": _draw_gear,
        "folder": _draw_folder,
        "globe": _draw_globe,
        "translate": _draw_globe,
        "play": _draw_play,
        "pause": _draw_pause,
        "stop": _draw_stop,
        "download": _draw_download,
        "export": _draw_download,
        "plus": _draw_plus,
        "add": _draw_plus,
        "trash": _draw_trash,
        "delete": _draw_trash,
        "sparkles": _draw_sparkles,
        "generate": _draw_sparkles,
        "moon": _draw_moon,
        "sun": _draw_sun,
        "book": _draw_book,
        "lexicon": _draw_book,
        "music": _draw_music,
        "subtitles": _draw_subtitles,
        "srt": _draw_subtitles,
        "compare": _draw_compare,
    }

    fn = draw_map.get(name, _draw_gear)

    if variant == "white":
        light_img = fn(COLOR_WHITE)
        dark_img = fn(COLOR_WHITE)
    elif variant == "muted":
        light_img = fn(COLOR_MUTED_DARK)
        dark_img = fn(COLOR_MUTED_LIGHT)
    elif variant == "danger":
        light_img = fn(COLOR_RED)
        dark_img = fn(COLOR_RED)
    else:  # 'theme'
        light_img = fn(COLOR_TEAL_DARK)
        dark_img = fn(COLOR_TEAL_LIGHT)

    ctk_img = ctk.CTkImage(light_image=light_img, dark_image=dark_img, size=(size, size))
    _ICON_CACHE[cache_key] = ctk_img
    return ctk_img

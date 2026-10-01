# Kulsh GPT | v2.39.0
# by (main author): starfall-apk
# coauthor & bot hosting: pomidorka1515

"""Pillow infographic engine: bar, line, pie, table, text, images."""

import json
import math
import os
import re
from io import BytesIO
from typing import Any, cast

from PIL import Image, ImageDraw, ImageFont

from src.util import (
    ChartTheme,
    Color,
    Font,
    JsonDict,
    SeriesSpec,
    json_dict,
    theme_str,
    download_image_bytes,
    logger,
)

# ============================================================
# CHART / INFOGRAPHIC ENGINE (Pillow)
# ============================================================
_PALETTE = [
    "#4F46E5", "#06B6D4", "#10B981", "#F59E0B", "#EF4444",
    "#8B5CF6", "#EC4899", "#14B8A6", "#F97316", "#6366F1",
]

CHART_THEMES = {
    "dark_modern": {
        "bg": "#0E0E12", "bg_grad": ("#171728", "#0E0E12"),
        "text": "#F3F4F6", "text_dim": "#9CA3AF", "grid": "#2A2A3A",
        "accent": "#10B981", "card": "#16161E", "border": "#2A2A3A",
    },
    "light_minimal": {
        "bg": "#FAFAFB", "bg_grad": ("#FFFFFF", "#F1F1F4"),
        "text": "#111827", "text_dim": "#4B5563", "grid": "#E5E7EB",
        "accent": "#2563EB", "card": "#FFFFFF", "border": "#E5E7EB",
    },
    "ocean": {
        "bg": "#0A1929", "bg_grad": ("#103A5C", "#0A1929"),
        "text": "#E5F2FF", "text_dim": "#7FB1D6", "grid": "#17334B",
        "accent": "#3FB0FF", "card": "#0F2538", "border": "#17334B",
    },
    "retro": {
        "bg": "#FBF6E9", "bg_grad": ("#FFF8E7", "#F0E2B6"),
        "text": "#2D2B22", "text_dim": "#6B6350", "grid": "#D8CBA5",
        "accent": "#D97706", "card": "#FFFAEB", "border": "#D8CBA5",
    },
}


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = (h or "#000000").lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return (0, 0, 0)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def as_rgb(c: Color) -> tuple[int, int, int]:
    if isinstance(c, str):
        return hex_to_rgb(c)
    return (int(c[0]), int(c[1]), int(c[2]))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*[max(0, min(255, int(c))) for c in rgb])


def lerp_color(c1: Color, c2: Color, t: float) -> tuple[int, int, int]:
    r1, g1, b1 = as_rgb(c1)
    r2, g2, b2 = as_rgb(c2)
    return (
        int(r1 + (r2 - r1) * t),
        int(g1 + (g2 - g1) * t),
        int(b1 + (b2 - b1) * t),
    )


def darken(c: Color, factor: float = 0.7) -> tuple[int, int, int]:
    rgb = as_rgb(c)
    return (int(rgb[0] * factor), int(rgb[1] * factor), int(rgb[2] * factor))


def lighten(c: Color, factor: float = 1.3) -> tuple[int, int, int]:
    rgb = as_rgb(c)
    return (
        min(255, int(rgb[0] * factor)),
        min(255, int(rgb[1] * factor)),
        min(255, int(rgb[2] * factor)),
    )


def make_gradient_bg(w: int, h: int, c1: str, c2: str) -> Image.Image:
    base = Image.new("RGB", (1, h), hex_to_rgb(c1))
    for y in range(h):
        t = y / max(1, h - 1)
        base.putpixel((0, y), lerp_color(c1, c2, t))
    return base.resize((w, h), Image.Resampling.BILINEAR)


def load_font(size: int, bold: bool = False) -> Font:
    candidates_bold = [
        os.path.join("fonts", "Montserrat-Bold.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "arialbd.ttf",
        "DejaVuSans-Bold.ttf",
    ]
    candidates_reg = [
        os.path.join("fonts", "Montserrat-Regular.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/Library/Fonts/Arial.ttf",
        "arial.ttf",
        "DejaVuSans.ttf",
    ]
    candidates = candidates_bold if bold else candidates_reg
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font: Font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text or " ", font=font)
    return int(bbox[2] - bbox[0]), int(bbox[3] - bbox[1])


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    xy_box: tuple[int, int, int, int],
    text: str,
    font: Font,
    fill: str | tuple[int, ...],
) -> None:
    x0, y0, x1, y1 = xy_box
    w, h = text_size(draw, text, font)
    x = x0 + (x1 - x0 - w) // 2
    y = y0 + (y1 - y0 - h) // 2
    draw.text((x, y), text, font=font, fill=fill)


def wrap_lines(draw: ImageDraw.ImageDraw, text: str, font: Font, max_width: int) -> list[str]:
    words = (text or "").split()
    lines: list[str] = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        tw, _ = text_size(draw, test, font)
        if tw <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def render_bar_chart(canvas: Image.Image, box: tuple[int, int, int, int],
                      spec: JsonDict, theme: ChartTheme) -> None:
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(canvas)
    title = spec.get("title") or ""
    labels = [str(v) for v in spec.get("labels", [])]
    values = [float(v) for v in spec.get("values", []) if is_number(v)]
    if not values:
        return
    colors = spec.get("colors") or _PALETTE
    # card
    draw.rounded_rectangle(box, radius=16, fill=theme["card"], outline=theme["border"], width=2)
    inner_pad = 24
    cx0, cy0, cx1, cy1 = x0 + inner_pad, y0 + inner_pad, x1 - inner_pad, y1 - inner_pad
    font_title = load_font(22, bold=True)
    font_lab = load_font(13)
    font_val = load_font(13, bold=True)

    if title:
        draw.text((cx0, cy0), title, font=font_title, fill=theme["text"])
        cy0 += 34

    # Chart area
    chart_top = cy0 + 4
    chart_bottom = cy1 - 36
    chart_left = cx0 + 8
    chart_right = cx1 - 8
    if chart_bottom <= chart_top:
        return

    vmax = max(values) if values else 1.0
    vmax = vmax if vmax > 0 else 1.0
    # nice ceiling
    magnitude = 10 ** int(math.floor(math.log10(vmax))) if vmax > 0 else 1
    nice_vmax = float(math.ceil(vmax / magnitude) * magnitude)
    if nice_vmax <= 0:
        nice_vmax = 1.0

    n = len(values)
    gap = 12
    total_w = chart_right - chart_left
    bar_w = max(6, int((total_w - gap * (n + 1)) / max(1, n)))

    # grid + axis labels
    steps = 5
    font_grid = load_font(11)
    for i in range(steps + 1):
        yy = chart_bottom - int((chart_bottom - chart_top) * i / steps)
        val = nice_vmax * i / steps
        draw.line([(chart_left, yy), (chart_right, yy)], fill=theme["grid"], width=1)
        vs = f"{val:.2f}".rstrip("0").rstrip(".")
        draw.text((cx0 - 4 - text_size(draw, vs, font_grid)[0], yy - 6), vs, font=font_grid, fill=theme["text_dim"])

    for idx, val in enumerate(values):
        bx = chart_left + gap + idx * (bar_w + gap)
        bh = int((chart_bottom - chart_top) * (val / nice_vmax))
        by = chart_bottom - bh
        color = colors[idx % len(colors)]
        try:
            rgb = hex_to_rgb(color)
        except Exception:
            rgb = (79, 70, 229)
        # gradient bar
        bar_img = Image.new("RGB", (bar_w, max(1, bh)))
        for yy in range(max(1, bh)):
            t = yy / max(1, bh - 1)
            bar_img.putpixel((0, yy), lerp_color(lighten(rgb, 1.25), rgb, t))
        bar_img = bar_img.resize((bar_w, max(1, bh)), Image.Resampling.BILINEAR)
        if bh > 0:
            canvas.paste(bar_img, (bx, by))
        # value on top
        vs = f"{val:g}"
        vw, _ = text_size(draw, vs, font_val)
        draw.text((bx + (bar_w - vw) // 2, by - 20), vs, font=font_val, fill=theme["text"])
        # label
        lab = labels[idx] if idx < len(labels) else ""
        lab = lab[:14]
        lw, _ = text_size(draw, lab, font_lab)
        draw.text((bx + (bar_w - lw) // 2, chart_bottom + 8), lab, font=font_lab, fill=theme["text_dim"])


def render_line_chart(canvas: Image.Image, box: tuple[int, int, int, int],
                       spec: JsonDict, theme: ChartTheme) -> None:
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(canvas)
    title = spec.get("title") or ""
    xs = [str(v) for v in spec.get("x", [])]
    series = spec.get("series", []) or []
    if not series:
        return
    # normalize series
    norm_series: list[SeriesSpec] = []
    for s in series:
        if not isinstance(s, dict):
            continue
        series_item = cast(JsonDict, s)
        ys = [float(v) for v in s.get("y", []) if is_number(v)]
        if not ys:
            continue
        raw_color = series_item.get("color")
        color = raw_color if isinstance(raw_color, str) else _PALETTE[len(norm_series) % len(_PALETTE)]
        raw_name = series_item.get("name")
        norm_series.append({
            "name": raw_name if isinstance(raw_name, str) and raw_name else f"Series {len(norm_series) + 1}",
            "y": ys,
            "color": color,
        })
    if not norm_series:
        return

    draw.rounded_rectangle(box, radius=16, fill=theme["card"], outline=theme["border"], width=2)
    inner_pad = 24
    cx0, cy0, cx1, cy1 = x0 + inner_pad, y0 + inner_pad, x1 - inner_pad, y1 - inner_pad
    font_title = load_font(22, bold=True)
    font_lab = load_font(12)
    font_grid = load_font(11)
    font_legend = load_font(12)

    if title:
        draw.text((cx0, cy0), title, font=font_title, fill=theme["text"])
        cy0 += 34

    # legend at top-right
    legend_x = cx1
    legend_y = cy0 - 4
    for s in reversed(norm_series):
        name = str(s["name"])[:18]
        color = str(s["color"])
        tw, th = text_size(draw, name, font_legend)
        legend_x -= tw + 24
        draw.line([(legend_x, legend_y + 8), (legend_x + 14, legend_y + 8)],
                  fill=hex_to_rgb(color), width=3)
        draw.text((legend_x + 18, legend_y), name, font=font_legend, fill=theme["text_dim"])

    chart_top = cy0 + 8
    chart_bottom = cy1 - 30
    chart_left = cx0 + 6
    chart_right = cx1 - 6
    if chart_bottom <= chart_top:
        return

    all_ys = [v for s in norm_series for v in cast(list[float], s["y"])]
    vmin = min(all_ys)
    vmax = max(all_ys)
    if vmax == vmin:
        vmax = vmin + 1
    pad = (vmax - vmin) * 0.1
    vmin -= pad
    vmax += pad

    steps = 5
    for i in range(steps + 1):
        yy = chart_bottom - int((chart_bottom - chart_top) * i / steps)
        val = vmin + (vmax - vmin) * i / steps
        draw.line([(chart_left, yy), (chart_right, yy)], fill=theme["grid"], width=1)
        vs = f"{val:.2f}".rstrip("0").rstrip(".")
        draw.text((cx0 - 4 - text_size(draw, vs, font_grid)[0], yy - 6),
                  vs, font=font_grid, fill=theme["text_dim"])

    # X positions
    max_len = max(len(cast(list[float], s["y"])) for s in norm_series)
    if max_len < 2:
        max_len = 2
    x_step = (chart_right - chart_left) / (max_len - 1)

    def _y_to_px(v: float) -> int:
        return chart_bottom - int((v - vmin) / (vmax - vmin) * (chart_bottom - chart_top))

    for s in norm_series:
        color = str(s["color"])
        pts = [(chart_left + i * x_step, _y_to_px(v)) for i, v in enumerate(cast(list[float], s["y"]))]
        if len(pts) >= 2:
            draw.line(pts, fill=hex_to_rgb(color), width=3)
        for p in pts:
            r = 4
            draw.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r],
                         fill=hex_to_rgb(color), outline=theme["bg"], width=2)

    # X labels
    for i in range(max_len):
        lab = xs[i] if i < len(xs) else str(i + 1)
        lab = lab[:10]
        lx = chart_left + i * x_step
        lw, _ = text_size(draw, lab, font_lab)
        draw.text((lx - lw // 2, chart_bottom + 6), lab, font=font_lab, fill=theme["text_dim"])


def render_pie_chart(canvas: Image.Image, box: tuple[int, int, int, int],
                      spec: JsonDict, theme: ChartTheme, depth: int = 0) -> None:
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(canvas)
    title = spec.get("title") or ""
    labels = [str(v) for v in spec.get("labels", [])]
    values = [float(v) for v in spec.get("values", []) if is_number(v)]
    if not values:
        return
    colors = spec.get("colors") or _PALETTE
    total = sum(values)
    if total <= 0:
        return

    draw.rounded_rectangle(box, radius=16, fill=theme["card"], outline=theme["border"], width=2)
    inner_pad = 24
    cx0, cy0, cx1, cy1 = x0 + inner_pad, y0 + inner_pad, x1 - inner_pad, y1 - inner_pad

    font_title = load_font(22, bold=True)
    font_legend = load_font(13)
    font_pct = load_font(13, bold=True)

    if title:
        draw.text((cx0, cy0), title, font=font_title, fill=theme["text"])
        cy0 += 34

    # Pie on left half, legend on right half
    chart_w = (cx1 - cx0)
    pie_box = (
        cx0 + 10,
        cy0 + 10,
        cx0 + min(chart_w // 2 + 40, (cy1 - cy0) + 10),
        cy1 - 10,
    )
    # make it square
    pw = pie_box[2] - pie_box[0]
    ph = pie_box[3] - pie_box[1]
    side = min(pw, ph)
    pcx = pie_box[0] + pw // 2
    pcy = pie_box[1] + ph // 2
    px0 = pcx - side // 2
    py0 = pcy - side // 2
    px1 = px0 + side
    py1 = py0 + side

    start = -90.0
    legend_x = px1 + 30
    legend_y = cy0 + 20

    for idx, val in enumerate(values):
        extent = 360 * (val / total)
        color = colors[idx % len(colors)]
        try:
            rgb = hex_to_rgb(str(color))
        except Exception:
            rgb = hex_to_rgb(_PALETTE[idx % len(_PALETTE)])

        if depth > 0:
            # Draw "side wall"
            for d in range(depth, 0, -1):
                draw.pieslice([px0, py0 + d, px1, py1 + d],
                              start, start + extent,
                              fill=darken(rgb, 0.55), outline=darken(rgb, 0.5))
        draw.pieslice([px0, py0, px1, py1], start, start + extent,
                      fill=rgb, outline=theme["bg"], width=2)
        start += extent

    # Legend
    for idx, val in enumerate(values):
        color = colors[idx % len(colors)]
        try:
            rgb = hex_to_rgb(str(color))
        except Exception:
            rgb = hex_to_rgb(_PALETTE[idx % len(_PALETTE)])
        pct = val / total * 100
        lab = labels[idx] if idx < len(labels) else f"Item {idx + 1}"
        lab_line = f"{lab}"
        pct_line = f"{pct:.1f}%"
        # swatch
        draw.rectangle([legend_x, legend_y + 4, legend_x + 16, legend_y + 20], fill=rgb)
        draw.text((legend_x + 24, legend_y), lab_line[:28], font=font_legend, fill=theme["text"])
        pw_, _ = text_size(draw, pct_line, font_pct)
        draw.text((cx1 - pw_ - 4, legend_y), pct_line, font=font_pct, fill=theme["text_dim"])
        legend_y += 28
        if legend_y > cy1 - 20:
            break


def render_table(canvas: Image.Image, box: tuple[int, int, int, int],
                  spec: JsonDict, theme: ChartTheme) -> None:
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(canvas)
    title = spec.get("title") or ""
    headers = [str(h) for h in spec.get("headers", [])]
    rows = [[str(c) for c in row] for row in spec.get("rows", [])]
    if not headers and not rows:
        return

    draw.rounded_rectangle(box, radius=16, fill=theme["card"], outline=theme["border"], width=2)
    inner_pad = 20
    cx0, cy0, cx1, cy1 = x0 + inner_pad, y0 + inner_pad, x1 - inner_pad, y1 - inner_pad

    font_title = load_font(22, bold=True)
    font_head = load_font(14, bold=True)
    font_row = load_font(14)

    if title:
        draw.text((cx0, cy0), title, font=font_title, fill=theme["text"])
        cy0 += 34

    n_cols = max([len(headers)] + [len(r) for r in rows] + [1])
    col_w = (cx1 - cx0) // n_cols
    row_h = 30

    y_cur = cy0 + 4
    # header
    if headers:
        for i in range(n_cols):
            label = headers[i] if i < len(headers) else ""
            cell_x0 = cx0 + i * col_w
            cell_x1 = cell_x0 + col_w
            draw.rectangle([cell_x0, y_cur, cell_x1, y_cur + row_h],
                           fill=theme["accent"])
            draw_centered_text(draw, (cell_x0 + 6, y_cur, cell_x1 - 6, y_cur + row_h),
                                label, font_head, "#FFFFFF")
        y_cur += row_h

    # rows
    for r_i, r in enumerate(rows):
        if y_cur + row_h > cy1:
            break
        row_bg = theme["bg"] if r_i % 2 == 0 else theme["card"]
        draw.rectangle([cx0, y_cur, cx1, y_cur + row_h], fill=row_bg)
        for i in range(n_cols):
            cell = r[i] if i < len(r) else ""
            cell_x0 = cx0 + i * col_w
            cell_x1 = cell_x0 + col_w
            draw_centered_text(draw, (cell_x0 + 6, y_cur, cell_x1 - 6, y_cur + row_h),
                                cell[:40], font_row, theme["text"])
        draw.line([(cx0, y_cur + row_h), (cx1, y_cur + row_h)], fill=theme["grid"], width=1)
        y_cur += row_h


async def load_remote_image(url: str) -> Image.Image | None:
    try:
        data = await download_image_bytes(url)
        return Image.open(BytesIO(data)).convert("RGBA")
    except Exception as e:
        logger.warning(f"load_remote_image err: {e}")
        return None


def render_image_block(canvas: Image.Image, box: tuple[int, int, int, int],
                        img: Image.Image, theme: ChartTheme) -> None:
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(box, radius=16, fill=theme["card"], outline=theme["border"], width=2)
    inner_pad = 12
    ix0, iy0, ix1, iy1 = x0 + inner_pad, y0 + inner_pad, x1 - inner_pad, y1 - inner_pad
    box_w = ix1 - ix0
    box_h = iy1 - iy0
    if box_w <= 0 or box_h <= 0:
        return
    im = img.copy()
    im.thumbnail((box_w, box_h), Image.Resampling.LANCZOS)
    ox = ix0 + (box_w - im.width) // 2
    oy = iy0 + (box_h - im.height) // 2
    if im.mode == "RGBA":
        canvas.paste(im, (ox, oy), im)
    else:
        canvas.paste(im, (ox, oy))


def is_number(x: object) -> bool:
    try:
        float(cast(Any, x))
        return True
    except (TypeError, ValueError):
        return False


async def render_infographic(spec: JsonDict, user_images: list[bytes] | None = None) -> BytesIO:
    """
    Строит инфографику по спецификации.
    spec = {
        "theme": "dark_modern",
        "title": "...",
        "subtitle": "...",
        "width": 1400,
        "blocks": [ {...}, ... ]
    }
    Возвращает BytesIO с PNG.
    """
    theme_name = spec.get("theme", "dark_modern")
    theme = CHART_THEMES.get(theme_name, CHART_THEMES["dark_modern"])

    width = int(spec.get("width", 1400))
    title = spec.get("title") or ""
    subtitle = spec.get("subtitle") or ""
    blocks = spec.get("blocks", []) or []

    # Preload images (URL or user references)
    preloaded: dict[int, Image.Image] = {}
    for idx, block in enumerate(blocks):
        if not isinstance(block, dict):
            continue
        if block.get("type") == "image":
            src = block.get("source", "url")
            if src == "user" and user_images:
                i = int(block.get("index", 0))
                if 0 <= i < len(user_images):
                    try:
                        preloaded[idx] = Image.open(BytesIO(user_images[i])).convert("RGBA")
                    except Exception:
                        pass
            elif src == "url" and block.get("url"):
                img = await load_remote_image(block["url"])
                if img is not None:
                    preloaded[idx] = img

    # Precompute heights
    # Approximate: heading 60, text computed by width, divider 32, chart uses "height" or default 340,
    # table uses headers/rows, image uses "height" or 400.
    padding = 40
    inner_w = width - padding * 2

    # measure text heights
    tmp_img = Image.new("RGB", (10, 10))
    tmp_draw = ImageDraw.Draw(tmp_img)
    font_title = load_font(44, bold=True)
    font_sub = load_font(20)
    font_h = load_font(28, bold=True)
    font_text = load_font(18)

    heights: list[int] = []
    for idx, block in enumerate(blocks):
        if not isinstance(block, dict):
            heights.append(0)
            continue
        t = block.get("type", "text")
        if t == "heading":
            heights.append(52)
        elif t == "text":
            lines = wrap_lines(tmp_draw, block.get("text", ""), font_text, inner_w)
            heights.append(max(30, len(lines) * 26 + 8))
        elif t == "divider":
            heights.append(36)
        elif t == "bar":
            heights.append(int(block.get("height", 340)))
        elif t == "line":
            heights.append(int(block.get("height", 340)))
        elif t == "pie":
            heights.append(int(block.get("height", 360)))
        elif t == "pie3d":
            heights.append(int(block.get("height", 380)))
        elif t == "table":
            n_rows = len(block.get("rows", []))
            n_head = 1 if block.get("headers") else 0
            heights.append(70 + (n_rows + n_head) * 30)
        elif t == "image":
            heights.append(int(block.get("height", 400)))
        else:
            heights.append(0)

    header_h = 0
    if title:
        header_h += 66
    if subtitle:
        header_h += 34

    total_h = padding * 2 + header_h + sum(heights) + max(0, len(blocks) - 1) * 20
    total_h = max(600, total_h)

    # Draw background
    bg_grad = theme.get("bg_grad")
    if isinstance(bg_grad, (tuple, list)) and len(bg_grad) >= 2:
        bg_c1, bg_c2 = str(bg_grad[0]), str(bg_grad[1])
    else:
        bg_c1 = bg_c2 = theme_str(theme, "bg")
    canvas = make_gradient_bg(width, total_h, bg_c1, bg_c2).convert("RGBA")

    draw = ImageDraw.Draw(canvas)

    # Title
    y = padding
    if title:
        draw.text((padding, y), title, font=font_title, fill=theme_str(theme, "text"))
        y += 58
    if subtitle:
        draw.text((padding, y), subtitle, font=font_sub, fill=theme_str(theme, "text_dim"))
        y += 34
    if title or subtitle:
        # subtle divider
        draw.line([(padding, y), (width - padding, y)], fill=theme_str(theme, "border"), width=2)
        y += 8

    # Blocks
    for idx, block in enumerate(blocks):
        h = heights[idx]
        if h <= 0 or not isinstance(block, dict):
            continue
        box = (padding, y, width - padding, y + h)
        t = block.get("type", "text")

        if t == "heading":
            draw_centered_text(draw, (box[0], box[1], box[2], box[1] + h),
                                str(block.get("text", "")), font_h, theme_str(theme, "text"))
        elif t == "text":
            lines = wrap_lines(draw, block.get("text", ""), font_text, inner_w)
            ty = y
            for line in lines:
                draw.text((padding, ty), line, font=font_text, fill=theme_str(theme, "text"))
                ty += 26
        elif t == "divider":
            mid_y = y + h // 2
            draw.line([(padding + 20, mid_y), (width - padding - 20, mid_y)],
                      fill=theme_str(theme, "border"), width=2)
        elif t == "bar":
            render_bar_chart(canvas, box, block, theme)
        elif t == "line":
            render_line_chart(canvas, box, block, theme)
        elif t == "pie":
            render_pie_chart(canvas, box, block, theme, depth=0)
        elif t == "pie3d":
            render_pie_chart(canvas, box, block, theme, depth=max(12, h // 20))
        elif t == "table":
            render_table(canvas, box, block, theme)
        elif t == "image":
            img = preloaded.get(idx)
            if img is not None:
                render_image_block(canvas, box, img, theme)

        y += h + 20

    out = BytesIO()
    canvas.convert("RGB").save(out, format="PNG", optimize=True)
    out.seek(0)
    return out


def extract_chart_marker(text: str) -> tuple[JsonDict | None, str]:
    if not text or "!chart" not in text:
        return None, text
    # try fenced first
    m = re.search(r'!chart\s*\n?```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if not m:
        # bare json (greedy balanced)
        idx = text.find("!chart")
        if idx >= 0:
            start = text.find("{", idx)
            if start >= 0:
                depth = 0
                end = -1
                in_str = False
                esc = False
                for i in range(start, len(text)):
                    c = text[i]
                    if esc:
                        esc = False
                        continue
                    if c == "\\":
                        esc = True
                        continue
                    if c == '"':
                        in_str = not in_str
                        continue
                    if in_str:
                        continue
                    if c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            break
                if end > 0:
                    raw = text[start:end]
                    try:
                        spec = json_dict(json.loads(raw))
                        remaining = (text[:idx] + text[end:]).strip()
                        return spec, remaining
                    except Exception:
                        pass
        return None, text
    try:
        spec = json_dict(json.loads(m.group(1)))
        remaining = (text[:m.start()] + text[m.end():]).strip()
        return spec, remaining
    except Exception as e:
        logger.warning(f"chart json parse fail: {e}")
        return None, text

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFilter, ImageFont

TZ = ZoneInfo("Europe/Bucharest")
OUT_DIR = Path("instagram/autopilot")
STYLE_VERSION = 1
HORIZON_DAYS = 14

BG_TOP = (4, 5, 6)
BG_BOTTOM = (14, 16, 18)
WHITE = (247, 249, 250)
MUTED = (160, 166, 170)
GREEN = (9, 255, 0)
GREEN_SOFT = (76, 255, 68)
PANEL = (20, 23, 25)
GRID = (33, 37, 40)

PILLARS = [
    "system_chain",
    "input_latency",
    "frametime_consistency",
    "testing_method",
    "cs16_authority",
    "pc_optimization",
    "competitive_setup",
    "myth_busting",
]

COPY = {
    "system_chain": {
        "eyebrow": "COMPETITIVE SYSTEMS",
        "headline": "THE WHOLE CHAIN MATTERS",
        "sub": "Mouse → USB → CPU → game → frametimes → display",
        "micro": "ONE WEAK LINK CAN MAKE A FAST PC FEEL WRONG",
    },
    "input_latency": {
        "eyebrow": "INPUT PATH",
        "headline": "INPUT FEEL IS A SYSTEM",
        "sub": "Measure the path. Don’t chase one magic setting.",
        "micro": "DEVICE → USB → CPU → GAME → DISPLAY",
    },
    "frametime_consistency": {
        "eyebrow": "FRAME DELIVERY",
        "headline": "SMOOTH > AVERAGE FPS",
        "sub": "Stable frametimes beat a pretty FPS counter.",
        "micro": "CONSISTENCY IS WHAT YOUR HAND ACTUALLY FEELS",
    },
    "testing_method": {
        "eyebrow": "DIAGNOSTIC METHOD",
        "headline": "BASELINE. CHANGE ONE THING.",
        "sub": "Measure → compare → keep or revert.",
        "micro": "STOP TUNING BLIND",
    },
    "cs16_authority": {
        "eyebrow": "CS 1.6 / FASTCUP",
        "headline": "CS 1.6 EXPOSES BAD TIMING",
        "sub": "Less visual noise. More obvious inconsistency.",
        "micro": "OLD GAME. USEFUL DIAGNOSTIC.",
    },
    "pc_optimization": {
        "eyebrow": "FULL PC OPTIMIZATION",
        "headline": "OPTIMIZE THE SYSTEM",
        "sub": "Windows • CPU/GPU • input • game • display",
        "micro": "COHERENT CHANGES. MEASURABLE RESULTS.",
    },
    "competitive_setup": {
        "eyebrow": "COMPETITIVE SETUP",
        "headline": "CONSISTENCY WINS",
        "sub": "A coherent setup beats a pile of random tweaks.",
        "micro": "BUILD A SYSTEM YOU CAN TRUST ROUND AFTER ROUND",
    },
    "myth_busting": {
        "eyebrow": "PERFORMANCE MYTH",
        "headline": "HIGH FPS ≠ LOW LATENCY",
        "sub": "Fast numbers can still feel wrong.",
        "micro": "MEASURE MORE THAN ONE COUNTER",
    },
}


def font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    candidates = []
    if mono:
        candidates.extend([
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf",
        ])
    elif bold:
        candidates.extend([
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ])
    else:
        candidates.extend([
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ])
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def gradient(width: int, height: int) -> Image.Image:
    image = Image.new("RGB", (width, height), BG_TOP)
    px = image.load()
    for y in range(height):
        t = y / max(height - 1, 1)
        # Gentle nonlinear vertical gradient keeps the visual dark and premium.
        t2 = t * t * (3 - 2 * t)
        row = tuple(int(a + (b - a) * t2) for a, b in zip(BG_TOP, BG_BOTTOM))
        for x in range(width):
            px[x, y] = row
    return image


def add_grid(draw: ImageDraw.ImageDraw, width: int, height: int, step: int) -> None:
    for x in range(0, width, step):
        draw.line((x, 0, x, height), fill=GRID, width=1)
    for y in range(0, height, step):
        draw.line((0, y, width, y), fill=GRID, width=1)


def rounded_panel(base: Image.Image, box: tuple[int, int, int, int], radius: int = 34) -> None:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle(box, radius=radius, fill=(*PANEL, 220), outline=(74, 80, 84, 105), width=2)
    # Controlled neon edge only on one side; avoids an esports-glow look.
    x0, y0, x1, y1 = box
    d.line((x0 + radius, y0, min(x0 + radius + 170, x1 - radius), y0), fill=(*GREEN, 220), width=4)
    base.alpha_composite(overlay)


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        probe = word if not current else current + " " + word
        if draw.textbbox((0, 0), probe, font=fnt)[2] <= max_width:
            current = probe
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wave(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], phase: float) -> None:
    x0, y0, x1, y1 = box
    mid = (y0 + y1) / 2
    amp = (y1 - y0) * 0.26
    points = []
    for x in range(x0, x1 + 1, 5):
        t = (x - x0) / max(x1 - x0, 1)
        jitter = math.sin(t * math.pi * 8 + phase) * 0.55 + math.sin(t * math.pi * 19 + phase * 0.7) * 0.18
        y = mid + amp * jitter
        points.append((x, int(y)))
    draw.line(points, fill=GREEN, width=4)
    draw.line((x0, int(mid), x1, int(mid)), fill=(80, 86, 90), width=1)


def draw_chain(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], labels: list[str]) -> None:
    x0, y0, x1, y1 = box
    gap = (x1 - x0) / max(len(labels) - 1, 1)
    cy = int((y0 + y1) / 2)
    xs = [int(x0 + i * gap) for i in range(len(labels))]
    draw.line((xs[0], cy, xs[-1], cy), fill=(95, 101, 105), width=3)
    small = font(18, bold=True, mono=True)
    for i, (x, label) in enumerate(zip(xs, labels)):
        r = 13 if i not in {0, len(labels) - 1} else 17
        draw.ellipse((x - r, cy - r, x + r, cy + r), fill=GREEN if i % 2 == 0 else WHITE)
        tw = draw.textbbox((0, 0), label, font=small)[2]
        draw.text((x - tw / 2, cy + 28), label, fill=MUTED, font=small)


def draw_crosshair(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    radius = min(x1 - x0, y1 - y0) // 3
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=(80, 86, 90), width=2)
    gap = radius // 4
    draw.line((cx - radius, cy, cx - gap, cy), fill=GREEN, width=4)
    draw.line((cx + gap, cy, cx + radius, cy), fill=GREEN, width=4)
    draw.line((cx, cy - radius, cx, cy - gap), fill=GREEN, width=4)
    draw.line((cx, cy + gap, cx, cy + radius), fill=GREEN, width=4)
    draw.rectangle((cx - 3, cy - 3, cx + 3, cy + 3), fill=WHITE)


def draw_visual(draw: ImageDraw.ImageDraw, pillar: str, box: tuple[int, int, int, int], seed: int) -> None:
    if pillar in {"system_chain", "input_latency", "pc_optimization"}:
        labels = ["MOUSE", "USB", "CPU", "GAME", "DISPLAY"] if pillar != "pc_optimization" else ["OS", "CPU", "GPU", "GAME", "DISPLAY"]
        draw_chain(draw, box, labels)
    elif pillar in {"frametime_consistency", "myth_busting"}:
        draw_wave(draw, box, phase=(seed % 17) / 3)
    elif pillar == "cs16_authority":
        draw_crosshair(draw, box)
    else:
        x0, y0, x1, y1 = box
        width = x1 - x0
        row_h = max((y1 - y0) // 4, 1)
        for i in range(4):
            yy = y0 + i * row_h
            level = 0.38 + (((seed + i * 13) % 52) / 100)
            draw.rounded_rectangle((x0, yy, x1, yy + 16), radius=8, fill=(54, 59, 63))
            draw.rounded_rectangle((x0, yy, int(x0 + width * level), yy + 16), radius=8, fill=GREEN if i == 2 else WHITE)
            label = ["INPUT", "FRAME", "SYSTEM", "DISPLAY"][i]
            draw.text((x0, yy + 24), label, fill=MUTED, font=font(16, bold=True, mono=True))


def compose(day, pillar: str, width: int, height: int, story: bool) -> Image.Image:
    base_rgb = gradient(width, height)
    base = base_rgb.convert("RGBA")
    d = ImageDraw.Draw(base)
    add_grid(d, width, height, 90 if story else 72)

    # Vignette / depth.
    vignette = Image.new("L", (width, height), 0)
    vd = ImageDraw.Draw(vignette)
    vd.ellipse((-width * 0.2, -height * 0.1, width * 1.15, height * 0.9), fill=120)
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=160))
    haze = Image.new("RGBA", (width, height), (9, 255, 0, 0))
    haze.putalpha(vignette.point(lambda p: int(p * 0.12)))
    base.alpha_composite(haze)

    margin = 78 if story else 72
    copy = COPY[pillar]

    eyebrow_font = font(24 if story else 22, bold=True, mono=True)
    headline_font = font(76 if story else 68, bold=True)
    sub_font = font(34 if story else 30)
    micro_font = font(20 if story else 18, bold=True, mono=True)
    footer_font = font(20 if story else 18, bold=True, mono=True)

    d.text((margin, margin), copy["eyebrow"], font=eyebrow_font, fill=GREEN)
    d.text((width - margin - 160, margin), day.strftime("%d.%m.%y"), font=micro_font, fill=MUTED)

    headline_y = margin + (108 if story else 88)
    lines = wrap(d, copy["headline"], headline_font, width - margin * 2)
    y = headline_y
    for line in lines[:3]:
        d.text((margin, y), line, font=headline_font, fill=WHITE)
        y += headline_font.size + 8

    y += 18
    for line in wrap(d, copy["sub"], sub_font, width - margin * 2)[:3]:
        d.text((margin, y), line, font=sub_font, fill=(210, 214, 216))
        y += sub_font.size + 10

    if story:
        panel_top = max(y + 85, int(height * 0.48))
        panel_bottom = height - 250
    else:
        panel_top = max(y + 55, int(height * 0.53))
        panel_bottom = height - 180
    panel_box = (margin, panel_top, width - margin, panel_bottom)
    rounded_panel(base, panel_box, 34)
    d = ImageDraw.Draw(base)
    inner = (panel_box[0] + 50, panel_box[1] + 60, panel_box[2] - 50, panel_box[3] - 80)
    draw_visual(d, pillar, inner, seed=day.toordinal())

    d.text((margin, panel_bottom + 42), copy["micro"], font=micro_font, fill=MUTED)
    d.line((margin, height - 92, width - margin, height - 92), fill=(62, 67, 70), width=1)
    d.text((margin, height - 68), "p0NDENUSH", font=footer_font, fill=WHITE)
    right = "p0ndenush.com"
    tw = d.textbbox((0, 0), right, font=footer_font)[2]
    d.text((width - margin - tw, height - 68), right, font=footer_font, fill=GREEN_SOFT)

    return base.convert("RGB")


def save_asset(day, pillar: str, story: bool) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "story" if story else "feed"
    path = OUT_DIR / f"{day.isoformat()}-{suffix}.jpg"
    size = (1080, 1920) if story else (1080, 1350)
    image = compose(day, pillar, *size, story=story)
    image.save(path, "JPEG", quality=92, optimize=True, progressive=True, subsampling=0)
    return path


def verify(path: Path, expected: tuple[int, int]) -> None:
    with Image.open(path) as image:
        if image.format != "JPEG" or image.mode != "RGB" or image.size != expected:
            raise RuntimeError(f"Invalid generated asset {path}: {image.format} {image.mode} {image.size}")
        image.verify()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=HORIZON_DAYS)
    parser.add_argument("--start", default="", help="YYYY-MM-DD; defaults to today in Europe/Bucharest")
    args = parser.parse_args()

    if args.days < 2 or args.days > 31:
        raise SystemExit("--days must be between 2 and 31")

    start = datetime.strptime(args.start, "%Y-%m-%d").date() if args.start else datetime.now(TZ).date()
    manifest: dict[str, object] = {
        "style_version": STYLE_VERSION,
        "timezone": "Europe/Bucharest",
        "start": start.isoformat(),
        "days": args.days,
        "assets": [],
    }

    for offset in range(args.days):
        day = start + timedelta(days=offset)
        pillar = PILLARS[day.toordinal() % len(PILLARS)]
        feed = save_asset(day, pillar, story=False)
        story = save_asset(day, pillar, story=True)
        verify(feed, (1080, 1350))
        verify(story, (1080, 1920))
        manifest["assets"].append(
            {
                "date": day.isoformat(),
                "pillar": pillar,
                "feed": str(feed),
                "story": str(story),
            }
        )
        print(f"OK {day} {pillar}: {feed.name}, {story.name}")

    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Generated {args.days * 2} assets; manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

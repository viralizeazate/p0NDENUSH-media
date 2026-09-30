from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
OUT = Path("instagram/2026-09-30-input-chain-v2.jpg")
OUT.parent.mkdir(parents=True, exist_ok=True)

im = Image.new("RGB", (W, H), (8, 8, 8))
d = ImageDraw.Draw(im)

font_paths = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
]
font_path = next(Path(p) for p in font_paths if Path(p).exists())
regular_path = Path(str(font_path).replace("Bold", ""))
if not regular_path.exists():
    regular_path = font_path

f_brand = ImageFont.truetype(str(font_path), 46)
f_head = ImageFont.truetype(str(font_path), 74)
f_body = ImageFont.truetype(str(regular_path), 34)
f_small = ImageFont.truetype(str(font_path), 30)

red = (210, 35, 45)
white = (245, 245, 245)
gray = (160, 160, 160)

d.rectangle((70, 70, 1010, 1280), outline=(45, 45, 45), width=3)
d.text((110, 130), "p0NDENUSH", font=f_brand, fill=red)
d.text((110, 250), "YOUR SETUP IS A CHAIN", font=f_head, fill=white)
d.text((110, 380), "Mouse  >  USB  >  CPU  >  Game  >  Frametime  >  Display", font=f_body, fill=gray)
d.line((110, 465, 970, 465), fill=red, width=6)
d.text((110, 545), "High FPS alone does not guarantee low latency.", font=f_body, fill=white)
d.text((110, 615), "Tune the full system — not one setting.", font=f_body, fill=white)
d.text((110, 930), "DM LATENCY", font=f_brand, fill=red)
d.text((110, 1045), "p0ndenush.com/products/full", font=f_small, fill=white)

# Meta-compatible baseline JPEG: RGB, 1080x1350, non-progressive.
im.save(OUT, "JPEG", quality=82, progressive=False, optimize=False, subsampling=2)
print(f"Generated {OUT}")

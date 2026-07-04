"""Generate optimized image assets for the portfolio.
Run:  python generate_assets.py
Produces: assets/portrait.jpg, assets/portrait.webp, assets/portrait-cyber.jpg,
          assets/portrait-cyber.webp, assets/og-image.jpg
(favicon.svg, site.webmanifest, .well-known/security.txt are static, not generated here.)
"""
import pathlib
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageOps

HERE = pathlib.Path(__file__).parent
ASSETS = HERE / "assets"; ASSETS.mkdir(exist_ok=True)
SRC = pathlib.Path(r"C:\Users\Lenovo\Downloads\Untitled design.jpg")  # hero: black-suit studio portrait
ABOUT_SRC = pathlib.Path(r"C:\Users\Lenovo\Downloads\Headshot.png")   # about: navy-suit headshot

TEAL = (45, 212, 191); GOLD = (230, 185, 79); BG = (6, 10, 20); TEXT = (233, 238, 248); MUTED = (158, 176, 203)

def font(bold=False, size=40):
    name = "arialbd.ttf" if bold else "arial.ttf"
    for p in (rf"C:\Windows\Fonts\{name}", name):
        try: return ImageFont.truetype(p, size)
        except Exception: pass
    return ImageFont.load_default()

def make_portrait():
    im = Image.open(SRC).convert("RGB")
    # resize so the long edge <= 1140 (covers 2x retina for both hero card and square crop)
    w, h = im.size
    scale = min(1.0, 1140 / max(w, h))
    if scale < 1.0:
        im = im.resize((round(w*scale), round(h*scale)), Image.LANCZOS)
    im.save(ASSETS / "portrait.jpg", "JPEG", quality=84, optimize=True, progressive=True)
    im.save(ASSETS / "portrait.webp", "WEBP", quality=80, method=6)
    print(f"  portrait.jpg / .webp  ({im.size[0]}x{im.size[1]})")
    return im.size

def make_about():
    im = Image.open(ABOUT_SRC).convert("RGB")
    w, h = im.size
    scale = min(1.0, 1000 / max(w, h))
    if scale < 1.0:
        im = im.resize((round(w*scale), round(h*scale)), Image.LANCZOS)
    im.save(ASSETS / "about.jpg", "JPEG", quality=86, optimize=True, progressive=True)
    im.save(ASSETS / "about.webp", "WEBP", quality=82, method=6)
    print(f"  about.jpg / .webp  ({im.size[0]}x{im.size[1]})")
    return im.size

def make_cyber_portrait():
    """A 'digital twin' of the real portrait: teal duotone + edge glow + scanlines + glitch bands."""
    im = Image.open(SRC).convert("L")
    w, h = im.size
    scale = min(1.0, 1140 / max(w, h))
    if scale < 1.0:
        im = im.resize((round(w*scale), round(h*scale)), Image.LANCZOS)
    base = ImageOps.autocontrast(im.filter(ImageFilter.MedianFilter(3)), cutoff=1)

    # duotone: shadows -> deep navy, highlights -> glowing teal (lit subject reads as a hologram)
    dark, light = (4, 10, 22), (52, 214, 196)
    luts = [[int(dark[c] + (light[c]-dark[c]) * (i/255)) for i in range(256)] for c in range(3)]
    duo = Image.merge("RGB", [base.point(l) for l in luts])

    # glowing edge lines (wireframe feel) — blur first so wall texture doesn't speckle
    edges = base.filter(ImageFilter.GaussianBlur(1.4)).filter(ImageFilter.FIND_EDGES)
    edges = edges.point(lambda x: 255 if x > 24 else 0).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    edge_rgb = Image.merge("RGB", [edges.point(lambda x, c=c: int(x*c/255)) for c in (110, 232, 214)])
    out = ImageChops.screen(duo, edge_rgb)

    # scanlines: darken every 3rd row
    sl = Image.new("L", (1, 3), 255); sl.putpixel((0, 2), 168)
    out = ImageChops.multiply(out, Image.merge("RGB", [sl.resize(out.size)]*3))

    # baked-in glitch bands (deterministic)
    rng = random.Random(2209)
    W, H = out.size
    for _ in range(9):
        y0 = rng.randint(0, H-18); hgt = rng.randint(4, 16); dx = rng.randint(-16, 16)
        band = out.crop((0, y0, W, y0+hgt))
        out.paste(band, (dx, y0))
    out.save(ASSETS / "portrait-cyber.jpg", "JPEG", quality=84, optimize=True, progressive=True)
    out.save(ASSETS / "portrait-cyber.webp", "WEBP", quality=80, method=6)
    print(f"  portrait-cyber.jpg / .webp  ({W}x{H})")


def circle_crop(im, d):
    w, h = im.size; s = min(w, h)
    im = im.crop(((w-s)//2, int((h-s)*0.12), (w+s)//2, int((h-s)*0.12)+s)).resize((d, d), Image.LANCZOS)
    mask = Image.new("L", (d, d), 0); ImageDraw.Draw(mask).ellipse((0, 0, d, d), fill=255)
    return im, mask

def make_og():
    W, H = 1200, 630
    og = Image.new("RGB", (W, H), BG)
    # vertical gradient + teal glow
    grad = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / H
        grad.putpixel((0, y), (int(6+t*8), int(10+t*12), int(20+t*22)))
    og.paste(grad.resize((W, H)))
    glow = Image.new("RGB", (W, H), BG); gd = ImageDraw.Draw(glow)
    gd.ellipse((720, -180, 1320, 420), fill=(14, 60, 70))
    og = Image.blend(og, glow, 0.5).filter(ImageFilter.GaussianBlur(60))
    d = ImageDraw.Draw(og)

    # teal accent bar
    d.rounded_rectangle((80, 150, 90, 480), radius=5, fill=TEAL)

    # eyebrow
    d.text((120, 152), "GRC  ·  SECOPS  ·  IAM  ·  AI SECURITY", font=font(False, 24), fill=TEAL)
    # name (two lines)
    d.text((118, 196), "Darshangiri", font=font(True, 86), fill=TEXT)
    d.text((118, 290), "Goswami", font=font(True, 86), fill=TEXT)
    # role
    d.text((120, 404), "Compliance · Security Operations · Identity & Access", font=font(False, 28), fill=MUTED)
    # frameworks
    d.text((120, 452), "GDPR · DORA · NIS2 · ISO 27001 · NIST CSF · EU AI Act", font=font(False, 24), fill=GOLD)
    # url
    d.text((120, 540), "darshan2209.github.io/darshangiri-goswami", font=font(False, 22), fill=(103, 120, 154))

    # portrait circle on the right with teal ring
    try:
        src = Image.open(SRC).convert("RGB")
        diam = 360; cx, cy = 980, 300
        circ, mask = circle_crop(src, diam)
        ring = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring)
        rd.ellipse((cx-diam//2-8, cy-diam//2-8, cx+diam//2+8, cy+diam//2+8), outline=TEAL, width=6)
        og.paste(circ, (cx-diam//2, cy-diam//2), mask)
        og.paste(ring, (0, 0), ring)
        # small gold verified shield badge
        bx, by = cx+diam//2-50, cy+diam//2-50
        d.ellipse((bx-34, by-34, bx+34, by+34), fill=BG, outline=GOLD, width=4)
        d.line((bx-14, by, bx-3, by+12), fill=GOLD, width=6)
        d.line((bx-3, by+12, bx+16, by-12), fill=GOLD, width=6)
    except Exception as e:
        print("  (portrait circle skipped:", e, ")")

    og.save(ASSETS / "og-image.jpg", "JPEG", quality=88, optimize=True)
    print(f"  og-image.jpg  ({W}x{H})")

if __name__ == "__main__":
    sz = make_portrait()
    asz = make_about()
    make_cyber_portrait()
    make_og()
    print(f"\n  HERO width/height attrs: {sz[0]}x{sz[1]}   ABOUT width/height attrs: {asz[0]}x{asz[1]}")
    print(f"\n  HERO/ABOUT portrait intrinsic size for width/height attrs: {sz[0]}x{sz[1]}")

"""Generate optimized image assets for the portfolio.
Run:  python generate_assets.py
Produces: assets/portrait.jpg, assets/portrait.webp, assets/portrait-cyber.jpg,
          assets/portrait-cyber.webp, assets/og-image.jpg
(favicon.svg, site.webmanifest, .well-known/security.txt are static, not generated here.)
The social card is drawn with the site's own self-hosted fonts from fonts/.
"""
import pathlib
import random
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageOps

HERE = pathlib.Path(__file__).parent
ASSETS = HERE / "assets"; ASSETS.mkdir(exist_ok=True)
FONTS = HERE / "fonts"
# Original imports from Downloads. Those files are gone from this machine, so each
# falls back to the committed asset it originally produced — enough to regenerate
# the OG card (which only needs a circle crop) without the source photos on hand.
# Re-point these at the originals before regenerating the hero/about portraits,
# since a fallback rebuild would resample an already-compressed JPEG.
SRC = pathlib.Path(r"C:\Users\Lenovo\Downloads\Untitled design.jpg")  # hero: black-suit studio portrait
ABOUT_SRC = pathlib.Path(r"C:\Users\Lenovo\Downloads\Headshot.png")   # about: navy-suit headshot
if not SRC.exists():
    SRC = HERE / "assets" / "portrait.jpg"
if not ABOUT_SRC.exists():
    ABOUT_SRC = HERE / "assets" / "about.jpg"

# Social-card palette: the site's tokens from the November 2026 redesign (:root in index.html).
INK = (9, 9, 9)              # --bg       #090909
PAPER = (242, 239, 235)      # --text     #f2efeb
PAPER_2 = (210, 205, 200)    # --text-2   #d2cdc8
MUTED = (160, 156, 154)      # --muted    #a09c9a
LINE = (46, 46, 45)          # --line-2   rgba(242,239,235,.16) over --bg
RED = (227, 43, 60)          # --accent   #e32b3c: type, rules, corner brackets
RED_FILL = (207, 34, 51)     # --accent-strong #cf2233: filled shapes

def site_font(stem, size, wght=None):
    """fonts/<stem>.woff2 at `size` px; `wght` sets the weight axis of a variable font (Manrope).
    Pillow opens WOFF2 itself when its FreeType has Brotli support (the Pillow 12 install this
    card was built with does). Otherwise the file is decompressed to a plain TTF in a scratch
    folder outside the repo, which needs: pip install fonttools brotli."""
    path = FONTS / f"{stem}.woff2"
    try:
        f = ImageFont.truetype(str(path), size)
    except OSError:
        f = ImageFont.truetype(str(_woff2_as_ttf(path)), size)
    if wght is not None:
        f.set_variation_by_axes([wght])
    return f

def _woff2_as_ttf(path):
    from fontTools.ttLib import TTFont
    out = pathlib.Path(tempfile.gettempdir()) / "portfolio-card-fonts" / f"{path.stem}.ttf"
    if not out.exists() or out.stat().st_mtime < path.stat().st_mtime:
        out.parent.mkdir(parents=True, exist_ok=True)
        ttf = TTFont(str(path)); ttf.flavor = None; ttf.save(str(out))
    return out

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


def circle_crop(im, d, side=0.86, top=0.03):
    """Head-and-shoulders disc of diameter d, shaded like the hero photo's frame: darker toward
    the rim, fading into the background at the bottom. portrait.jpg has white side borders, so
    the square is taken inside them: `side` of the photo's width, starting `top` of its height
    down. The mask is drawn at 4x and scaled down so the rim is smooth."""
    content = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).convert("L")
    l, t, r, b = content.point(lambda p: 255 if p > 40 else 0).getbbox() or (0, 0, *im.size)
    s = round(min(r - l, b - t) * side)
    x0 = (l + r - s) // 2; y0 = t + round((b - t) * top)
    im = im.crop((x0, y0, x0 + s, y0 + s)).resize((d, d), Image.LANCZOS)
    rim = Image.radial_gradient("L").resize((d, d), Image.BILINEAR)    # 0 centre, 255 rim
    rim = rim.point(lambda v: round(255 * 0.55 * max(0.0, (v / 255 - 0.5) / 0.5) ** 1.6))
    low = Image.linear_gradient("L").resize((d, d), Image.BILINEAR)    # 0 top, 255 bottom
    low = low.point(lambda v: round(255 * 0.7 * max(0.0, (v / 255 - 0.62) / 0.38)))
    im = Image.composite(Image.new("RGB", (d, d), INK), im, ImageChops.screen(rim, low))
    big = Image.new("L", (4 * d, 4 * d), 0)
    ImageDraw.Draw(big).ellipse((0, 0, 4 * d - 1, 4 * d - 1), fill=255)
    return im, big.resize((d, d), Image.LANCZOS)

def radial_glow(size, center, radii, color, alpha, stop=0.7):
    """CSS radial-gradient(rgba(color, alpha), transparent stop) as an RGBA layer."""
    rx, ry = radii
    ramp = Image.radial_gradient("L").resize((2 * rx, 2 * ry), Image.BILINEAR)  # 0 centre, 255 rim
    mask = Image.new("L", size, 0)
    mask.paste(ramp.point(lambda v: round(255 * alpha * max(0.0, 1 - v / 255 / stop))),
               (center[0] - rx, center[1] - ry))
    layer = Image.new("RGBA", size, color + (0,)); layer.putalpha(mask)
    return layer

def text_tracked(d, x, baseline, text, fnt, fill, tracking=0.0):
    """Left-aligned text on a baseline with CSS letter-spacing (`tracking` in em). Returns the end x."""
    step = tracking * fnt.size
    for ch in text:
        d.text((x, baseline), ch, font=fnt, fill=fill, anchor="ls")
        x += fnt.getlength(ch) + step
    return x - step

def make_og():
    """1200x630 share card in the site's look: near-black, off-white type, one red accent.
    Name in Anton, role in Manrope, small labels in IBM Plex Mono, portrait disc on the right."""
    W, H = 1200, 630
    X0, XR = 64, 1136                      # side margins
    cx, cy, diam = 960, 325, 320           # portrait disc; its left edge sits at x=800

    # the hero's background: a red glow behind the photo and a faint lift at bottom left
    card = Image.new("RGBA", (W, H), INK + (255,))
    card = Image.alpha_composite(card, radial_glow((W, H), (cx, cy), (504, 346), RED, 0.16))
    card = Image.alpha_composite(card, radial_glow((W, H), (120, H), (720, 252), PAPER, 0.04))
    card = card.convert("RGB")
    d = ImageDraw.Draw(card)

    # kicker row: red rule, tracked mono label, hairline under it
    d.rectangle((X0, 80, X0 + 35, 82), fill=RED)
    text_tracked(d, X0 + 52, 88, "DETECTION · IDENTITY · GOVERNANCE",
                 site_font("ibm-plex-mono-500-latin", 20), RED, 0.14)
    d.line((X0, 118, XR, 118), fill=LINE, width=1)

    # name in uppercase Anton like the hero, with the hero's red caret after the surname.
    # Both text lines must clear the portrait disc, whose left edge sits at x=800 (its
    # corner brackets start at x=784); at 136px "DARSHANGIRI" ends near x=720. Longer
    # strings run under the photo instead of wrapping, so check the render after editing.
    name = site_font("anton-latin", 136)
    for word, base in (("DARSHANGIRI", 273), ("GOSWAMI", 395)):
        d.text((X0 - name.getbbox(word, anchor="ls")[0], base), word, font=name, fill=PAPER, anchor="ls")
    caret_x = d.textbbox((X0 - name.getbbox("GOSWAMI", anchor="ls")[0], 395), "GOSWAMI", font=name, anchor="ls")[2] + 8
    d.rectangle((caret_x, 395 - 12, caret_x + 57, 395), fill=RED_FILL)

    # role in Manrope; stack in mono (named tools read as evidence where acronyms read as reading)
    mono = site_font("ibm-plex-mono-400-latin", 20)
    d.text((X0, 453), "Detection & Response · Cloud · Identity",
           font=site_font("manrope-latin", 30, wght=600), fill=PAPER_2, anchor="ls")
    d.text((X0, 493), "Zeek · Kafka · Wazuh/OpenSearch · MISP · AWS · k3s", font=mono, fill=MUTED, anchor="ls")

    # footer row: hairline, then the url
    d.line((X0, 530, XR, 530), fill=LINE, width=1)
    d.text((X0, 566), "darshan2209.github.io/darshangiri-goswami", font=mono, fill=MUTED, anchor="ls")

    # portrait disc framed by the hero photo's red corner brackets
    try:
        disc, mask = circle_crop(Image.open(SRC).convert("RGB"), diam)
        card.paste(disc, (cx - diam // 2, cy - diam // 2), mask)
        l, t, r, b = cx - diam // 2 - 16, cy - diam // 2 - 16, cx + diam // 2 + 16, cy + diam // 2 + 16
        arm, w = 36, 3
        d.rectangle((l, t, l + arm, t + w - 1), fill=RED); d.rectangle((l, t, l + w - 1, t + arm), fill=RED)
        d.rectangle((r - arm, b - w + 1, r, b), fill=RED); d.rectangle((r - w + 1, b - arm, r, b), fill=RED)
    except Exception as e:
        print("  (portrait disc skipped:", e, ")")

    # 4:4:4 chroma keeps the thin red type and rules crisp
    card.save(ASSETS / "og-image.jpg", "JPEG", quality=88, optimize=True, subsampling=0)
    print(f"  og-image.jpg  ({W}x{H})")

if __name__ == "__main__":
    sz = make_portrait()
    asz = make_about()
    make_cyber_portrait()
    make_og()
    print(f"\n  HERO width/height attrs: {sz[0]}x{sz[1]}   ABOUT width/height attrs: {asz[0]}x{asz[1]}")
    print(f"\n  HERO/ABOUT portrait intrinsic size for width/height attrs: {sz[0]}x{sz[1]}")

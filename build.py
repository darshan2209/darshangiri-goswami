"""Build index.html from index.template.html by embedding photos as base64.
Run:  python build.py
"""
import base64, mimetypes, pathlib, sys

HERE = pathlib.Path(__file__).parent
TEMPLATE = HERE / "index.template.html"
OUT = HERE / "index.html"

# Source photos (edit these paths if you move the images)
HERO_PHOTO  = pathlib.Path(r"C:\Users\Lenovo\Pictures\photo_2026-04-13_15-04-24.jpg")   # suit portrait
ABOUT_PHOTO = pathlib.Path(r"C:\Users\Lenovo\Pictures\photo_2026-04-17_10-30-14.jpg")   # headshot

def data_uri(p: pathlib.Path) -> str:
    if not p.exists():
        print(f"  ! missing: {p}  (placeholder left blank)")
        return ""
    mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"

def main():
    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("__HERO_PHOTO__", data_uri(HERO_PHOTO))
    html = html.replace("__ABOUT_PHOTO__", data_uri(ABOUT_PHOTO))
    OUT.write_text(html, encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    print(f"  built {OUT}  ({kb:.0f} KB)")

if __name__ == "__main__":
    main()

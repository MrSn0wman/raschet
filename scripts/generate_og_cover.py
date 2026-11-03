"""Reproduce the Raschet.net social cover (optional Pillow development tool)."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def font_path(bold):
    names = (["C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else
             ["C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    for name in names:
        if Path(name).is_file():
            return name
    raise SystemExit("Provide --regular-font and --bold-font with Cyrillic-capable TTF files")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "assets" / "og-cover.png")
    parser.add_argument("--regular-font")
    parser.add_argument("--bold-font")
    args = parser.parse_args()
    scale = 2
    image = Image.new("RGB", (1200 * scale, 630 * scale))
    draw = ImageDraw.Draw(image)
    def box(coords):
        return tuple(round(v * scale) for v in coords)
    def font(size, bold=False):
        return ImageFont.truetype((args.bold_font if bold else args.regular_font) or font_path(bold), round(size * scale))
    for y in range(630 * scale):
        t = y / (630 * scale - 1)
        draw.line((0, y, 1200 * scale, y), fill=(int(10 + 4*t), int(107 + 22*t), int(64 + 15*t)))
    overlay = Image.new("RGBA", image.size)
    deco = ImageDraw.Draw(overlay)
    deco.ellipse(box((800, -260, 1460, 400)), fill=(255, 255, 255, 15))
    deco.ellipse(box((750, 430, 1130, 810)), fill=(255, 255, 255, 15))
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box((90, 161, 176, 247)), radius=22*scale, fill="white")
    for x,y,filled in [(114,185,True),(139,185,False),(114,210,False),(139,210,True)]:
        draw.rounded_rectangle(box((x,y,x+17,y+17)), radius=3*scale, fill="#087c4d" if filled else "white", outline="#087c4d", width=3*scale)
    draw.text(box((196,174)), "Расчёт", font=font(64, True), fill="white")
    draw.rounded_rectangle(box((418,194,496,235)), radius=9*scale, fill="#f3cd18")
    draw.text(box((429,200)), ".net", font=font(24), fill="#076c46")
    draw.text(box((90,287)), "Онлайн-калькуляторы и инструменты для", font=font(32, True), fill="white")
    draw.text(box((90,333)), "повседневных и финансовых расчётов", font=font(32, True), fill="white")
    x = 90
    for label in ["Ипотека", "НДФЛ", "Вклады", "Проценты", "ОСАГО", "Даты", "Генераторы"]:
        width = draw.textlength(label, font=font(22)) / scale + 42
        draw.rounded_rectangle(box((x,417,x+width,469)), radius=26*scale, outline="#90bba7", width=scale)
        draw.text(box((x+21,431)), label, font=font(22), fill="white")
        x += width + 10
    image = image.resize((1200,630), Image.Resampling.LANCZOS)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output, optimize=True)
    print("Cover generated:", args.output)


if __name__ == "__main__":
    main()

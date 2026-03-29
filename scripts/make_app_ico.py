"""
Собирает assets/app.ico из assets/app.png для встраивания в CorePilot.exe.

Для мелких размеров (16–32) слегка усиливает контраст и резкость — текст всё равно
часто нечитаем; для идеальной читаемости лучше отдельная упрощённая картинка без мелкого текста.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PNG = ROOT / "assets" / "app.png"
DEFAULT_ICO = ROOT / "assets" / "app.ico"

SIZES = (16, 24, 32, 48, 64, 128, 256)


def _layer_for_size(im: Image.Image, size: int) -> Image.Image:
    """Квадрат: вписываем в size×size, для мелких — чуть контраста и unsharp."""
    rgba = im.convert("RGBA")
    side = min(rgba.size)
    rgba = ImageOps.fit(rgba, (side, side), method=Image.Resampling.LANCZOS)
    out = rgba.resize((size, size), Image.Resampling.LANCZOS)
    if size <= 32:
        out = ImageEnhance.Contrast(out).enhance(1.12)
        out = out.filter(ImageFilter.UnsharpMask(radius=0.45, percent=100, threshold=1))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="PNG → ICO для PyInstaller (Windows exe icon).")
    ap.add_argument(
        "-i",
        "--input",
        type=Path,
        default=DEFAULT_PNG,
        help=f"Исходный PNG (по умолчанию {DEFAULT_PNG.name})",
    )
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_ICO,
        help=f"Куда записать ICO (по умолчанию {DEFAULT_ICO.name})",
    )
    args = ap.parse_args()
    if not args.input.is_file():
        print(f"Нет файла: {args.input}", file=sys.stderr)
        return 1
    im = Image.open(args.input)
    layers = [_layer_for_size(im, s) for s in SIZES]
    sizes = [(s, s) for s in SIZES]
    # Pillow ICO: первый кадр задаёт max(w,h); если это 16×16, остальные размеры отвергаются
    # (см. IcoImagePlugin._save). Поэтому сохраняем с самым большым слоём первым.
    largest = layers[-1]
    smaller = layers[:-1]
    largest.save(
        args.output,
        format="ICO",
        sizes=sizes,
        append_images=smaller,
    )
    print(f"OK: {args.output} ({', '.join(map(str, SIZES))} px)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

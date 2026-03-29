"""
Копирует assets/CorePilot.install_root рядом с exe после сборки (PyInstaller и т.п.).

Примеры:
  python scripts/copy_install_marker.py dist
  python scripts/copy_install_marker.py dist/CorePilot.exe
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER_SRC = ROOT / "assets" / "CorePilot.install_root"


def main() -> int:
    if not MARKER_SRC.is_file():
        print(f"Нет файла маркера: {MARKER_SRC}", file=sys.stderr)
        return 1
    ap = argparse.ArgumentParser(description="Копирует CorePilot.install_root в папку релиза.")
    ap.add_argument(
        "target",
        nargs="?",
        default="dist",
        help="Каталог с exe или полный путь к .exe (по умолчанию dist)",
    )
    args = ap.parse_args()
    t = Path(args.target)
    if t.suffix.lower() == ".exe" or (t.exists() and t.is_file()):
        dest_dir = t.resolve().parent
    else:
        dest_dir = t.resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "CorePilot.install_root"
    shutil.copy2(MARKER_SRC, dest)
    print(f"OK: {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

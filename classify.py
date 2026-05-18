"""
image-classifier: Visual similarity-based image grouping tool.

Usage:
    classify.py [--dir DIR] [--eps EPS] [--min-samples N]

Options:
    --dir          Target folder (default: script location)
    --eps          DBSCAN epsilon, controls grouping sensitivity (default: 0.35)
    --min-samples  Minimum images per group (default: 2)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
RESERVED_PREFIXES = ("group_", "_ungrouped", "_classify_backup")


def scan_images(directory: Path) -> list[Path]:
    """대상 폴더 최상위의 지원 이미지 파일 목록을 반환한다."""
    directory = Path(directory)
    if not directory.exists():
        print(f"[ERROR] 폴더를 찾을 수 없습니다: {directory}")
        sys.exit(1)

    paths = [
        p for p in directory.iterdir()
        if p.is_file()
        and p.suffix.lower() in SUPPORTED_EXTENSIONS
        and not any(p.parent.name.startswith(pfx) for pfx in RESERVED_PREFIXES)
    ]
    return paths


def parse_args():
    parser = argparse.ArgumentParser(
        description="Group images by visual similarity."
    )
    parser.add_argument("--dir", default=None, help="Target folder path")
    parser.add_argument("--eps", type=float, default=0.35, help="DBSCAN epsilon (0.0~1.0)")
    parser.add_argument("--min-samples", type=int, default=2, help="Min images per group")
    return parser.parse_args()


def main():
    args = parse_args()
    target = Path(args.dir) if args.dir else Path(__file__).parent

    images = scan_images(target)
    if not images:
        print("이미지를 찾을 수 없습니다.")
        sys.exit(0)

    print("image-classifier - 구현 예정")
    print(f"  이미지 수  : {len(images)}")
    print(f"  eps        : {args.eps}")
    print(f"  min-samples: {args.min_samples}")


if __name__ == "__main__":
    main()

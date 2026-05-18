"""
image-classifier: Visual similarity-based image grouping tool.

Usage:
    classify.py [--dir DIR] [--eps EPS] [--min-samples N]

Options:
    --dir          Target folder (default: script location)
    --eps          DBSCAN epsilon, controls grouping sensitivity (default: 0.35)
    --min-samples  Minimum images per group (default: 2)
"""

import argparse
import sys


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
    print("image-classifier - 구현 예정")
    print(f"  dir        : {args.dir}")
    print(f"  eps        : {args.eps}")
    print(f"  min-samples: {args.min_samples}")


if __name__ == "__main__":
    main()

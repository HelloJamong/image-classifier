"""
image-classifier: Visual similarity-based image grouping tool.

Usage:
    classify.py [--dir DIR] [--eps EPS] [--min-samples N]

Options:
    --dir          Target folder (default: executable folder when frozen, otherwise cwd)
    --eps          Normalized phash Hamming distance threshold (default: 0.32)
    --min-samples  Minimum images per group (default: 2)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import imagehash
import numpy as np
from PIL import Image
from sklearn.cluster import AgglomerativeClustering

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
RESERVED_PREFIXES = ("group_", "_ungrouped", "_classify_backup")
DEFAULT_EPS = 0.32


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


def compute_hashes(
    paths: list[Path],
) -> tuple[list[tuple[Path, np.ndarray]], list[tuple[Path, str]]]:
    """각 이미지를 phash로 해싱해 64차원 float 벡터로 반환한다.

    Returns:
        hashes:  [(path, vector), ...]  성공 목록
        skipped: [(path, reason), ...]  실패 목록
    """
    hashes: list[tuple[Path, np.ndarray]] = []
    skipped: list[tuple[Path, str]] = []
    total = len(paths)

    for i, path in enumerate(paths, 1):
        print(f"해싱 중... ({i}/{total})", end="\r")
        try:
            img = Image.open(path)
            img.seek(0)  # GIF 첫 프레임; 일반 이미지는 seek(0)이 무해함
            img = img.convert("RGB")
            h = imagehash.phash(img)
            vec = np.array(h.hash).flatten().astype(float)
            hashes.append((path, vec))
        except Exception as e:
            skipped.append((path, str(e)))

    if total:
        print()
    return hashes, skipped


def cluster(
    hashes: list[tuple[Path, np.ndarray]],
    eps: float,
    min_samples: int,
) -> tuple[dict[int, list[Path]], list[Path]]:
    """phash 벡터를 normalized Hamming distance 기준으로 클러스터링한다.

    Complete-linkage를 사용해 클러스터 내부의 모든 이미지가 threshold 이내에
    머물도록 한다. DBSCAN의 밀도 연결 방식은 중간 이미지가 다리처럼 이어질 때
    서로 다른 이미지 묶음까지 하나의 거대 그룹으로 합쳐질 수 있다.

    Returns:
        groups:    {cluster_id: [path, ...]}  (0-based 정수 키)
        ungrouped: [path, ...]                (min_samples 미만 그룹)
    """
    if not hashes:
        return {}, []

    paths = [p for p, _ in hashes]
    vectors = np.array([v for _, v in hashes])
    min_samples = max(min_samples, 1)
    if len(paths) == 1:
        if min_samples == 1:
            return {0: paths}, []
        return {}, paths
    if len(paths) < min_samples:
        return {}, paths

    labels = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=eps,
        metric="hamming",
        linkage="complete",
    ).fit_predict(vectors)

    raw_groups: dict[int, list[Path]] = {}
    ungrouped: list[Path] = []

    for path, label in zip(paths, labels):
        raw_groups.setdefault(label, []).append(path)

    groups: dict[int, list[Path]] = {}
    next_group_id = 0
    for _, group_paths in sorted(raw_groups.items()):
        if len(group_paths) < min_samples:
            ungrouped.extend(group_paths)
        else:
            groups[next_group_id] = group_paths
            next_group_id += 1

    return groups, ungrouped


def move_files(
    groups: dict[int, list[Path]],
    ungrouped: list[Path],
    target_dir: Path,
) -> list[tuple[Path, Path]]:
    """이미지를 그룹 폴더로 이동한다.

    Returns:
        [(원본경로, 이동후경로), ...]
    """
    import shutil

    moved: list[tuple[Path, Path]] = []

    for idx, (_, paths) in enumerate(sorted(groups.items()), 1):
        dest_dir = target_dir / f"group_{idx:03d}"
        dest_dir.mkdir(exist_ok=True)
        for src in paths:
            dst = dest_dir / src.name
            try:
                shutil.move(str(src), str(dst))
                moved.append((src, dst))
            except Exception as e:
                print(f"[경고] 이동 실패 ({src.name}): {e}")

    if ungrouped:
        ung_dir = target_dir / "_ungrouped"
        ung_dir.mkdir(exist_ok=True)
        for src in ungrouped:
            dst = ung_dir / src.name
            try:
                shutil.move(str(src), str(dst))
                moved.append((src, dst))
            except Exception as e:
                print(f"[경고] 이동 실패 ({src.name}): {e}")

    return moved


def build_restore_script(
    moved: list[tuple[Path, Path]],
    target_dir: Path,
) -> Path | None:
    """이동된 파일을 원래 위치로 되돌리는 Windows .bat 스크립트를 생성한다.

    Returns:
        생성된 스크립트 경로, 이동 파일이 없으면 None
    """
    import datetime

    if not moved:
        return None

    backup_dir = target_dir / "_classify_backup"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    script_path = backup_dir / f"restore_{timestamp}.bat"

    lines = [
        "@echo off",
        f":: image-classifier 복원 스크립트 ({timestamp})",
        ":: 이 파일을 실행하면 분류 전 상태로 되돌립니다.",
        "",
    ]
    for src, dst in moved:
        lines.append(f'move "{dst}" "{src}"')

    script_path.write_text("\n".join(lines), encoding="utf-8")
    return script_path


def print_preview(groups: dict[int, list[Path]], ungrouped: list[Path]) -> None:
    """클러스터링 결과 미리보기를 콘솔에 출력한다."""
    print("분류 결과 미리보기")
    print("─" * 34)
    print(f"그룹 수     : {len(groups)}")
    for idx, (_, paths) in enumerate(sorted(groups.items()), 1):
        label = f"group_{idx:03d}"
        print(f"{label:<12}: {len(paths)}장")
    print(f"미분류(_ungrouped): {len(ungrouped)}장")
    print("─" * 34)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Group images by visual similarity."
    )
    parser.add_argument("--dir", default=None, help="Target folder path")
    parser.add_argument(
        "--eps",
        type=float,
        default=DEFAULT_EPS,
        help="Normalized phash Hamming distance threshold (0.0~1.0)",
    )
    parser.add_argument("--min-samples", type=int, default=2, help="Min images per group")
    return parser.parse_args()


def resolve_target_dir(arg_dir: str | None) -> Path:
    """CLI 대상 폴더를 결정한다.

    PyInstaller onefile exe에서는 ``__file__``이 임시 압축 해제 폴더를 가리킬 수 있으므로,
    --dir 미지정 시 exe가 있는 폴더를 기본 대상으로 사용한다.
    """
    if arg_dir:
        return Path(arg_dir)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path.cwd()


def main():
    args = parse_args()
    target = resolve_target_dir(args.dir)

    images = scan_images(target)
    if not images:
        print("이미지를 찾을 수 없습니다.")
        sys.exit(0)

    hashes, skipped = compute_hashes(images)

    if not hashes:
        print("처리 가능한 이미지가 없습니다.")
        _print_skip_log(skipped)
        sys.exit(0)

    groups, ungrouped = cluster(hashes, eps=args.eps, min_samples=args.min_samples)
    print_preview(groups, ungrouped)

    answer = input("실행하시겠습니까? (Y/N): ").strip().upper()
    if answer != "Y":
        print("취소되었습니다.")
        sys.exit(0)

    moved = move_files(groups, ungrouped, target)
    build_restore_script(moved, target)

    print(f"\n완료: {len(moved)}개 파일 이동.")
    _print_skip_log(skipped)
    sys.exit(0)


def _print_skip_log(skipped: list[tuple[Path, str]]) -> None:
    if skipped:
        print(f"\n[경고] 처리 실패한 파일 {len(skipped)}개:")
        for path, reason in skipped:
            print(f"  - {path.name}: {reason}")


if __name__ == "__main__":
    main()

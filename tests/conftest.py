from pathlib import Path
import pytest
from PIL import Image


def make_solid_image(path: Path, color=(255, 0, 0), size=(64, 64), fmt="PNG"):
    img = Image.new("RGB", size, color)
    img.save(path, format=fmt)
    return path


@pytest.fixture
def image_dir(tmp_path):
    """지원/비지원 파일이 혼재하는 임시 폴더."""
    (tmp_path / "photo.jpg").touch()
    (tmp_path / "photo.JPEG").touch()
    (tmp_path / "art.PNG").touch()
    (tmp_path / "anim.gif").touch()
    (tmp_path / "banner.webp").touch()
    (tmp_path / "icon.bmp").touch()
    (tmp_path / "readme.txt").touch()
    (tmp_path / "data.json").touch()
    return tmp_path


def make_gradient_image(path: Path, start: int, end: int):
    """좌→우 밝기 그라디언트 이미지 생성 (phash에서 명확히 구분됨)."""
    import numpy as np
    arr = np.tile(np.linspace(start, end, 64, dtype=np.uint8), (64, 1))
    img = Image.fromarray(np.stack([arr, arr, arr], axis=2), mode="RGB")
    img.save(path)
    return path


@pytest.fixture
def valid_images(tmp_path):
    """실제 픽셀 데이터가 있는 이미지 파일 3장."""
    make_gradient_image(tmp_path / "red.png", start=0, end=200)
    make_gradient_image(tmp_path / "red2.png", start=0, end=200)   # red와 동일
    make_gradient_image(tmp_path / "blue.png", start=200, end=0)   # 반대 방향
    return tmp_path


@pytest.fixture
def corrupt_image(tmp_path):
    """손상된 이미지 파일."""
    bad = tmp_path / "bad.jpg"
    bad.write_bytes(b"not an image")
    return bad


@pytest.fixture
def reserved_dir(tmp_path):
    """예약 폴더(group_, _ungrouped, _classify_backup) 내 파일 포함."""
    (tmp_path / "photo.jpg").touch()
    (tmp_path / "group_001").mkdir()
    (tmp_path / "group_001" / "already_grouped.jpg").touch()
    (tmp_path / "_ungrouped").mkdir()
    (tmp_path / "_ungrouped" / "misc.png").touch()
    (tmp_path / "_classify_backup").mkdir()
    (tmp_path / "_classify_backup" / "restore.bat").touch()
    return tmp_path

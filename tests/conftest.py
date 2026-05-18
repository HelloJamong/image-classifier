from pathlib import Path
import pytest


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

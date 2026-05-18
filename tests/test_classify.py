import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from classify import scan_images


class TestScanImages:
    def test_returns_only_supported_extensions(self, image_dir):
        result = scan_images(image_dir)
        names = {p.name for p in result}
        assert "photo.jpg" in names
        assert "anim.gif" in names
        assert "banner.webp" in names
        assert "icon.bmp" in names
        assert "readme.txt" not in names
        assert "data.json" not in names

    def test_case_insensitive_extensions(self, image_dir):
        result = scan_images(image_dir)
        names = {p.name for p in result}
        assert "photo.JPEG" in names
        assert "art.PNG" in names

    def test_excludes_reserved_folders(self, reserved_dir):
        result = scan_images(reserved_dir)
        names = {p.name for p in result}
        assert "photo.jpg" in names
        assert "already_grouped.jpg" not in names
        assert "misc.png" not in names

    def test_empty_dir_returns_empty(self, tmp_path):
        result = scan_images(tmp_path)
        assert result == []

    def test_nonexistent_dir_raises(self, tmp_path):
        with pytest.raises(SystemExit):
            scan_images(tmp_path / "does_not_exist")

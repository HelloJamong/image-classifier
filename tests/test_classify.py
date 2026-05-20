import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from unittest.mock import patch
from classify import (
    scan_images,
    compute_hashes,
    cluster,
    print_preview,
    move_files,
    build_restore_script,
    resolve_target_dir,
    main,
)


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


class TestComputeHashes:
    def test_returns_vector_per_image(self, valid_images):
        paths = list(valid_images.glob("*.png"))
        hashes, skipped = compute_hashes(paths)
        assert len(hashes) == 3
        assert skipped == []

    def test_vector_shape_is_64(self, valid_images):
        paths = list(valid_images.glob("*.png"))
        hashes, _ = compute_hashes(paths)
        for _, vec in hashes:
            assert vec.shape == (64,)
            assert vec.dtype == float

    def test_identical_images_same_hash(self, valid_images):
        red = valid_images / "red.png"
        red2 = valid_images / "red2.png"
        hashes, _ = compute_hashes([red, red2])
        vec1 = hashes[0][1]
        vec2 = hashes[1][1]
        assert np.array_equal(vec1, vec2)

    def test_different_images_different_hash(self, valid_images):
        red = valid_images / "red.png"
        blue = valid_images / "blue.png"
        hashes, _ = compute_hashes([red, blue])
        assert not np.array_equal(hashes[0][1], hashes[1][1])

    def test_corrupt_file_is_skipped(self, corrupt_image, valid_images):
        red = valid_images / "red.png"
        hashes, skipped = compute_hashes([corrupt_image, red])
        assert len(hashes) == 1
        assert len(skipped) == 1
        assert skipped[0][0] == corrupt_image

    def test_gif_first_frame(self, tmp_path):
        from PIL import Image
        frames = [Image.new("RGB", (64, 64), (i * 80, 0, 0)) for i in range(3)]
        gif_path = tmp_path / "anim.gif"
        frames[0].save(gif_path, save_all=True, append_images=frames[1:], loop=0)
        hashes, skipped = compute_hashes([gif_path])
        assert len(hashes) == 1
        assert skipped == []


class TestCluster:
    def _make_vectors(self, valid_images):
        paths = [valid_images / "red.png", valid_images / "red2.png", valid_images / "blue.png"]
        hashes, _ = compute_hashes(paths)
        return hashes

    def test_similar_images_same_group(self, valid_images):
        hashes = self._make_vectors(valid_images)
        groups, ungrouped = cluster(hashes, eps=0.35, min_samples=2)
        # red와 red2는 같은 그룹에 배정돼야 함
        group_paths = [set(paths) for paths in groups.values()]
        red = valid_images / "red.png"
        red2 = valid_images / "red2.png"
        assert any(red in g and red2 in g for g in group_paths)

    def test_noise_goes_to_ungrouped(self, valid_images):
        hashes = self._make_vectors(valid_images)
        groups, ungrouped = cluster(hashes, eps=0.35, min_samples=2)
        # blue는 혼자이므로 ungrouped 또는 별도 그룹
        blue = valid_images / "blue.png"
        all_grouped = {p for paths in groups.values() for p in paths}
        # blue가 그룹에 없으면 ungrouped에 있어야 함
        if blue not in all_grouped:
            assert blue in ungrouped

    def test_returns_dict_and_list(self, valid_images):
        hashes = self._make_vectors(valid_images)
        groups, ungrouped = cluster(hashes, eps=0.35, min_samples=2)
        assert isinstance(groups, dict)
        assert isinstance(ungrouped, list)

    def test_empty_input(self):
        groups, ungrouped = cluster([], eps=0.35, min_samples=2)
        assert groups == {}
        assert ungrouped == []

    def test_single_image_goes_to_ungrouped(self, valid_images):
        hashes, _ = compute_hashes([valid_images / "red.png"])
        groups, ungrouped = cluster(hashes, eps=0.35, min_samples=2)
        assert groups == {}
        assert len(ungrouped) == 1


class TestPrintPreview:
    def _make_groups(self, tmp_path):
        a = tmp_path / "a.png"
        b = tmp_path / "b.png"
        c = tmp_path / "c.png"
        d = tmp_path / "d.png"
        return {0: [a, b], 1: [c]}, [d]

    def test_shows_group_count(self, tmp_path, capsys):
        groups, ungrouped = self._make_groups(tmp_path)
        print_preview(groups, ungrouped)
        out = capsys.readouterr().out
        assert "2" in out  # 그룹 수

    def test_shows_each_group_size(self, tmp_path, capsys):
        groups, ungrouped = self._make_groups(tmp_path)
        print_preview(groups, ungrouped)
        out = capsys.readouterr().out
        assert "group_001" in out
        assert "2장" in out
        assert "group_002" in out
        assert "1장" in out

    def test_shows_ungrouped_count(self, tmp_path, capsys):
        groups, ungrouped = self._make_groups(tmp_path)
        print_preview(groups, ungrouped)
        out = capsys.readouterr().out
        assert "_ungrouped" in out
        assert "1장" in out

    def test_empty_groups(self, tmp_path, capsys):
        print_preview({}, [tmp_path / "a.png"])
        out = capsys.readouterr().out
        assert "0" in out or "그룹" in out


class TestMoveFiles:
    def _make_img(self, path):
        from PIL import Image
        Image.new("RGB", (8, 8), (128, 64, 32)).save(path)
        return path

    def _setup(self, tmp_path):
        a = self._make_img(tmp_path / "a.png")
        b = self._make_img(tmp_path / "b.png")
        c = self._make_img(tmp_path / "c.png")
        groups = {0: [a, b]}
        ungrouped = [c]
        return groups, ungrouped

    def test_files_moved_to_group_dirs(self, tmp_path):
        groups, ungrouped = self._setup(tmp_path)
        move_files(groups, ungrouped, tmp_path)
        assert (tmp_path / "group_001" / "a.png").exists()
        assert (tmp_path / "group_001" / "b.png").exists()
        assert not (tmp_path / "a.png").exists()

    def test_ungrouped_moved_to_ungrouped_dir(self, tmp_path):
        groups, ungrouped = self._setup(tmp_path)
        move_files(groups, ungrouped, tmp_path)
        assert (tmp_path / "_ungrouped" / "c.png").exists()
        assert not (tmp_path / "c.png").exists()

    def test_returns_moved_list(self, tmp_path):
        groups, ungrouped = self._setup(tmp_path)
        moved = move_files(groups, ungrouped, tmp_path)
        assert len(moved) == 3
        for src, dst in moved:
            assert isinstance(src, Path)
            assert isinstance(dst, Path)
            assert dst.exists()

    def test_group_folder_zero_padded(self, tmp_path):
        groups, ungrouped = self._setup(tmp_path)
        move_files(groups, ungrouped, tmp_path)
        assert (tmp_path / "group_001").is_dir()


class TestBuildRestoreScript:
    def _moved_list(self, tmp_path):
        src1 = tmp_path / "a.png"
        dst1 = tmp_path / "group_001" / "a.png"
        src2 = tmp_path / "b.png"
        dst2 = tmp_path / "_ungrouped" / "b.png"
        return [(src1, dst1), (src2, dst2)]

    def test_creates_bat_file(self, tmp_path):
        moved = self._moved_list(tmp_path)
        script = build_restore_script(moved, tmp_path)
        assert script is not None
        assert script.suffix == ".bat"
        assert script.exists()

    def test_bat_in_backup_dir(self, tmp_path):
        moved = self._moved_list(tmp_path)
        script = build_restore_script(moved, tmp_path)
        assert script.parent.name == "_classify_backup"

    def test_bat_contains_move_commands(self, tmp_path):
        moved = self._moved_list(tmp_path)
        script = build_restore_script(moved, tmp_path)
        content = script.read_text(encoding="utf-8")
        assert "move" in content
        assert "a.png" in content
        assert "b.png" in content

    def test_bat_starts_with_echo_off(self, tmp_path):
        moved = self._moved_list(tmp_path)
        script = build_restore_script(moved, tmp_path)
        content = script.read_text(encoding="utf-8")
        assert content.startswith("@echo off")

    def test_empty_moved_returns_none(self, tmp_path):
        result = build_restore_script([], tmp_path)
        assert result is None


class TestMain:
    def _make_img(self, path):
        from PIL import Image
        Image.new("RGB", (64, 64), (100, 150, 200)).save(path)
        return path

    def _setup_dir(self, tmp_path):
        self._make_img(tmp_path / "a.png")
        self._make_img(tmp_path / "b.png")

    def test_no_dir_defaults_to_current_working_directory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert resolve_target_dir(None) == tmp_path

    def test_frozen_no_dir_defaults_to_executable_directory(self, tmp_path, monkeypatch):
        exe_dir = tmp_path / "images"
        exe_dir.mkdir()
        fake_exe = exe_dir / "classify_images.exe"
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(fake_exe))

        assert resolve_target_dir(None) == exe_dir

    def test_explicit_dir_takes_precedence(self, tmp_path, monkeypatch):
        cwd = tmp_path / "cwd"
        target = tmp_path / "target"
        cwd.mkdir()
        target.mkdir()
        monkeypatch.chdir(cwd)
        assert resolve_target_dir(str(target)) == target

    def test_n_response_skips_move(self, tmp_path):
        self._setup_dir(tmp_path)
        with patch("sys.argv", ["classify.py", "--dir", str(tmp_path)]):
            with patch("builtins.input", return_value="N"):
                with pytest.raises(SystemExit) as exc:
                    main()
        assert exc.value.code == 0
        assert (tmp_path / "a.png").exists()
        assert not (tmp_path / "group_001").exists()

    def test_y_response_moves_files(self, tmp_path):
        self._setup_dir(tmp_path)
        with patch("sys.argv", ["classify.py", "--dir", str(tmp_path)]):
            with patch("builtins.input", return_value="Y"):
                with pytest.raises(SystemExit) as exc:
                    main()
        assert exc.value.code == 0
        assert not (tmp_path / "a.png").exists()

    def test_nonexistent_dir_exits_with_error(self, tmp_path):
        missing = tmp_path / "no_such_dir"
        with patch("sys.argv", ["classify.py", "--dir", str(missing)]):
            with pytest.raises(SystemExit) as exc:
                main()
        assert exc.value.code != 0

    def test_empty_dir_exits_cleanly(self, tmp_path):
        with patch("sys.argv", ["classify.py", "--dir", str(tmp_path)]):
            with pytest.raises(SystemExit) as exc:
                main()
        assert exc.value.code == 0

    def test_skip_log_printed_for_corrupt_files(self, tmp_path, capsys):
        self._make_img(tmp_path / "good.png")
        (tmp_path / "bad.jpg").write_bytes(b"not an image")
        with patch("sys.argv", ["classify.py", "--dir", str(tmp_path)]):
            with patch("builtins.input", return_value="Y"):
                with pytest.raises(SystemExit):
                    main()
        out = capsys.readouterr().out
        assert "bad.jpg" in out


class TestIntegration:
    """전체 파이프라인 통합 테스트 — 실제 이미지 픽스처 사용."""

    def _populate(self, tmp_path):
        """유사 이미지 쌍 2장 + 이질 이미지 1장 + 손상 파일 1개 생성."""
        from PIL import Image
        import numpy as np

        def gradient(path, start, end):
            arr = np.tile(np.linspace(start, end, 64, dtype=np.uint8), (64, 1))
            Image.fromarray(np.stack([arr, arr, arr], axis=2)).save(path)

        gradient(tmp_path / "sim_a.png", 0, 200)
        gradient(tmp_path / "sim_b.png", 0, 200)   # sim_a와 동일
        gradient(tmp_path / "diff.png", 200, 0)     # 다른 이미지
        (tmp_path / "corrupt.jpg").write_bytes(b"garbage")

    def test_similar_images_grouped_together(self, tmp_path):
        self._populate(tmp_path)
        hashes, _ = compute_hashes(scan_images(tmp_path))
        groups, _ = cluster(hashes, eps=0.35, min_samples=2)
        all_groups = list(groups.values())
        sim_a = tmp_path / "sim_a.png"
        sim_b = tmp_path / "sim_b.png"
        assert any(sim_a in g and sim_b in g for g in all_groups)

    def test_corrupt_file_skipped_pipeline_continues(self, tmp_path):
        self._populate(tmp_path)
        hashes, skipped = compute_hashes(scan_images(tmp_path))
        assert any(p.name == "corrupt.jpg" for p, _ in skipped)
        assert len(hashes) == 3  # 3 valid images

    def test_full_run_y_creates_group_dirs(self, tmp_path):
        self._populate(tmp_path)
        with patch("sys.argv", ["classify.py", "--dir", str(tmp_path)]):
            with patch("builtins.input", return_value="Y"):
                with pytest.raises(SystemExit):
                    main()
        group_dirs = [d for d in tmp_path.iterdir() if d.is_dir() and d.name.startswith("group_")]
        assert len(group_dirs) >= 1

    def test_full_run_y_creates_restore_script(self, tmp_path):
        self._populate(tmp_path)
        with patch("sys.argv", ["classify.py", "--dir", str(tmp_path)]):
            with patch("builtins.input", return_value="Y"):
                with pytest.raises(SystemExit):
                    main()
        backup_dir = tmp_path / "_classify_backup"
        assert backup_dir.exists()
        bat_files = list(backup_dir.glob("restore_*.bat"))
        assert len(bat_files) == 1

    def test_full_run_n_leaves_dir_unchanged(self, tmp_path):
        self._populate(tmp_path)
        before = {p.name for p in tmp_path.iterdir() if p.is_file()}
        with patch("sys.argv", ["classify.py", "--dir", str(tmp_path)]):
            with patch("builtins.input", return_value="N"):
                with pytest.raises(SystemExit):
                    main()
        after = {p.name for p in tmp_path.iterdir() if p.is_file()}
        assert before == after

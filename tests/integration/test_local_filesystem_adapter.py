from pathlib import Path
from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter


def test_list_copy_move_ensure_dir(tmp_path: Path):
    fs = LocalFileSystemAdapter()
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    fs.ensure_dir(src_dir)
    fs.ensure_dir(dst_dir)

    f1 = src_dir / "a.tif"
    f2 = src_dir / "b.jpg"
    f1.write_bytes(b"x")
    f2.write_bytes(b"y")

    files = fs.list_files(src_dir, ["*.tif"])
    assert f1 in files and f2 not in files

    dst_file = dst_dir / "copied.tif"
    fs.copy(f1, dst_file)
    assert dst_file.exists()

    moved = dst_dir / "moved.tif"
    fs.move(dst_file, moved)
    assert moved.exists() and not dst_file.exists()



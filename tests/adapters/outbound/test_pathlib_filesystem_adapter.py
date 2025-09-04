from pathlib import Path
from percell.adapters.outbound.pathlib_filesystem_adapter import PathlibFilesystemAdapter


def test_dir_lifecycle_and_listing(tmp_path: Path):
    fs = PathlibFilesystemAdapter()
    root = tmp_path / 'root'
    fs.ensure_dir(root)
    assert fs.exists(root)

    # create files and dirs
    (root / 'a.txt').write_text('a')
    fs.ensure_dir(root / 'sub')
    (root / 'sub' / 'b.txt').write_text('b')

    files = fs.list_files(root, pattern='*.txt')
    assert set(p.name for p in files) == {'a.txt'}

    dirs = fs.list_dirs(root)
    assert set(p.name for p in dirs) == {'sub'}

    # glob from root
    g = fs.glob('**/*.txt', root=root)
    names = set(p.name for p in g)
    assert names == {'a.txt', 'b.txt'}

    # remove a file
    fs.remove_file(root / 'a.txt')
    assert not (root / 'a.txt').exists()

    # remove dir recursively
    fs.remove_dir(root, recursive=True)
    assert not root.exists()

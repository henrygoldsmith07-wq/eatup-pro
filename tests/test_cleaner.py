import os
import time
from pathlib import Path, PureWindowsPath

import pytest

import cleaner
from cleaner import EatUpCleaner, drive_root


@pytest.mark.parametrize("path, expected", [
    (r"C:\Users\bob\AppData\Local\Temp\x.dat", "Temporary"),
    (r"C:\Windows\Temp\setup.log", "Temporary"),
    (r"C:\Temp\stuff.bin", "Temporary"),
    (r"C:\Users\bob\Documents\report.tmp", "Temporary"),
    (r"C:\Users\bob\Documents\~$report.docx", "Temporary"),
    # Substring look-alikes must not be treated as temp
    (r"C:\Users\bob\Documents\Templates\letter.docx", "Documents"),
    (r"C:\Users\Tempest\Music\song.mp3", "Music"),
    (r"C:\dev\app\node_modules\tmp\lib\tmp.js", "Other"),
    (r"C:\Users\bob\Documents\backup.bak", "Other"),
    (r"C:\Windows\System32\kernel32.dll", "System"),
    (r"C:\Windows\System32\stray.tmp", "System"),
    (r"C:\Program Files\App\app.exe", "System"),
    (r"C:\$Recycle.Bin\S-1-5\$R123.tmp", "System"),
    (r"C:\Users\bob\Downloads\movie.mp4", "Downloads"),
    (r"C:\Users\bob\Videos\clip.mkv", "Videos"),
])
def test_classify_file(path, expected):
    assert EatUpCleaner._classify_file(PureWindowsPath(path)) == expected


def test_drive_root():
    assert drive_root("C:") == "C:" + os.sep
    assert drive_root("/data") == "/data"


@pytest.fixture
def tree(tmp_path, monkeypatch):
    # pytest's tmp_path lives under /tmp, which the scanner treats as a root temp dir
    monkeypatch.setattr(cleaner, "ROOT_TEMP_DIRS", set())
    monkeypatch.setattr(cleaner, "DUPLICATE_MIN_BYTES", 1)
    old = time.time() - 3 * 86400

    def make(rel, content, mtime=old):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        os.utime(p, (mtime, mtime))
        return p

    make("docs/a.txt", b"same content")
    make("docs/copy/a.txt", b"same content", mtime=time.time())
    make("docs/b.txt", b"diff content")  # Same size, different content
    make("work/old.tmp", b"x" * 10)
    make("work/fresh.tmp", b"y" * 10, mtime=time.time())
    return tmp_path


def test_scan_finds_only_aged_temp_files(tree):
    c = EatUpCleaner()
    result = c.scan_drive(str(tree))
    assert [f.name for f in result.temp_files] == ["old.tmp"]
    assert result.files_scanned == 5
    assert result.cleanable_size == 10
    assert sum(result.categories.values()) == 3 * 12 + 2 * 10


def test_find_duplicates_keeps_oldest_first(tree):
    c = EatUpCleaner()
    c.scan_drive(str(tree))
    groups = c.find_duplicates()
    assert len(groups) == 1
    assert [Path(f.path).relative_to(tree).as_posix() for f in groups[0]] == ["docs/a.txt", "docs/copy/a.txt"]
    assert c.duplicate_bytes() == 12


def test_unreadable_files_are_not_grouped(tree, monkeypatch):
    monkeypatch.setattr(EatUpCleaner, "_compute_file_hash", staticmethod(lambda *a: None))
    c = EatUpCleaner()
    c.scan_drive(str(tree))
    assert c.find_duplicates() == []


def test_cleanup_recycles_and_never_removes_last_copy(tree, monkeypatch):
    recycled = []

    def fake_recycle(path):
        recycled.append(Path(path).relative_to(tree).as_posix())
        os.remove(path)

    monkeypatch.setattr(cleaner, "move_to_recycle_bin", fake_recycle)
    c = EatUpCleaner()
    c.scan_drive(str(tree))
    c.find_duplicates()

    preview = c.smart_cleanup(dry_run=True)
    assert (preview.files_deleted, preview.freed_bytes) == (2, 22)
    assert recycled == []

    result = c.smart_cleanup()
    assert sorted(recycled) == ["docs/copy/a.txt", "work/old.tmp"]
    assert (result.files_deleted, result.freed_bytes, result.errors) == (2, 22, [])
    assert (tree / "docs/a.txt").exists()
    assert c.scan_results.temp_files == [] and c.scan_results.duplicates == []

    # Repeating the cleanup must not report phantom savings
    assert c.smart_cleanup().files_deleted == 0


def test_cleanup_skips_files_modified_since_scan(tree, monkeypatch):
    monkeypatch.setattr(cleaner, "move_to_recycle_bin", lambda p: pytest.fail("should not delete"))
    c = EatUpCleaner()
    c.scan_drive(str(tree))
    (tree / "work/old.tmp").write_bytes(b"now in use, bigger")
    assert c.cleanup_temp_files().files_deleted == 0


def test_delete_errors_are_reported(tree, monkeypatch):
    def boom(path):
        raise PermissionError("locked")

    monkeypatch.setattr(cleaner, "move_to_recycle_bin", boom)
    c = EatUpCleaner()
    c.scan_drive(str(tree))
    result = c.cleanup_temp_files()
    assert result.files_deleted == 0 and len(result.errors) == 1

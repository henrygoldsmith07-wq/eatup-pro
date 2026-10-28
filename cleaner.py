#!/usr/bin/env python3
"""
EatUp Pro - Disk Cleanup Tool
A modern, safe disk space analyzer and cleaner for Windows
"""

import os
import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Iterable, Optional
from dataclasses import dataclass, field
import psutil  # System monitoring

try:
    import winshell  # Windows Recycle Bin integration
except ImportError:  # Non-Windows: scanning works, deletion is unavailable
    winshell = None


GB = 1024 ** 3
LARGE_FILE_BYTES = GB
DUPLICATE_MIN_BYTES = 1024 ** 2
TEMP_MIN_AGE_DAYS = 1  # Leave files a running program may still be writing

CATEGORIES = ('Applications', 'Videos', 'Documents', 'Images', 'Music',
              'Downloads', 'System', 'Temporary', 'Other')

VIDEO_EXTS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.m4v'}
DOC_EXTS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.rtf', '.txt'}
IMG_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.raw'}
MUSIC_EXTS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'}
APP_EXTS = {'.exe', '.msi', '.dll', '.sys', '.drv'}

# Directory names are matched against whole path components (lowercased),
# never as substrings: "Temp" must not match "Templates" or "Contemporary".
SYSTEM_DIRS = {'windows', 'program files', 'program files (x86)', 'programdata',
               'system volume information', '$windows.~bt', '$windows.~ws'}
TRASH_DIRS = {'$recycle.bin'}
DOWNLOAD_DIRS = {'downloads'}
# Known temp locations as consecutive path components: anything named "tmp"
# deeper in the tree (e.g. node_modules/tmp) may belong to an application.
TEMP_LOCATIONS = (('appdata', 'local', 'temp'), ('windows', 'temp'))
ROOT_TEMP_DIRS = {'temp', 'tmp'}
TEMP_SUFFIXES = {'.tmp', '.temp', '.crdownload', '.part'}
TEMP_PREFIXES = ('~$',)  # Office owner/lock files


@dataclass
class FileInfo:
    """File information structure"""
    path: str
    size: int
    name: str
    category: str
    age_days: int = 0
    is_duplicate: bool = False


@dataclass
class ScanResult:
    """Scan result container"""
    total_used: int
    total_space: int
    categories: Dict[str, int]
    large_files: List[FileInfo]
    duplicates: List[List[FileInfo]]
    temp_files: List[FileInfo]
    cleanable_size: int
    drive: str = 'C:'
    files_scanned: int = 0


@dataclass
class CleanupResult:
    """Outcome of a cleanup operation"""
    freed_bytes: int = 0
    files_deleted: int = 0
    errors: List[str] = field(default_factory=list)

    def merge(self, other: 'CleanupResult') -> 'CleanupResult':
        self.freed_bytes += other.freed_bytes
        self.files_deleted += other.files_deleted
        self.errors.extend(other.errors)
        return self


def drive_root(drive: str) -> str:
    """'C:' means the current directory on C: to Windows; scan its root instead."""
    if len(drive) == 2 and drive[1] == ':':
        return drive + os.sep
    return drive


def move_to_recycle_bin(path: str):
    if winshell is None:
        raise RuntimeError("Recycle Bin support requires winshell (Windows only)")
    # The app shows its own confirmation, so suppress per-file shell dialogs
    winshell.delete_file(path, allow_undo=True, no_confirm=True, silent=True)


class EatUpCleaner:
    """Main disk cleanup engine"""

    def __init__(self):
        self.scan_results: Optional[ScanResult] = None
        self.files_scanned = 0  # Live progress counter for the API

    def scan_drive(self, drive: str = "C:", max_depth: int = 5) -> ScanResult:
        """Scan specified drive for storage analysis"""
        print(f"🔍 Scanning {drive} drive...")

        root_dir = drive_root(drive)
        usage = shutil.disk_usage(root_dir)
        categories = {name: 0 for name in CATEGORIES}
        large_files = []
        temp_files = []
        now = datetime.now().timestamp()
        self.files_scanned = 0

        for root, dirs, files in self._walk(root_dir, max_depth):
            for filename in files:
                filepath = Path(root) / filename
                try:
                    file_stat = filepath.stat()
                except OSError:
                    continue  # Skip inaccessible files

                file_size = file_stat.st_size
                age_days = int((now - file_stat.st_mtime) / 86400)
                category = self._classify_file(filepath)
                categories[category] += file_size

                if file_size >= LARGE_FILE_BYTES:
                    large_files.append(FileInfo(str(filepath), file_size, filename, category, age_days))

                if category == 'Temporary' and age_days >= TEMP_MIN_AGE_DAYS:
                    temp_files.append(FileInfo(str(filepath), file_size, filename, 'Temporary', age_days))

                self.files_scanned += 1
                if self.files_scanned % 1000 == 0:
                    print(f"⏳ Scanned {self.files_scanned} files...", end='\r')

        large_files.sort(key=lambda f: f.size, reverse=True)
        temp_files.sort(key=lambda f: f.size, reverse=True)
        retained_large_files = large_files[:100]
        retained_temp_files = temp_files[:500]

        self.scan_results = ScanResult(
            total_used=usage.used,
            total_space=usage.total,
            categories=categories,
            large_files=retained_large_files,  # Keep the 100 largest
            duplicates=[],  # Filled by find_duplicates()
            temp_files=retained_temp_files,  # Keep the 500 largest
            cleanable_size=sum(f.size for f in retained_temp_files),
            drive=drive,
            files_scanned=self.files_scanned
        )

        print(f"\n✅ Scan complete! Found {self.files_scanned} files")
        return self.scan_results

    @staticmethod
    def _walk(root_dir: str, max_depth: int, skip_dirs: Iterable[str] = ()):
        """os.walk limited to max_depth levels below root_dir, pruning skip_dirs"""
        skip = set(skip_dirs)
        for root, dirs, files in os.walk(root_dir, topdown=True):
            rel = os.path.relpath(root, root_dir)
            depth = 0 if rel == '.' else rel.count(os.sep) + 1
            if depth >= max_depth:
                dirs.clear()
            elif skip:
                dirs[:] = [d for d in dirs if d.lower() not in skip]
            yield root, dirs, files

    @staticmethod
    def _classify_file(filepath: Path) -> str:
        """Classify file into category based on extension and path"""
        parts = [p.lower() for p in filepath.parts[:-1]]
        if EatUpCleaner._is_temp_file(filepath, parts):
            return 'Temporary'
        if set(parts) & (SYSTEM_DIRS | TRASH_DIRS):
            return 'System'
        if set(parts) & DOWNLOAD_DIRS:
            return 'Downloads'
        
        ext = filepath.suffix.lower()
        if ext in VIDEO_EXTS:
            return 'Videos'
        if ext in DOC_EXTS:
            return 'Documents'
        if ext in IMG_EXTS:
            return 'Images'
        if ext in MUSIC_EXTS:
            return 'Music'
        if ext in APP_EXTS:
            return 'Applications'
        return 'Other'
    
    @staticmethod
    def _is_temp_file(filepath: Path, parts: Optional[List[str]] = None) -> bool:
        """Identify temporary files that are safe to recycle"""
        if parts is None:
            parts = [p.lower() for p in filepath.parts[:-1]]
        if set(parts) & TRASH_DIRS:
            return False  # Already in the Recycle Bin
        if len(parts) > 1 and parts[1] in ROOT_TEMP_DIRS:
            return True  # e.g. C:\Temp
        for location in TEMP_LOCATIONS:
            n = len(location)
            if any(tuple(parts[i:i + n]) == location for i in range(len(parts) - n + 1)):
                return True
        if set(parts) & SYSTEM_DIRS:
            return False  # Stray .tmp files under system dirs may be in use
        name = filepath.name.lower()
        return filepath.suffix.lower() in TEMP_SUFFIXES or name.startswith(TEMP_PREFIXES)
    
    def find_duplicates(self, chunk_size: int = 65536, max_depth: int = 5) -> List[List[FileInfo]]:
        """Find duplicate files (>= 1 MB, outside system dirs) by content hash"""
        print("🔎 Finding duplicate files...")

        if not self.scan_results:
            self.scan_drive()

        root_dir = drive_root(self.scan_results.drive)
        now = datetime.now().timestamp()

        # Only files of identical size can be duplicates, so group by size first
        size_groups: Dict[int, List[FileInfo]] = {}
        for root, dirs, files in self._walk(root_dir, max_depth, SYSTEM_DIRS | TRASH_DIRS):
            for filename in files:
                filepath = Path(root) / filename
                try:
                    file_stat = filepath.stat()
                except OSError:
                    continue
                if file_stat.st_size < DUPLICATE_MIN_BYTES:
                    continue
                size_groups.setdefault(file_stat.st_size, []).append(FileInfo(
                    path=str(filepath),
                    size=file_stat.st_size,
                    name=filename,
                    category=self._classify_file(filepath),
                    age_days=int((now - file_stat.st_mtime) / 86400)
                ))

        duplicates = []
        hashes_computed = 0
        for files in size_groups.values():
            if len(files) < 2:
                continue

            hash_groups: Dict[str, List[FileInfo]] = {}
            for file_info in files:
                hash_value = self._compute_file_hash(file_info.path, chunk_size)
                if hash_value is None:
                    continue  # Unreadable files must never be grouped together
                hashes_computed += 1
                hash_groups.setdefault(hash_value, []).append(file_info)

            for dup_files in hash_groups.values():
                if len(dup_files) >= 2:
                    # Oldest copy first: it is the one cleanup keeps
                    dup_files.sort(key=lambda f: f.age_days, reverse=True)
                    for f in dup_files[1:]:
                        f.is_duplicate = True
                    duplicates.append(dup_files)

        self.scan_results.duplicates = duplicates
        self.scan_results.cleanable_size = (
            sum(f.size for f in self.scan_results.temp_files) + self.duplicate_bytes()
        )

        print(f"✅ Found {len(duplicates)} duplicate groups ({hashes_computed} hashes computed)")
        return duplicates

    def duplicate_bytes(self) -> int:
        """Bytes reclaimable by keeping one copy of each duplicate group"""
        if not self.scan_results:
            return 0
        return sum(f.size for group in self.scan_results.duplicates for f in group[1:])

    @staticmethod
    def _compute_file_hash(filepath: str, chunk_size: int = 65536) -> Optional[str]:
        """Compute MD5 hash of a file (fast for duplicate detection), None if unreadable"""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except OSError:
            return None

    def get_temp_files_list(self, limit: int = 100) -> List[FileInfo]:
        """Get list of temporary files"""
        if not self.scan_results:
            return []
        return self.scan_results.temp_files[:limit]

    @staticmethod
    def _recycle_files(files: List[FileInfo], dry_run: bool) -> CleanupResult:
        """Move files to the Recycle Bin, skipping any that changed since the scan"""
        result = CleanupResult()
        for file_info in files:
            if not dry_run:
                try:
                    if os.path.getsize(file_info.path) != file_info.size:
                        continue  # Modified since scan: no longer the file we vetted
                    move_to_recycle_bin(file_info.path)
                except FileNotFoundError:
                    continue
                except Exception as e:
                    result.errors.append(f"{file_info.path}: {e}")
                    print(f"  ⚠️  Could not delete {file_info.path}: {e}")
                    continue
                print(f"  📦 Moved to Recycle Bin: {file_info.name}")
            result.freed_bytes += file_info.size
            result.files_deleted += 1
        return result

    @staticmethod
    def _remaining(files: List[FileInfo]) -> List[FileInfo]:
        return [f for f in files if os.path.exists(f.path)]

    def _recompute_cleanable_size(self) -> None:
        """Drop cleaned files from the reported reclaimable space"""
        self.scan_results.cleanable_size = (
            sum(f.size for f in self.scan_results.temp_files) + self.duplicate_bytes()
        )

    def cleanup_temp_files(self, dry_run: bool = False) -> CleanupResult:
        """Move scanned temporary files to the Recycle Bin"""
        print("🗑️ Cleaning temporary files...")
        if not self.scan_results:
            return CleanupResult()

        result = self._recycle_files(self.scan_results.temp_files, dry_run)
        if not dry_run:
            self.scan_results.temp_files = self._remaining(self.scan_results.temp_files)
            self._recompute_cleanable_size()

        print(f"✅ Freed {result.freed_bytes / GB:.2f} GB ({result.files_deleted} files)")
        return result

    def cleanup_duplicates(self, dry_run: bool = False) -> CleanupResult:
        """Remove all but the oldest copy in each duplicate group"""
        print("🔄 Removing duplicate files...")
        result = CleanupResult()

        if not self.scan_results or not self.scan_results.duplicates:
            print("No duplicates found")
            return result

        for dup_group in self.scan_results.duplicates:
            keeper = dup_group[0]
            if not dry_run and not os.path.exists(keeper.path):
                continue  # Never remove the last surviving copy
            result.merge(self._recycle_files(dup_group[1:], dry_run))

        if not dry_run:
            self.scan_results.duplicates = [
                group for group in (self._remaining(g) for g in self.scan_results.duplicates)
                if len(group) > 1
            ]
            self._recompute_cleanable_size()

        print(f"✅ Freed {result.freed_bytes / GB:.2f} GB ({result.files_deleted} files)")
        return result

    def cleanup_large_files(self, min_size_gb: float = 1, dry_run: bool = False) -> CleanupResult:
        """Remove files larger than specified size"""
        print(f"💾 Removing files larger than {min_size_gb} GB...")
        if not self.scan_results:
            return CleanupResult()

        targets = [f for f in self.scan_results.large_files if f.size >= min_size_gb * GB]
        result = self._recycle_files(targets, dry_run)
        if not dry_run:
            self.scan_results.large_files = self._remaining(self.scan_results.large_files)

        print(f"✅ Freed {result.freed_bytes / GB:.2f} GB ({result.files_deleted} files)")
        return result

    def smart_cleanup(self, dry_run: bool = False) -> CleanupResult:
        """Perform intelligent cleanup with highest priority items first"""
        print("⚡ Performing Smart Cleanup...")

        # Priority 1: Temporary files (safest), Priority 2: Duplicates (high impact)
        result = self.cleanup_temp_files(dry_run)
        result.merge(self.cleanup_duplicates(dry_run))

        print(f"🎯 Total Freed: {result.freed_bytes / GB:.2f} GB")
        return result

    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage(os.path.abspath(os.sep)).percent,
            'uptime': psutil.boot_time(),
            'timestamp': datetime.now().isoformat()
        }

    def build_report(self) -> Optional[Dict[str, Any]]:
        """Summarize scan results as a JSON-serializable dict"""
        if not self.scan_results:
            return None
        results = self.scan_results
        return {
            'scan_date': datetime.now().isoformat(),
            'drive': results.drive,
            'total_used_gb': results.total_used / GB,
            'total_space_gb': results.total_space / GB,
            'utilization_percent': (results.total_used / results.total_space * 100) if results.total_space else 0,
            'categories': {k: v / GB for k, v in results.categories.items()},
            'files_scanned': results.files_scanned,
            'large_files_count': len(results.large_files),
            'duplicate_groups': len(results.duplicates),
            'temp_files_count': len(results.temp_files),
            'cleanable_gb': results.cleanable_size / GB,
            'system_stats': self.get_system_stats()
        }

    def export_report(self, filename: str = None) -> Optional[str]:
        """Export scan results to a JSON report file, returning its path"""
        report = self.build_report()
        if report is None:
            print("❌ No scan results available")
            return None

        if filename is None:
            filename = f"eatup_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"📊 Report saved to {filename}")
        return filename


def _confirm_cleanup(preview: CleanupResult, files: List[FileInfo] = ()) -> bool:
    """Show what a cleanup would remove and ask before doing it"""
    if preview.files_deleted == 0:
        print("Nothing to clean up.")
        return False
    for f in files:
        print(f"  • {f.path} ({f.size / GB:.2f} GB)")
    answer = input(f"\nMove {preview.files_deleted} files ({preview.freed_bytes / GB:.2f} GB) "
                   f"to the Recycle Bin? [y/N]: ").strip().lower()
    return answer == 'y'


def main():
    """Main CLI interface"""
    print("=" * 60)
    print("   EATUP PRO - Disk Cleanup Tool")
    print("=" * 60)
    print()

    cleaner = EatUpCleaner()

    while True:
        print("\nMenu:")
        print("1. Scan Drive")
        print("2. Find Duplicates")
        print("3. Cleanup Temp Files")
        print("4. Cleanup Large Files")
        print("5. Smart Cleanup (All)")
        print("6. Export Report")
        print("7. Exit")

        choice = input("\nEnter choice (1-7): ").strip()

        if choice in ('3', '4', '5') and not cleaner.scan_results:
            print("Run a scan first (option 1)")
            continue

        if choice == '1':
            cleaner.scan_drive()
        elif choice == '2':
            cleaner.find_duplicates()
        elif choice == '3':
            if _confirm_cleanup(cleaner.cleanup_temp_files(dry_run=True)):
                cleaner.cleanup_temp_files()
        elif choice == '4':
            large = cleaner.scan_results.large_files
            if _confirm_cleanup(cleaner.cleanup_large_files(min_size_gb=1, dry_run=True), large):
                cleaner.cleanup_large_files(min_size_gb=1)
        elif choice == '5':
            if _confirm_cleanup(cleaner.smart_cleanup(dry_run=True)):
                cleaner.smart_cleanup()
        elif choice == '6':
            cleaner.export_report()
        elif choice == '7':
            print("Goodbye!")
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()

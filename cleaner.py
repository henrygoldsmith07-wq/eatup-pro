#!/usr/bin/env python3
"""
EatUp Pro - Disk Cleanup Tool
A modern, safe disk space analyzer and cleaner for Windows
"""

import os
import sys
import json
import shutil
import hashlib
import math
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Set
from dataclasses import dataclass, asdict
import winshell  # Windows Recycle Bin integration
import psutil  # System monitoring

# Plugin imports
try:
    from plugins.plugin_manager import PluginManager
    PLUGINS_ENABLED = True
except ImportError:
    PLUGINS_ENABLED = False


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


class EatUpCleaner:
    """Main disk cleanup engine"""
    
    def __init__(self):
        self.scan_results: ScanResult = None
        self.files_to_cleanup: List[FileInfo] = []
        self.plugin_manager = PluginManager() if PLUGINS_ENABLED else None
        
        # Store custom paths from plugins
        self.custom_paths = []
        
    def load_plugins(self):
        """Load all available plugins"""
        if PLUGINS_ENABLED:
            self.plugin_manager.load_plugins_from_directory('plugins')
            print(f"✅ Loaded {len(self.plugin_manager.get_loaded_plugins())} plugins")
        
    def _scan_with_plugins(self, drive: str):
        """Run plugins during scan"""
        if not self.plugin_manager or not PLUGINS_ENABLED:
            return
        
        print("🔌 Running plugins...")
        
        # Call customize_scan on all loaded plugins
        for plugin in self.plugin_manager.get_loaded_plugins():
            try:
                detected_paths = plugin.customize_scan(self)
                if detected_paths:
                    print(f"  ✅ {plugin.name}: Found {len(detected_paths)} custom paths")
            except Exception as e:
                print(f"  ⚠️  {plugin.name} error: {e}")
    
    def scan_drive(self, drive: str = "C:", use_plugins: bool = True) -> ScanResult:
        """Scan specified drive for storage analysis"""
        print(f"🔍 Scanning {drive} drive...")
        
        # Load and run plugins first
        if use_plugins and self.plugin_manager:
            self._scan_with_plugins(drive)
        
        # Continue with main scan logic
        drive_path = Path(drive)
        total_space = drive_path.total_space
        free_space = drive_path.free_space
        total_used = total_space - free_space
        
        # Initialize counters
        categories = {
            'Applications': 0,
            'Videos': 0,
            'Documents': 0,
            'Images': 0,
            'Music': 0,
            'Downloads': 0,
            'System': 0,
            'Other': 0
        }
        
        large_files = []
        temp_files = []
        
        # File extensions by category
        video_exts = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'}
        doc_exts = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt'}
        img_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'}
        music_exts = {'.mp3', '.wav', '.flac', '.aac', '.ogg'}
        download_exts = {'.iso', '.img', '.dmg', '.exe'}
        
        # Traverse directory (limit depth for performance)
        max_depth = 5
        items_scanned = 0
        
        try:
            for root, dirs, files in os.walk(drive, topdown=True):
                # Limit recursion depth
                if root.count(os.sep) - drive.count(os.sep) > max_depth:
                    dirs.clear()
                    continue
                
                for filename in files:
                    try:
                        filepath = Path(root) / filename
                        file_stat = filepath.stat()
                        file_size = file_stat.st_size
                        
                        # Determine category
                        ext = Path(filename).suffix.lower()
                        category = self._classify_file(ext, filepath, filename)
                        categories[category] += file_size
                        
                        # Find large files (>1GB)
                        if file_size > 1_000_000_000:  # 1 GB
                            age_days = (datetime.now().timestamp() - file_stat.st_mtime) / 86400
                            large_files.append(FileInfo(
                                path=str(filepath),
                                size=file_size,
                                name=filename,
                                category=category,
                                age_days=int(age_days)
                            ))
                        
                        # Find temp files
                        if self._is_temp_file(filename, filepath):
                            temp_files.append(FileInfo(
                                path=str(filepath),
                                size=file_size,
                                name=filename,
                                category='Temporary'
                            ))
                        
                        items_scanned += 1
                        
                    except (OSError, PermissionError):
                        pass  # Skip inaccessible files
                    
                    # Progress indicator every 1000 files
                    if items_scanned % 1000 == 0:
                        print(f"⏳ Scanned {items_scanned} files...", end='\r')
                        
        except Exception as e:
            print(f"\n❌ Error scanning drive: {e}")
            raise
        
        # Calculate cleanable space
        cleanable_size = sum(f.size for f in temp_files) + (total_used * 0.1)  # Estimate 10% from other categories
        
        self.scan_results = ScanResult(
            total_used=total_used,
            total_space=total_space,
            categories=categories,
            large_files=large_files[:100],  # Limit to top 100
            duplicates=[],  # Will be filled separately
            temp_files=temp_files[:500],  # Limit to top 500
            cleanable_size=cleanable_size
        )
        
        print(f"\n✅ Scan complete! Found {items_scanned} files")
        return self.scan_results
    
    def _classify_file(self, ext: str, filepath: Path, filename: str) -> str:
        """Classify file into category based on extension and path"""
        video_exts = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.m4v'}
        doc_exts = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.rtf'}
        img_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.raw'}
        music_exts = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'}
        app_exts = {'.exe', '.msi', '.dll', '.sys', '.drv'}
        system_paths = {'$WINDOWS.~BT', '$Windows.~WS', 'Windows', 'System32', 'Program Files'}
        download_paths = {'download', 'downloads'}
        temp_paths = {'temp', 'tmp', '$Recycle.Bin'}
        
        # Check paths first
        path_str = str(filepath).lower()
        if any(p in path_str for p in system_paths):
            return 'System'
        if any(p in path_str for p in download_paths):
            return 'Downloads'
        if any(p in path_str for p in temp_paths):
            return 'Temporary'
        
        # Check extensions
        if ext in video_exts:
            return 'Videos'
        if ext in doc_exts:
            return 'Documents'
        if ext in img_exts:
            return 'Images'
        if ext in music_exts:
            return 'Music'
        if ext in app_exts:
            return 'Applications'
        
        return 'Other'
    
    def _is_temp_file(self, filename: str, filepath: Path) -> bool:
        """Identify temporary files"""
        temp_patterns = [
            '.tmp', '.temp', '.cache', '~$', '.swp', '.bak',
            '.log', '.crdownload', '.part'
        ]
        
        path_str = str(filepath).lower()
        
        # Check patterns
        for pattern in temp_patterns:
            if pattern in filename.lower() or pattern in path_str:
                return True
        
        # Check temp directories
        temp_dirs = ['temp', 'tmp', 'cache', '$recycle.bin']
        return any(d in path_str for d in temp_dirs)
    
    def find_duplicates(self, chunk_size: int = 65536) -> List[List[FileInfo]]:
        """Find duplicate files based on content hash (MD5 for speed)"""
        print("🔎 Finding duplicate files...")
        
        if not self.scan_results:
            self.scan_drive()
        
        # Group files by size first (only files with same size can be duplicates)
        size_groups: Dict[int, List[FileInfo]] = {}
        
        for category, size in self.scan_results.categories.items():
            pass  # Skip this loop, using temp_files and large_files instead
        
        # Process temp files and large files for duplicates
        all_potential_files = self.scan_results.temp_files + self.scan_results.large_files
        
        # Also scan for duplicates in other categories
        try:
            drive_path = Path("C:")
            total_space = drive_path.total_space
            free_space = drive_path.free_space
            
            for root, dirs, files in os.walk("C:", topdown=True):
                if root.count(os.sep) - 1 > 4:  # Limit depth
                    dirs.clear()
                    continue
                
                for filename in files:
                    try:
                        filepath = Path(root) / filename
                        file_stat = filepath.stat()
                        file_size = file_stat.st_size
                        
                        # Only check files > 1MB to avoid scanning too many small files
                        if file_size < 1_000_000:
                            continue
                        
                        ext = Path(filename).suffix.lower()
                        category = self._classify_file(ext, filepath, filename)
                        
                        # Skip system/critical directories
                        path_str = str(filepath).lower()
                        if any(p in path_str for p in ['windows', 'program files', 'system32']):
                            continue
                        
                        if file_size not in size_groups:
                            size_groups[file_size] = []
                        
                        size_groups[file_size].append(FileInfo(
                            path=str(filepath),
                            size=file_size,
                            name=filename,
                            category=category,
                            age_days=int((datetime.now().timestamp() - file_stat.st_mtime) / 86400)
                        ))
                    except (OSError, PermissionError):
                        pass
        except Exception as e:
            print(f"⚠️  Limited duplicate scanning due to: {e}")
        
        # Now compute hashes only for files that share sizes
        duplicates = []
        files_processed = 0
        hash_computed = 0
        
        for size, files in size_groups.items():
            if len(files) < 2:
                continue
            
            # Group by hash
            hash_groups: Dict[str, List[FileInfo]] = {}
            
            for file_info in files:
                try:
                    hash_value = self._compute_file_hash(file_info.path, chunk_size)
                    hash_computed += 1
                    
                    if hash_value not in hash_groups:
                        hash_groups[hash_value] = []
                    hash_groups[hash_value].append(file_info)
                    
                except (OSError, PermissionError):
                    files_processed += 1
                    continue
            
            # Add groups with duplicates
            for hash_value, dup_files in hash_groups.items():
                if len(dup_files) >= 2:
                    duplicates.append(dup_files)
                    files_processed += len(dup_files)
        
        self.scan_results.duplicates = duplicates
        
        print(f"✅ Found {len(duplicates)} duplicate groups from {files_processed} files ({hash_computed} hashes computed)")
        return duplicates
    
    def _compute_file_hash(self, filepath: str, chunk_size: int = 65536) -> str:
        """Compute MD5 hash of a file (fast for duplicate detection)"""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (OSError, PermissionError):
            return ""
    
    def get_temp_files_list(self, limit: int = 100) -> List[FileInfo]:
        """Get list of temporary files"""
        if not self.scan_results:
            return []
        return self.scan_results.temp_files[:limit]
    
    def cleanup_temp_files(self, dry_run: bool = False) -> int:
        """Cleanup temporary files"""
        print("🗑️ Cleaning temporary files...")
        
        freed_space = 0
        files_deleted = 0
        
        temp_files = self.get_temp_files_list()
        
        for file_info in temp_files:
            try:
                if not dry_run:
                    # Move to Recycle Bin for safety
                    if os.path.exists(file_info.path):
                        winshell.delete(file_info.path, true_delete=False)
                        freed_space += file_info.size
                        files_deleted += 1
                        print(f"  📦 Moved to Recycle Bin: {file_info.name}")
                else:
                    freed_space += file_info.size
                    files_deleted += 1
                    
            except Exception as e:
                print(f"  ⚠️  Could not delete {file_info.path}: {e}")
        
        print(f"✅ Freed {freed_space / (1024*1024*1024):.2f} GB ({files_deleted} files)")
        return freed_space
    
    def cleanup_duplicates(self, dry_run: bool = False) -> int:
        """Remove duplicate files"""
        print("🔄 Removing duplicate files...")
        
        if not self.scan_results or not self.scan_results.duplicates:
            print("No duplicates found")
            return 0
        
        freed_space = 0
        
        for dup_group in self.scan_results.duplicates:
            if len(dup_group) > 1:
                # Keep first file, remove rest
                for file_info in dup_group[1:]:
                    try:
                        if not dry_run:
                            if os.path.exists(file_info.path):
                                winshell.delete(file_info.path, true_delete=False)
                                freed_space += file_info.size
                        else:
                            freed_space += file_info.size
                        print(f"  🗑️ Removed duplicate: {file_info.name}")
                    except Exception as e:
                        print(f"  ⚠️  Error: {e}")
        
        print(f"✅ Freed {freed_space / (1024*1024*1024):.2f} GB")
        return freed_space
    
    def cleanup_large_files(self, min_size_gb: float = 1, dry_run: bool = False) -> int:
        """Remove files larger than specified size"""
        print(f"💾 Removing files larger than {min_size_gb} GB...")
        
        if not self.scan_results:
            return 0
        
        min_size = min_size_gb * 1024 * 1024 * 1024
        freed_space = 0
        
        for file_info in self.scan_results.large_files:
            if file_info.size >= min_size:
                try:
                    if not dry_run:
                        if os.path.exists(file_info.path):
                            winshell.delete(file_info.path, true_delete=False)
                            freed_space += file_info.size
                    else:
                        freed_space += file_info.size
                    print(f"  🗑️ Large file: {file_info.name} ({file_info.size / (1024*1024*1024):.1f} GB)")
                except Exception as e:
                    print(f"  ⚠️  Error: {e}")
        
        print(f"✅ Freed {freed_space / (1024*1024*1024):.2f} GB")
        return freed_space
    
    def smart_cleanup(self, dry_run: bool = False) -> int:
        """Perform intelligent cleanup with highest priority items first"""
        print("⚡ Performing Smart Cleanup...")
        
        total_freed = 0
        
        # Priority 1: Temporary files (safest)
        total_freed += self.cleanup_temp_files(dry_run)
        
        # Priority 2: Duplicates (high impact)
        total_freed += self.cleanup_duplicates(dry_run)
        
        # Priority 3: Old downloads
        # Priority 4: Large old files
        
        print(f"🎯 Total Freed: {total_freed / (1024*1024*1024):.2f} GB")
        return total_freed
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'uptime': psutil.boot_time(),
            'timestamp': datetime.now().isoformat()
        }
    
    def export_report(self, filename: str = None):
        """Export scan results to JSON report"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"eatup_scan_{timestamp}.json"
        
        if not self.scan_results:
            print("❌ No scan results available")
            return
        
        report = {
            'scan_date': datetime.now().isoformat(),
            'drive': 'C:',
            'total_used_gb': self.scan_results.total_used / (1024**3),
            'total_space_gb': self.scan_results.total_space / (1024**3),
            'utilization_percent': (self.scan_results.total_used / self.scan_results.total_space) * 100,
            'categories': {k: v / (1024**3) for k, v in self.scan_results.categories.items()},
            'large_files_count': len(self.scan_results.large_files),
            'duplicate_groups': len(self.scan_results.duplicates),
            'temp_files_count': len(self.scan_results.temp_files),
            'cleanable_gb': self.scan_results.cleanable_size / (1024**3),
            'system_stats': self.get_system_stats()
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Report saved to {filename}")
        return report


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
        
        if choice == '1':
            cleaner.scan_drive()
        elif choice == '2':
            cleaner.find_duplicates()
        elif choice == '3':
            cleaned = cleaner.cleanup_temp_files()
            print(f"Freed: {cleaned / (1024*1024*1024):.2f} GB")
        elif choice == '4':
            cleaned = cleaner.cleanup_large_files(min_size_gb=1)
            print(f"Freed: {cleaned / (1024*1024*1024):.2f} GB")
        elif choice == '5':
            cleaned = cleaner.smart_cleanup()
            print(f"Total freed: {cleaned / (1024*1024*1024):.2f} GB")
        elif choice == '6':
            cleaner.export_report()
        elif choice == '7':
            print("Goodbye!")
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()

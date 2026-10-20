# EatUp Pro - Complete User Guide 📚

## Table of Contents
1. [Quick Start](#quick-start)
2. [Main Interface](#main-interface)
3. [Features Walkthrough](#features-walkthrough)
4. [Safety & Best Practices](#safety--best-practices)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Usage](#advanced-usage)

---

## Quick Start

### First Time Setup

1. **Double-click** `start.bat` to launch the tool
   - If it doesn't work, Python must be installed first
   
2. **Choose your interface**:
   - Option 1: Web GUI (recommended for most users)
   - Option 2: Command Line (for advanced users)

3. **Grant permissions** if prompted by Windows (scanner needs read access to drives)

### First Scan

1. Click "Scan Drive" button
2. Wait 30-60 seconds for initial scan
3. Review results automatically displayed

### Quick Cleanup

For instant space recovery:
1. Click "Smart Cleanup" (blue button)
2. Preview what will be deleted
3. Confirm deletion
4. Space is now free! (files in Recycle Bin)

---

## Main Interface

### Navigation Bar

```
[Logo] ── [Scan Drive] [Storage] [Cleanup] [Dark Mode Toggle]
```

- **Scan Drive**: Re-analyze disk usage
- **Storage**: View category breakdown
- **Cleanup**: Review and delete files
- **🌗 Icon**: Switch between light/dark themes

### Dashboard Layout

#### Top Section: Storage Overview
```
┌─────────────────────────────────────────┐
│  C: Drive Usage              [197 GB]   │
│  ┌───┬───┬───┬───┬───┬───┬───┬───┐    │
│   Blue Green Purple Orange Red...       │
│  └───┴───┴───┴───┴───┴───┴───┴───┘    │
└─────────────────────────────────────────┘
```

Each colored block = one category (clickable for details)

#### Left Panel: Category Bars
```
Applications    ████████████  45%
Videos          ████████      24%
Documents       ██████        18%
Images          ████           8%
Music           █              3%
Downloads       ██             1%
System          █              1%
Other           ▏              0%
```

#### Right Panel: Quick Actions

```
┌──────────────────┐  ┌──────────────────┐
│ 🗑️ Clear Temp    │  │ ⚡ Smart Cleanup │
│  Remove temp     │  │ Auto-cleanup     │
│  files           │  │ recommended      │
└──────────────────┘  └──────────────────┘
┌──────────────────┐  ┌──────────────────┐
│ 🔄 Find Dups     │  │ 💾 Large Files   │
│ Identify dups    │  │ Find >1GB files  │
└──────────────────┘  └──────────────────┘
```

### Status Indicators

- ✅ **Green** - Safe to clean
- ⚠️ **Yellow** - Review before cleaning
- ❌ **Red** - System file, protected

---

## Features Walkthrough

### Feature 1: Interactive Storage Map

**What it does**: Visual treemap showing disk usage

**How to use**:
1. Automatically appears after scanning
2. Hover over blocks to see category name
3. Resize shows/hides labels

**Categories explained**:
- **Apps**: Installed programs (protected)
- **Videos**: Media files (user control)
- **Documents**: Your documents (backup first!)
- **Images**: Photos (personal choice)
- **Downloads**: Downloaded files (review needed)
- **System**: Windows files (protected)
- **Temporary**: Cache/temp files (safe)

### Feature 2: Quick Clean Actions

#### Clear Temp Files
- Scans for `.tmp`, `.temp`, `.cache` files
- Removes browser caches
- Clears Windows update leftovers
- **Safe?**: Yes, always safe

#### Find Duplicates
- Hash-based duplicate detection
- Groups identical files
- Shows size of duplicates
- **Safe?**: Yes, keeps one copy

#### Large Files (>1GB)
- Lists biggest files on drive
- Shows file age
- Displays location
- **Safe?**: Review first!

#### Smart Cleanup
Automated selection based on:
1. Temporary files (priority 1)
2. Duplicate files (priority 2)
3. Old downloads (priority 3)

### Feature 3: File Browser

Click any cleanup category to browse files:

```
┌─────────────────────────────────────┐
│ ☐ Temporary Files        1,247 files│
│    Safe to remove • Goes to recycle │
├─────────────────────────────────────┤
│ 📁 folder_name                    245MB│
│ 📄 file1.tmp                      15MB │
│ 📄 cache_001.cache                89MB │
│ 📄 log_backup.log                 2MB  │
└─────────────────────────────────────┘
Selection: 1,247 files • 2.3 GB
```

**Actions**:
- ☑️ Click checkbox to select/deselect
- Use "Select All" / "Deselect All" buttons
- Preview before confirming

### Feature 4: Confirmation Dialog

Before deleting, you'll see:
```
┌──────────────────────────────────┐
│  Confirm Deletion                │
├──────────────────────────────────┤
│  These files will go to Recycle  │
│  Bin and can be restored.        │
│                                  │
│  Total: 12 files • 345 MB        │
│                                  │
│  [Cancel]        [Delete]        │
└──────────────────────────────────┘
```

**Important**: 
- ✅ Clicking "Delete" moves to Recycle Bin
- ❌ Nothing is permanently deleted yet
- ⏳ Empty Recycle Bin when sure to reclaim space

### Feature 5: Results Display

After cleanup completes:
```
         ✓
   SUCCESSFUL CLEANUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Space Freed: 12.4 GB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Files removed: 1,247
  Categories cleaned:
    • Temporary Files ✓
    • Duplicate Files ✓
  
  [Scan Again] [View Report]
```

---

## Safety & Best Practices

### 🛡️ Safety Features Explained

#### Recycle Bin Protection
- ALL deletions go to Recycle Bin first
- Files remain recoverable for 30+ days
- You can restore anytime from Recycle Bin
- Only empty Recycle Bin when absolutely certain

#### What's Protected?
The tool **AVOIDS** deleting:
- Windows system files
- Program files in Program Files/
- Your Documents folder content
- Database files
- Active application files

#### Dry Run Mode
Before actual deletion:
1. Enable dry run to preview changes
2. See exactly what WILL be deleted
3. Never lose important data unexpectedly

### Recommended Workflow

#### For New Users
1. **First time**: Run with dry run only
2. **Review**: Check each category carefully
3. **Start small**: Clean temporary files only
4. **Verify**: Ensure system works fine
5. **Expand**: Add more categories gradually

#### Monthly Maintenance
1. Scan once per month
2. Always clean temp files
3. Review old downloads
4. Check for new duplicates
5. Export report for records

#### Before Major Operations
1. Create system restore point
2. Backup important documents
3. Close all running applications
4. Connect power source (laptop)
5. Have admin rights

### When NOT to Clean

❌ **Don't clean**:
- Recent downloads you might need
- Personal media files (photos/videos)
- Work documents or projects
- Game installations you play
- Software installers you own
- Backups stored locally

✅ **Safe to clean**:
- Old temporary files
- Duplicate copies you made
- Obsolete installer files
- Browser caches
- Update leftovers
- System temp files

### Data Recovery Guide

If you accidentally deleted something:

1. **Immediate Action**:
   ```
   Open Recycle Bin → Find file → Right-click → Restore
   ```

2. **Restore Multiple Files**:
   - Select files in Recycle Bin
   - Right-click → "Restore all items"

3. **Full Restore**:
   - Empty Recycle Bin only when 100% sure

4. **Can't find in Recycle Bin?**
   - Tool may have already emptied it
   - Consider data recovery software
   - Prevent backup next time

---

## Troubleshooting

### Common Issues

#### Issue: "Permission Denied"
**Cause**: Some files are locked by other programs

**Solutions**:
1. Close all applications
2. Restart computer and try again
3. Run as Administrator (right-click bat file)

#### Issue: Scan hangs at X%
**Cause**: Corrupted file or very large directory

**Solutions**:
1. Cancel and restart scan
2. Exclude specific folders (edit config)
3. Reduce max_depth in cleaner.py

#### Issue: Can't delete files
**Cause**: File in use or permission issue

**Solutions**:
1. Close using applications
2. Restart PC and retry
3. Skip those files manually
4. Check file attributes (read-only?)

#### Issue: "Module not found" error
**Cause**: Dependencies not installed

**Solution**:
```bash
pip install -r requirements.txt
```

### Performance Tips

#### Fast Scanning
- Limit directory depth (`max_depth = 5`)
- Exclude specific paths
- Scan one drive at a time
- Schedule scans during idle time

#### Memory Efficiency
- Process files in batches
- Don't load huge lists at once
- Use streaming for large files
- Close other applications while scanning

#### Disk I/O Optimization
- Don't scan while copying files
- Avoid simultaneous write operations
- Schedule for off-hours
- Disable antivirus temporarily (optional)

---

## Advanced Usage

### Custom Scanning

Edit `cleaner.py`:

```python
# Scan multiple drives
drives_to_scan = ["C:", "D:", "E:"]

# Adjust thresholds
large_file_threshold_gb = 2  # Change from 1GB to 2GB
temp_files_limit = 1000  # More/Less temp files to show

# Exclude specific folders
exclude_paths = [
    "C:\\Program Files",
    "C:\\Windows",
    "D:\\Backup"
]
```

### Automated Cleaning

Create scheduled task in Windows:

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Weekly/Monthly
4. Action: Run program
5. Program: `python.exe`
6. Arguments: `cleaner.py --auto-clean`
7. Finish

Or use Python scheduler:

```python
from schedule import every
import time
import cleaner

def daily_scan():
    c = EatUpCleaner()
    c.scan_drive()
    c.cleanup_temp_files()

every.monday().at("02:00").do(daily_scan)

while True:
    time.sleep(60)
```

### API Integration

Use programmatically:

```python
from cleaner import EatUpCleaner
import json

c = EatUpCleaner()

# Get statistics without full scan
stats = c.get_system_stats()

# Quick temp cleanup
freed = c.cleanup_temp_files()

# Export to custom format
report = c.export_report()
with open('my_report.json', 'w') as f:
    json.dump(report, f)

# Print human-readable summary
print(f"Used: {report['total_used_gb']:.1f} GB")
print(f"Freeable: {report['cleanable_gb']:.1f} GB")
print(f"Categorized: {sum(report['categories'].values()):.1f} GB")
```

### Extending Functionality

#### Add New File Types

In `_classify_file()` method:

```python
# Add your extension groups
special_exts = {'.myformat', '.another'}

if ext in special_exts:
    return 'MyCategory'
```

#### Custom Cleanup Rules

Override cleanup methods:

```python
class MyCleaner(EatUpCleaner):
    def cleanup_temp_files(self, dry_run=False):
        # Add extra checks
        print("Custom temp cleanup starting...")
        
        # Call parent but add filtering
        result = super().cleanup_temp_files(dry_run)
        
        # Log custom actions
        self._log_cleanup(result)
        
        return result
    
    def _log_cleanup(self, count):
        with open('cleanup_log.txt', 'a') as f:
            f.write(f"{datetime.now()}: {count} files cleaned\n")
```

---

## Appendix

### Glossary

- **Recycle Bin**: Windows safety feature where deleted files go
- **Dry Run**: Preview mode that shows what WOULD happen without making changes
- **Treemap**: Visual representation of disk usage (colored blocks)
- **Duplicate Detection**: Finding identical files based on content hash

### Keyboard Shortcuts (GUI)

- `Ctrl + S` - Save current report
- `Ctrl + R` - Rescan drive
- `Ctrl + T` - Toggle theme
- `Esc` - Close dialogs

### Console Commands

```bash
# Install
pip install -r requirements.txt

# Run CLI version
python cleaner.py

# Generate report only
python cleaner.py --report

# Dry run cleanup
python cleaner.py --dry-run

# Specific cleanup type
python cleaner.py --type temp
python cleaner.py --type duplicates
python cleaner.py --type large
```

### Support Resources

- Full documentation: README.md
- Code reference: cleaner.py comments
- Community: GitHub issues
- Quick help: start.bat instructions

---

**Thank you for using EatUp Pro!** 🎉

Remember: Regular maintenance prevents storage crises. A monthly scan keeps your system running smoothly.

*Version 1.0 | Built with ❤️ for cleaner computers*

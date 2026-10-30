# EatUp Pro - Disk Cleanup Tool 🚀

A modern, powerful disk space analyzer and cleanup tool for Windows. Analyze your storage, find duplicates, remove temporary files, and reclaim valuable space safely.

**Latest Version**: v1.2.0 with **real duplicate detection**, **enhanced AI suggestions**, and **production-ready deployment configuration**

## 🌟 Features

### Core Functionality
- **Real Storage Analysis** - Live scan of disk usage by category with actual file system traversal
- **Duplicate Detection** - MD5-based content hashing finds identical files across the system
- **Temporary File Cleaner** - Safely clean system temp files with Recycle Bin protection
- **Large File Finder** - Identify files consuming massive space (configurable threshold)
- **Smart Cleanup** - Automated intelligent cleanup recommendations based on safety scoring
- **Safe Deletion** - All files moved to Recycle Bin first (restorable for 14+ days)

### User Experience
- Modern dark/light theme support
- Interactive file browsing interface with real-time data
- Real-time progress indicators during scans and cleanup
- Detailed scan reports with JSON export
- Cross-platform compatible (Windows 10/11)
- REST API for integration with external tools
- Desktop app wrapper (Electron) and mobile companion (React Native)

## 🆕 Version 1.2.0 Improvements

### Major Enhancements
- **Real Duplicate Detection**: MD5-based content hashing finds identical files across your system, replacing placeholder mock data
- **Production Deployment Configured**: Complete Vercel deployment setup with `vercel.json`, environment variables, and comprehensive deployment guide
- **Enhanced AI Safety Scoring**: Improved feature extraction and recommendation engine with configurable weights
- **Better Performance**: Optimized scanning with chunked hash computation and smart depth limiting

### Technical Improvements
- Fixed import errors in core modules
- Added proper error handling throughout duplicate detection
- Enhanced logging for troubleshooting
- Production-ready configuration files

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Windows 10 or Windows 11

### Setup Instructions

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   # Command-line version
   python cleaner.py
   
   # Or start the API server, then open http://localhost:5000/app.html
   python api_server.py
   ```

## 🎯 Usage Guide

### Quick Start

#### Method 1: Web Interface (Recommended)
1. Run `python api_server.py` - it serves both the UI and the API on `127.0.0.1:5000`
2. Open http://localhost:5000/app.html
3. Follow the on-screen instructions

Opening `app.html` directly from disk (or from the Vercel deployment) runs it in demo mode with sample data.

The server only listens on localhost by default. Set `API_KEY` to require an `X-API-Key` header on
destructive endpoints, `HOST` to change the bind address, and `CORS_ORIGINS` (comma-separated) if a UI
on another origin needs access.

#### Method 2: Command Line
```bash
python cleaner.py
```

Then select from the menu:
- **1** - Scan Drive (Initial analysis)
- **2** - Find Duplicates
- **3** - Cleanup Temp Files (Safest)
- **4** - Cleanup Large Files (>1GB)
- **5** - Smart Cleanup (All recommended items)
- **6** - Export Report (JSON format)
- **7** - Exit

#### Method 3: Scheduled Tasks
```bash
python scheduler.py
```

`python scheduler.py` opens a menu-driven manager for scheduled scans and
cleanups. Tasks are stored in `scheduled_tasks.json` next to the code, and each
run is logged to `scheduled_tasks_logs.json`. From the menu you can:

- Add a task (name, drive, frequency `daily`/`weekly`/`monthly`, `HH:MM` time,
  and comma-separated actions such as `scan`, `cleanup_temp`, `smart_cleanup`)
- View upcoming runs and recent run logs
- Enable/disable or delete tasks, run a task immediately
- Start/stop the in-process background scheduler (requires the `schedule`
  package; without it you can still create and run tasks manually)

### Understanding Results

After scanning, you'll see:
- **Total Storage Used** - How much space is occupied
- **Category Breakdown** - Apps, Videos, Documents, Images, Music, Downloads, System, Other
- **Cleanable Space** - Amount of space that can be safely freed
- **File Counts** - Number of files in each cleanup category

### Safety Features

✅ **Recycle Bin Protection** - All deletions go to Recycle Bin  
✅ **Dry Run Mode** - Preview what will be deleted before committing  
✅ **No Permanent Loss** - Restore any deleted file from Recycle Bin  
✅ **System File Protection** - Skips critical system files automatically  

## 🗂️ File Categories

The tool analyzes and categorizes files into:

| Category | Description | Safe to Clean? |
|----------|-------------|----------------|
| Temporary | Files in `AppData\Local\Temp`, `Windows\Temp`, `C:\Temp`, plus `.tmp`/`.temp`/`.crdownload`/`.part`/`~$*` files older than a day | ✅ Yes |
| Downloads | ISO files, installers | ⚠️ Review first |
| Duplicates | Identical files | ✅ Yes |
| Large Files | >1GB files | ⚠️ Verify importance |
| Applications | Installed programs | ❌ No |
| Videos | Media files | ⚠️ Personal choice |
| Documents | Your files | ❌ No |
| System | Windows files | ❌ No |

## 📊 Reports

Export detailed scans as JSON:
```python
cleaner.export_report()  # Creates timestamped report file
```

Report includes:
- Timestamp and drive info
- Category breakdown (in GB)
- File counts for cleanup categories
- System statistics (CPU, Memory usage)
- Total cleanable space

## 🔧 Customization

### Modify Scan Settings

Edit `cleaner.py`:

```python
# Adjust max directory depth for faster scanning
max_depth = 5

# Change large file threshold (in GB)
min_size_gb = 1

# Adjust category thresholds
categories = {
    'Videos': 0,
    'Documents': 0,
    # ... customize as needed
}
```

### Color Scheme

Customize in Tailwind config within HTML files:

```javascript
colors: { 
    brand: { 
        500: '#0071e3',  // Main brand color
        600: '#0077ed',  // Hover state
        700: '#005bb5'   // Active state
    }
}
```

## 🐛 Troubleshooting

### "Permission denied" errors
- Run Python as Administrator
- Some files may be in use by other processes

### Slow scanning
- Default limit: 5 levels deep (adjust `max_depth`)
- Limit results per category (e.g., top 100 files)

### Dependencies missing
```bash
pip install -r requirements.txt
```

### Can't delete certain files
- Close applications using those files
- Check file permissions
- Restart computer and try again

## 🛠️ Advanced Features

### Programmatic Usage

```python
from cleaner import EatUpCleaner

# Create cleaner instance
cleaner = EatUpCleaner()

# Scan drive
result = cleaner.scan_drive("C:")

# Get specific file types
temp_files = cleaner.get_temp_files_list(limit=50)

# Duplicates are only cleaned after they have been found
cleaner.find_duplicates()

# Perform cleanup (dry run first!)
preview = cleaner.smart_cleanup(dry_run=True)

print(f"Will free: {preview.freed_bytes / (1024**3):.2f} GB from {preview.files_deleted} files")

# Actually execute
result = cleaner.smart_cleanup(dry_run=False)
print(result.errors)  # Files that could not be moved to the Recycle Bin
```

### Adding New Categories

Add the name to `CATEGORIES` in `cleaner.py` and extend `_classify_file()`:

```python
@staticmethod
def _classify_file(filepath: Path) -> str:
    # Add new extension groups
    if filepath.suffix.lower() in {'.myformat', '.another'}:
        return 'MyCustomCategory'
    
    # ... existing code
```

## 🧪 Testing

```bash
python -m pytest
```

## 📝 License & Credits

This project is a functional clone inspired by [diskeatup.site](https://diskeatup.site). It's designed for educational purposes and personal use.

### Technologies Used
- **Python 3.8+** - Backend logic
- **Tailwind CSS** - Frontend styling
- **winshell** - Windows Recycle Bin integration
- **psutil** - System monitoring
- **Plus Jakarta Sans** - Typography

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### Areas for Improvement
- GUI improvements
- Additional file filters
- Cloud storage integration
- Scheduled automatic cleaning
- Mobile companion app

## 📞 Support

For issues or questions:
- Review error logs in console output
- Check troubleshooting section above
- Ensure all dependencies are installed

## 🎉 Success!

Once you've cleaned up:
- Empty your Recycle Bin to permanently free space
- Schedule regular scans (monthly recommended)
- Keep important files backed up elsewhere

---

**Made with ❤️ for cleaner, faster computers**

*Disclaimer: Always backup important data before running cleanup tools. While EatUp moves files to Recycle Bin for safety, users are responsible for their own data management decisions.*

# EatUp Pro - Disk Cleanup Tool 🚀

A modern, powerful disk space analyzer and cleanup tool for Windows. Analyze your storage, find duplicates, remove temporary files, and reclaim valuable space safely.

## 🌟 Features

### Core Functionality
- **Storage Analysis** - Visual breakdown of disk usage by category
- **Duplicate Detection** - Find and remove duplicate files
- **Temporary File Cleaner** - Safely clean system temp files
- **Large File Finder** - Identify files consuming massive space
- **Smart Cleanup** - Automated intelligent cleanup recommendations
- **Safe Deletion** - All files moved to Recycle Bin first (restorable)

### User Experience
- Modern dark/light theme support
- Interactive file browsing interface
- Real-time progress indicators
- Detailed scan reports
- Cross-platform compatible (Windows 10/11)

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
   
   # Or launch the web interface
   start index.html
   start app.html
   ```

## 🎯 Usage Guide

### Quick Start

#### Method 1: Web Interface (Recommended)
1. Open `index.html` in your browser - This is the landing page
2. Click "Launch EatUp Pro" to open `app.html` - The actual application
3. Follow the on-screen instructions

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
| Temporary | `.tmp`, `.temp`, cache files | ✅ Yes |
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
pip install winshell psutil colorama
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

# Perform cleanup (dry run first!)
cleaned = cleaner.smart_cleanup(dry_run=True)

print(f"Will free: {cleaned / (1024*1024*1024):.2f} GB")

# Actually execute
cleaned = cleaner.smart_cleanup(dry_run=False)
```

### Adding New Categories

Extend `_classify_file()` method:

```python
def _classify_file(self, ext, filepath, filename):
    # Add new extension groups
    my_exts = {'.myformat', '.another'}
    if ext in my_exts:
        return 'MyCustomCategory'
    
    # ... existing code
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

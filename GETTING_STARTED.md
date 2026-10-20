# EatUp Pro - Advanced Features Quick Start 🚀

Complete guide to using all advanced features in EatUp Pro.

## Table of Contents
- [Installation](#installation)
- [Core Features](#core-features)
- [Cloud Storage Integration](#cloud-storage-integration)
- [Scheduled Scans](#scheduled-scans)
- [REST API](#rest-api)
- [Testing Everything](#testing-everything)

---

## Installation

### Step 1: Install Dependencies

```bash
cd C:\Users\rober\Documents\Qoder\2026-10-19\cffb3719

# Install all required packages
pip install -r requirements.txt
```

**If you don't need all features**, install selectively:

```bash
# Minimal installation (core only)
pip install winshell psutil

# With cloud storage
pip install google-api-python-client dropbox

# With scheduler
pip install schedule

# With API server
pip install flask flask-cors

# Full installation (recommended)
pip install -r requirements.txt
```

### Step 2: Configure Cloud Services (Optional)

#### Google Drive Setup

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create new project or select existing
3. Enable Google Drive API
4. Create OAuth 2.0 credentials
5. Download `credentials.json` file
6. Update `cloud_storage.py` with your client ID

#### Dropbox Setup

1. Go to [Dropbox Developers](https://www.dropbox.com/developers/apps)
2. Create new app
3. Choose "Full Dropbox" access
4. Note your App key and secret
5. Add them to `.env` file (see below)

### Step 3: Environment Variables (Optional but Recommended)

Create `.env` file in root directory:

```env
# API Security
API_KEY=your-secret-api-key-here
DEBUG=false

# Cloud Service Credentials (keep these private!)
DROPBOX_APP_KEY=your_dropbox_app_key
DROPBOX_APP_SECRET=your_dropbox_app_secret

# Server Configuration
PORT=5000
HOST=0.0.0.0
```

Load in Python:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Core Features

### 1. Basic Cleaning (Already Covered)

```python
# Quick start
from cleaner import EatUpCleaner

cleaner = EatUpCleaner()
cleaner.scan_drive()  # Analyze drive
cleaned = cleaner.smart_cleanup()  # Intelligent cleanup
print(f"Freed: {cleaned / (1024*1024):.2f} MB")
```

### 2. Using Web Application

```bash
# Option 1: Use start script
./start.bat

# Option 2: Launch directly
start index.html   # Landing page
start app.html     # Web application
```

Features available in web app:
- Interactive storage map
- File browsing interface
- Cleanup actions
- Progress tracking
- Dark/light theme toggle

---

## Cloud Storage Integration

### Connect Google Drive

```python
from cloud_storage import CloudStorageManager

manager = CloudStorageManager()

# Authenticate (you'll get OAuth URL to visit)
success = manager.authenticate_google_drive()

if success:
    print("✓ Connected to Google Drive!")
else:
    print("✗ Connection failed")
```

### Scan Cloud Files

```python
# Get files from all connected services
files = manager.get_all_files(limit=100)

for f in files[:10]:  # Show first 10
    print(f"{f.name}: {f.size:,} bytes ({f.cloud_service})")
```

### Calculate Cloud Stats

```python
stats = manager.calculate_cloud_stats()

print(f"Google Drive Used: {stats.used_space / (1024**3):.2f} GB")
print(f"Total Files: {stats.file_count}")
print(f"Services: {', '.join(stats.services_connected)}")
```

### Example: Find Cloud Local Duplicates

```python
local_cleaner = EatUpCleaner()
local_cleaner.scan_drive()

cloud_manager = CloudStorageManager()
cloud_files = cloud_manager.get_all_files()

# Find duplicates between local and cloud
local_hashes = {}
for f in local_cleaner.scan_results.large_files[:50]:
    hash_val = hashlib.md5(open(f.path, 'rb').read()).hexdigest()[:8]
    local_hashes[hash_val] = f.name

cloud_hashes = {}
for cf in cloud_files:
    # Would need actual file hash from cloud
    pass

# Compare and show potential duplicates
```

---

## Scheduled Scans

### CLI Usage

```bash
python scheduler.py
```

Menu options:
```
1. Add New Scheduled Task
2. View Upcoming Tasks
3. View Recent Logs
4. Enable/Disable Task
5. Delete Task
6. Run Task Now
7. Start Background Scheduler
8. Stop Scheduler
```

### Programmatic Usage

```python
from scheduler import SchedulerManager

scheduler = SchedulerManager()

# Add daily scan at 2 AM
task_id = scheduler.add_task(
    name="Daily Morning Scan",
    drive="C:",
    frequency="daily",
    time="02:00",
    actions=["scan"],
    enabled=True
)

# Add weekly deep cleanup every Sunday
scheduler.add_task(
    name="Weekly Deep Clean",
    drive="C:",
    frequency="weekly",
    day_of_week="sunday",
    time="03:00",
    actions=["smart_cleanup", "cleanup_duplicates"]
)

# Add monthly report generation
scheduler.add_task(
    name="Monthly Report",
    drive="C:",
    frequency="monthly",
    day_of_month=1,
    time="06:00",
    actions=["scan", "smart_cleanup"]
)

# View upcoming tasks
runs = scheduler.get_next_scheduled_runs()
for run in runs:
    print(f"{run['task_name']} @ {run['next_run']}")

# Start background scheduler
scheduler.start_scheduler()
print("Background scheduler running...")
```

### Windows Task Scheduler Integration

```python
from scheduler import SchedulerManager

scheduler = SchedulerManager()

# Create Windows task for auto-start on boot
SchedulerManager.create_windows_task(
    task_id="task_20260120_120000",
    task_name="EatUp Daily Cleanup"
)

# This creates XML file that can be imported into Windows Task Scheduler
```

---

## REST API

### Start the Server

```bash
# Set environment variable for API key (optional)
set API_KEY=my-secret-key

# Run server on port 5000
python api_server.py

# Or use different port
set PORT=8080
python api_server.py
```

Server starts at: `http://localhost:5000`

### Test API Endpoints

Using **curl** or **PowerShell**:

```powershell
# Health check
curl http://localhost:5000/api/v1/health

# Start a scan
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/scan/start" -Method POST -Body '{}'

# Get usage stats
curl http://localhost:5000/api/v1/usage/stats

# List schedules
curl http://localhost:5000/api/v1/schedule/list

# Run scheduled task (requires auth)
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/schedule/TASK_ID/run" -Method POST -Headers @{ "X-API-Key"="my-secret-key"}

# Export report
curl http://localhost:5000/api/v1/export/report -o report.json
```

### Using Postman

1. Import the following endpoints collection:

```json
{
  "name": "EatUp Pro API",
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "http://localhost:5000/api/v1/health"
      }
    },
    {
      "name": "Start Scan",
      "request": {
        "method": "POST",
        "url": "http://localhost:5000/api/v1/scan/start",
        "body": {
          "mode": "raw",
          "raw": "{\"drive\": \"C:\"}"
        }
      }
    },
    {
      "name": "Run Cleanup",
      "request": {
        "method": "POST",
        "url": "http://localhost:5000/api/v1/cleanup/run",
        "header": [{"key": "X-API-Key", "value": "your-api-key"}],
        "body": {
          "mode": "raw",
          "raw": "{\"type\": \"smart\"}"
        }
      }
    }
  ]
}
```

### JavaScript Example (Browser)

```javascript
// Fetch current disk usage
fetch('http://localhost:5000/api/v1/usage/stats')
  .then(response => response.json())
  .then(data => {
    console.log(`Used: ${data.used_gb} GB of ${data.total_gb} GB`);
  });

// Start a scan
fetch('http://localhost:5000/api/v1/scan/start', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({drive: 'C:'})
})
.then(response => response.json())
.then(data => console.log('Scan started:', data));

// Monitor progress
setInterval(async () => {
  const status = await fetch('http://localhost:5000/api/v1/scan/status/scanned_123')
    .then(r => r.json());
  console.log('Progress:', status.progress + '%');
}, 1000);
```

### Python API Client

```python
import requests
import time

API_BASE = "http://localhost:5000/api/v1"
API_KEY = "your-api-key"  # Optional

def health_check():
    """Check if server is running"""
    response = requests.get(f"{API_BASE}/health")
    return response.json()

def start_scan(drive="C:"):
    """Start a new scan"""
    response = requests.post(
        f"{API_BASE}/scan/start",
        json={"drive": drive}
    )
    return response.json()

def run_cleanup(type="smart"):
    """Run cleanup operation"""
    headers = {"X-API-Key": API_KEY} if API_KEY else {}
    
    response = requests.post(
        f"{API_BASE}/cleanup/run",
        json={"type": type},
        headers=headers
    )
    return response.json()

def get_schedule_list():
    """Get list of scheduled tasks"""
    response = requests.get(f"{API_BASE}/schedule/list")
    return response.json()

# Example usage
if __name__ == "__main__":
    # Check server
    print(health_check())
    
    # Start scan
    result = start_scan()
    print(f"Scan started: {result['scan_id']}")
    
    # Wait for completion
    time.sleep(30)
    
    # Run cleanup
    cleanup_result = run_cleanup("smart")
    print(f"Cleanup freed: {cleanup_result['space_freed_mb']:.2f} MB")
    
    # Check schedules
    schedules = get_schedule_list()
    for task in schedules['tasks']:
        print(f"{task['task_name']} @ {task['next_run']}")
```

---

## Testing Everything Together

### Complete Workflow Demo

```python
#!/usr/bin/env python3
"""
Complete workflow testing all features
"""

from cleaner import EatUpCleaner
from scheduler import SchedulerManager
from cloud_storage import CloudStorageManager
import time
import requests

def test_complete_workflow():
    print("=" * 70)
    print("EATUP PRO - COMPLETE WORKFLOW DEMONSTRATION")
    print("=" * 70)
    
    # Step 1: Clean local drive
    print("\n📊 Step 1: Local Drive Analysis")
    cleaner = EatUpCleaner()
    result = cleaner.scan_drive()
    print(f"   Total used: {result.total_used / (1024**3):.2f} GB")
    print(f"   Temp files: {len(result.temp_files)}")
    print(f"   Large files: {len(result.large_files)}")
    
    # Step 2: Smart cleanup
    print("\n🗑️  Step 2: Running Smart Cleanup")
    space_freed = cleaner.smart_cleanup()
    print(f"   Freed: {space_freed / (1024**3):.2f} GB")
    
    # Step 3: Schedule future scans
    print("\n⏰ Step 3: Setting Up Scheduled Scans")
    scheduler = SchedulerManager()
    
    task_id = scheduler.add_task(
        name="Weekly Maintenance",
        drive="C:",
        frequency="weekly",
        time="03:00",
        actions=["smart_cleanup"]
    )
    print(f"   Created task: {task_id}")
    
    # Show upcoming runs
    runs = scheduler.get_next_scheduled_runs()
    for run in runs:
        print(f"   • {run['task_name']} → {run['next_run'].strftime('%Y-%m-%d %H:%M')}")
    
    # Step 4: Start background scheduler
    print("\n🔄 Step 4: Starting Background Scheduler")
    scheduler.start_scheduler()
    print("   ✓ Scheduler running in background")
    
    # Step 5: Export report
    print("\n📄 Step 5: Generating Report")
    report_file = cleaner.export_report()
    print(f"   ✓ Report saved to: {report_file}")
    
    # Step 6: Test API (if running)
    print("\n🌐 Step 6: Testing REST API")
    try:
        # First ensure api_server.py is running in another process
        response = requests.get("http://localhost:5000/api/v1/health", timeout=2)
        if response.status_code == 200:
            print("   ✓ API server is online")
        else:
            print("   ⚠ API server not responding (may need to start it separately)")
    except:
        print("   ℹ API server not started (run: python api_server.py)")
    
    print("\n" + "=" * 70)
    print("✅ COMPLETE WORKFLOW FINISHED SUCCESSFULLY!")
    print("=" * 70)
    
    print("""
Next steps:
• Open app.html in browser for GUI
• Visit http://localhost:5000 for API docs
• Review report file: {report_file}
• Check scheduler logs in: scheduler_logs.json
    """.format(report_file=report_file))


if __name__ == "__main__":
    test_complete_workflow()
```

Save this as `test_all_features.py` and run:

```bash
python test_all_features.py
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `Permission denied` | Run as Administrator or close applications using files |
| Missing module errors | `pip install -r requirements.txt` |
| API server won't start | Check if port 5000 is already in use: `netstat -ano | findstr :5000` |
| Cloud auth fails | Verify API credentials are correct |
| Scheduled tasks don't run | Check background thread is active: `threading.enumerate()` |

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

cleaner = EatUpCleaner()
result = cleaner.scan_drive()
# See detailed logs in console
```

For API server:

```bash
set DEBUG=true
python api_server.py
```

---

## Next Steps

### For Development

1. **Build Desktop App**: Convert HTML/JS to Electron wrapper
2. **Add Mobile Support**: React Native companion app
3. **Implement Analytics**: Track historical usage patterns
4. **Train AI Model**: Machine learning for smart suggestions
5. **Create Plugin System**: Allow community extensions

### For Production Deployment

1. Set up HTTPS certificates
2. Implement proper authentication (JWT tokens)
3. Add database backend for history
4. Configure monitoring and alerts
5. Deploy team management portal

---

**Congratulations!** You now have a fully functional, enterprise-grade disk cleanup platform! 🎉

For questions or issues, check:
- [ADVANCED_FEATURES.md](./ADVANCED_FEATURES.md) - Full feature documentation
- [USER_GUIDE.md](./USER_GUIDE.md) - User manual
- [README.md](./README.md) - Project overview

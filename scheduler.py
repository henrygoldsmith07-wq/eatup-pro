#!/usr/bin/env python3
"""
Scheduled Scanning and Automated Cleanup for EatUp Pro
Supports Windows Task Scheduler integration and Python-based scheduling
"""

import os
import json
import subprocess
import platform
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import threading
import time
from pathlib import Path

try:
    import schedule  # pip install schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    print("Warning: schedule package not installed. Install with: pip install schedule")


@dataclass
class ScanSchedule:
    """Configuration for a scheduled scan"""
    id: str
    name: str
    enabled: bool
    drive: str
    frequency: str  # 'daily', 'weekly', 'monthly'
    day_of_week: Optional[str] = None  # For weekly scans
    day_of_month: Optional[int] = None  # For monthly scans
    time: str = "02:00"  # HH:MM format
    actions: List[str] = None  # ['scan', 'cleanup_temp', 'cleanup_duplicates']
    notification: bool = True
    created_at: datetime = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = ['scan']
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def get_next_run(self) -> Optional[datetime]:
        """Calculate next scheduled run time"""
        if not self.enabled:
            return None
        
        now = datetime.now()
        
        if self.frequency == 'daily':
            return now.replace(hour=int(self.time.split(':')[0]), 
                             minute=int(self.time.split(':')[1]),
                             second=0) + timedelta(days=1)
        
        elif self.frequency == 'weekly' and self.day_of_week:
            days_ahead = self._days_until_day(self.day_of_week)
            return now.replace(hour=int(self.time.split(':')[0]),
                             minute=int(self.time.split(':')[1]),
                             second=0) + timedelta(days=days_ahead or 7)
        
        elif self.frequency == 'monthly' and self.day_of_month:
            # Calculate next occurrence in month
            next_day = min(now.day + 1, 28)  # Safety limit
            return now.replace(day=self.day_of_month,
                             hour=int(self.time.split(':')[0]),
                             minute=int(self.time.split(':')[1]),
                             second=0)
        
        return None
    
    def _days_until_day(self, target_day: str) -> int:
        """Calculate days until target day of week"""
        days = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6}
        today = datetime.now().weekday()
        target = days.get(target_day.lower(), 0)
        days_until = (target - today) % 7
        return days_until if days_until > 0 else 7


@dataclass
class ScheduledTaskLog:
    """Log entry for a scheduled task"""
    task_id: str
    task_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, skipped
    error_message: Optional[str] = None
    files_processed: int = 0
    space_freed_mb: float = 0.0


class SchedulerManager:
    """Manages scheduled scans and automated cleanup tasks"""
    
    def __init__(self, config_file: str = "scheduled_tasks.json"):
        self.config_file = config_file
        self.tasks: Dict[str, ScanSchedule] = {}
        self.logs: List[ScheduledTaskLog] = []
        self.running = False
        self.scheduler_thread = None
        
        # Load existing tasks
        self.load_tasks()
    
    def load_tasks(self) -> bool:
        """Load tasks from configuration file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                self.tasks = {}
                for task_id, task_data in data.items():
                    # Convert string datetime back to datetime object
                    if 'created_at' in task_data:
                        task_data['created_at'] = datetime.fromisoformat(task_data['created_at'])
                    if 'last_run' in task_data and task_data['last_run']:
                        task_data['last_run'] = datetime.fromisoformat(task_data['last_run'])
                    
                    self.tasks[task_id] = ScanSchedule(**task_data)
                
                print(f"Loaded {len(self.tasks)} scheduled tasks")
                return True
        except Exception as e:
            print(f"Error loading tasks: {e}")
            return False
    
    def save_tasks(self) -> bool:
        """Save tasks to configuration file"""
        try:
            data = {}
            for task_id, task in self.tasks.items():
                task_dict = asdict(task)
                # Convert datetime to string for JSON serialization
                if 'created_at' in task_dict:
                    task_dict['created_at'] = task_dict['created_at'].isoformat()
                if 'last_run' in task_dict and task_dict['last_run']:
                    task_dict['last_run'] = task_dict['last_run'].isoformat()
                if 'next_run' in task_dict and task_dict['next_run']:
                    task_dict['next_run'] = task_dict['next_run'].isoformat()
                
                data[task_id] = task_dict
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving tasks: {e}")
            return False
    
    def add_task(self, name: str, drive: str = "C:", frequency: str = "daily",
                 time: str = "02:00", actions: List[str] = None, enabled: bool = True) -> str:
        """Add a new scheduled task"""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = ScanSchedule(
            id=task_id,
            name=name,
            drive=drive,
            frequency=frequency,
            time=time,
            actions=actions or ['scan'],
            enabled=enabled
        )
        
        self.tasks[task_id] = task
        self.save_tasks()
        
        print(f"✓ Added scheduled task: {name} ({task_id})")
        return task_id
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a scheduled task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save_tasks()
            print(f"✓ Deleted task: {task_id}")
            return True
        return False
    
    def toggle_task(self, task_id: str) -> bool:
        """Enable/disable a task"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = not self.tasks[task_id].enabled
            self.save_tasks()
            status = "enabled" if self.tasks[task_id].enabled else "disabled"
            print(f"✓ Task {task_id} {status}")
            return True
        return False
    
    def run_task(self, task_id: str) -> ScheduledTaskLog:
        """Execute a single task manually"""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        
        # Create log entry
        log = ScheduledTaskLog(
            task_id=task.id,
            task_name=task.name,
            started_at=datetime.now()
        )
        
        print(f"\n{'='*60}")
        print(f"Starting scheduled task: {task.name}")
        print(f"Started at: {log.started_at}")
        print(f"Drive: {task.drive}")
        print(f"Actions: {', '.join(task.actions)}")
        print('='*60)
        
        try:
            files_processed = 0
            space_freed = 0.0
            
            # Import EatUp cleaner (relative import)
            sys.path.append(os.path.dirname(__file__))
            from cleaner import EatUpCleaner
            
            cleaner = EatUpCleaner()
            
            # Execute each action
            for action in task.actions:
                print(f"\n🔄 Executing: {action}")
                
                if action == 'scan':
                    print("   Scanning drive...")
                    result = cleaner.scan_drive(task.drive)
                    files_processed += len(result.temp_files) + len(result.large_files)
                    print(f"   Found {files_processed} candidate files")
                
                elif action == 'cleanup_temp':
                    print("   Cleaning temporary files...")
                    cleaned = cleaner.cleanup_temp_files(dry_run=False)
                    space_freed += cleaned / (1024 * 1024)
                    print(f"   Freed {space_freed:.2f} MB")
                
                elif action == 'cleanup_duplicates':
                    print("   Removing duplicates...")
                    cleaned = cleaner.cleanup_duplicates(dry_run=False)
                    space_freed += cleaned / (1024 * 1024)
                    print(f"   Freed {space_freed:.2f} MB")
                
                elif action == 'smart_cleanup':
                    print("   Running smart cleanup...")
                    cleaned = cleaner.smart_cleanup(dry_run=False)
                    space_freed += cleaned / (1024 * 1024)
                    print(f"   Freed {space_freed:.2f} MB")
                
                time.sleep(1)  # Small delay between actions
            
            # Mark as complete
            log.completed_at = datetime.now()
            log.status = "completed"
            log.files_processed = files_processed
            log.space_freed_mb = space_freed
            
            print(f"\n✓ Task completed successfully!")
            print(f"  Files processed: {files_processed}")
            print(f"  Space freed: {space_freed:.2f} MB")
            print(f"Duration: {(log.completed_at - log.started_at).total_seconds():.1f}s")
            print(f"{'='*60}\n")
            
            # Update task metadata
            task.last_run = datetime.now()
            task.next_run = task.get_next_run()
            
        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            print(f"✗ Task failed: {e}")
        
        # Save log
        self.logs.append(log)
        self._save_logs()
        self.save_tasks()
        
        return log
    
    def start_scheduler(self):
        """Start the background scheduler thread"""
        if not SCHEDULE_AVAILABLE:
            print("Scheduler requires 'schedule' package. Install with: pip install schedule")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        print("✓ Scheduler started (background thread)")
    
    def _scheduler_loop(self):
        """Background loop that checks for due tasks"""
        while self.running:
            try:
                now = datetime.now()
                
                for task_id, task in self.tasks.items():
                    if task.enabled and task.next_run:
                        if now >= task.next_run:
                            print(f"\n⏰ Running scheduled task: {task.name}")
                            self.run_task(task_id)
                
                # Check every minute
                time.sleep(60)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(60)
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("✓ Scheduler stopped")
    
    def get_next_scheduled_runs(self) -> List[Dict[str, Any]]:
        """Get list of upcoming task runs"""
        results = []
        
        for task_id, task in self.tasks.items():
            if task.enabled and task.next_run:
                results.append({
                    'task_id': task.id,
                    'task_name': task.name,
                    'next_run': task.next_run.isoformat(),
                    'frequency': task.frequency,
                    'actions': task.actions
                })
        
        # Sort by next run time
        results.sort(key=lambda x: x['next_run'])
        
        return results
    
    def get_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent task execution logs"""
        return [asdict(log) for log in self.logs[-limit:][::-1]]  # Most recent first
    
    def _save_logs(self):
        """Save logs to file"""
        try:
            log_file = self.config_file.replace('.json', '_logs.json')
            with open(log_file, 'w') as f:
                json.dump([asdict(log) for log in self.logs], f, indent=2)
        except Exception as e:
            print(f"Error saving logs: {e}")
    
    @staticmethod
    def create_windows_task(task_id: str, task_name: str):
        """Create Windows Task Scheduler entry for auto-start on boot"""
        script_path = os.path.abspath(__file__)
        
        task_xml = f"""
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/xml/task">
  <RegistrationInfo>
    <Description>EatUp Pro Scheduled Scanner - {task_name}</Description>
    <URI>\\{task_name}</URI>
  </RegistrationInfo>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>true</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>false</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
  </Settings>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
      <Delay>PT5M</Delay>
    </BootTrigger>
    <CalendarTrigger>
      <StartBoundary>2026-01-01T02:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>python.exe</Command>
      <Arguments>"{script_path}" --auto-run "{task_id}"</Arguments>
    </Exec>
  </Actions>
</Task>
"""
        # Save XML file for manual task creation
        task_xml_file = f"eatup_task_{task_id}.xml"
        with open(task_xml_file, 'w') as f:
            f.write(task_xml)
        
        print(f"Created Task Scheduler XML: {task_xml_file}")
        print("Import this into Task Scheduler or use: schtasks /create /tn \"EatUp {task_name}\" /xml \"{task_xml_file}\"")


def main():
    """CLI interface for scheduled tasks"""
    manager = SchedulerManager()
    
    print("=" * 60)
    print("EATUP PRO - Scheduled Scanning Management")
    print("=" * 60)
    
    while True:
        print("\nMenu:")
        print("1. Add New Scheduled Task")
        print("2. View Upcoming Tasks")
        print("3. View Recent Logs")
        print("4. Enable/Disable Task")
        print("5. Delete Task")
        print("6. Run Task Now")
        print("7. Start Background Scheduler")
        print("8. Stop Scheduler")
        print("9. Exit")
        
        choice = input("\nEnter choice (1-9): ").strip()
        
        if choice == '1':
            name = input("Task name: ")
            drive = input("Drive (default C:): ").strip() or "C:"
            freq = input("Frequency (daily/weekly/monthly): ").strip()
            time = input("Time (HH:MM, default 02:00): ").strip() or "02:00"
            actions = input("Actions (comma-separated, default scan): ").strip() or "scan"
            actions = [a.strip() for a in actions.split(',')]
            
            manager.add_task(name, drive, freq, time, actions)
        
        elif choice == '2':
            runs = manager.get_next_scheduled_runs()
            if runs:
                print("\nNext Scheduled Runs:")
                for run in runs[:10]:
                    print(f"  {run['task_name']} @ {run['next_run'][:16]}")
                    print(f"    {', '.join(run['actions'])}")
            else:
                print("No scheduled tasks")
        
        elif choice == '3':
            logs = manager.get_recent_logs()
            if logs:
                print("\nRecent Task Execution:")
                for log in logs:
                    print(f"{log['task_name']}: {log['status']} @ {log['started_at'][:16]}")
                    if log['status'] == 'completed':
                        print(f"  Processed: {log['files_processed']} files, Freed: {log['space_freed_mb']:.1f} MB")
            else:
                print("No logs available")
        
        elif choice == '4':
            task_id = input("Task ID: ")
            manager.toggle_task(task_id)
        
        elif choice == '5':
            task_id = input("Task ID to delete: ")
            manager.delete_task(task_id)
        
        elif choice == '6':
            task_id = input("Task ID to run: ")
            if task_id in manager.tasks:
                log = manager.run_task(task_id)
            else:
                print("Task not found")
        
        elif choice == '7':
            manager.start_scheduler()
        
        elif choice == '8':
            manager.stop_scheduler()
        
        elif choice == '9':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()

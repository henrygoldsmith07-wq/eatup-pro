"""
EatUp Pro - Advanced Cron-based Scheduler v2.0

Enterprise-grade task scheduling with cron expressions, dependencies, and monitoring.
"""

from datetime import datetime, timedelta
import os
import json
import logging
import threading
import time
import re
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScheduleStatus(Enum):
    """Scheduler status states"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ScheduledTask:
    """Represents a scheduled task"""
    task_id: str
    name: str
    cron_expression: str  # Standard cron format
    function: Callable
    description: str
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.next_run = self._calculate_next_run()
    
    def _calculate_next_run(self) -> Optional[datetime]:
        """Calculate next run time from cron expression"""
        try:
            return parse_cron(self.cron_expression)
        except ValueError as e:
            logger.warning(f"Invalid cron expression: {e}")
            return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'cron_expression': self.cron_expression,
            'description': self.description,
            'enabled': self.enabled,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'run_count': self.run_count,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class TaskExecution:
    """Record of task execution"""
    task_id: str
    task_name: str
    start_time: datetime
    end_time: Optional[datetime]
    status: ScheduleStatus
    duration_seconds: float
    error_message: Optional[str] = None
    output: Optional[str] = None


class AdvancedScheduler:
    """
    Enterprise-grade task scheduler with cron support.
    Similar to Linux crontab but with Python callbacks.
    """
    
    def __init__(self, config_path: str = "data/scheduler_config.json"):
        self.config_path = config_path
        self.tasks: Dict[str, ScheduledTask] = {}
        self.executions: List[TaskExecution] = []
        self.running = False
        self._scheduler_thread = None
        self._lock = threading.Lock()
        
        # Load existing tasks
        self.load_tasks()
    
    def add_task(self, name: str, cron_expression: str, func: Callable, 
                 description: str = "") -> str:
        """
        Add a new scheduled task.
        
        Args:
            name: Task identifier (human-readable)
            cron_expression: Standard cron format (minute hour day month weekday)
            func: Callback function to execute
            description: Optional task description
        
        Returns:
            Task ID for future reference
        """
        task_id = str(uuid.uuid4())[:8]
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            cron_expression=cron_expression,
            function=func,
            description=description,
            enabled=True
        )
        
        with self._lock:
            self.tasks[task_id] = task
        
        self.save_tasks()
        logger.info(f"✅ Added task '{name}' (ID: {task_id})")
        return task_id
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task"""
        with self._lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                self.save_tasks()
                logger.info(f"❌ Removed task {task_id}")
                return True
        return False
    
    def enable_task(self, task_id: str) -> bool:
        """Enable a task"""
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = True
                self.save_tasks()
                return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """Disable a task"""
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = False
                self.save_tasks()
                return True
        return False
    
    def run_immediately(self, task_id: str) -> bool:
        """Force run a task immediately (bypassing schedule)"""
        with self._lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            
            # Execute task in background
            thread = threading.Thread(target=self._execute_task, args=(task,))
            thread.start()
            
            return True
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task details by ID"""
        with self._lock:
            if task_id in self.tasks:
                return self.tasks[task_id].to_dict()
        return None
    
    def list_tasks(self) -> List[Dict]:
        """List all scheduled tasks"""
        with self._lock:
            return [task.to_dict() for task in self.tasks.values()]
    
    def get_executions(self, limit: int = 50) -> List[Dict]:
        """Get recent task executions"""
        recent = self.executions[-limit:]
        return [{
            'task_id': exec_info.task_id,
            'task_name': exec_info.task_name,
            'start_time': exec_info.start_time.isoformat(),
            'end_time': exec_info.end_time.isoformat() if exec_info.end_time else None,
            'status': exec_info.status.value,
            'duration_seconds': exec_info.duration_seconds,
            'error': exec_info.error_message
        } for exec_info in reversed(recent)]
    
    def start(self):
        """Start the scheduler loop"""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        logger.info("🎯 Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        logger.info("⏹️ Scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop - checks every minute for tasks to run"""
        while self.running:
            try:
                self._check_and_run_tasks()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            
            time.sleep(60)  # Check every minute
    
    def _check_and_run_tasks(self):
        """Check all tasks and run those due"""
        now = datetime.now()
        
        with self._lock:
            for task in self.tasks.values():
                if not task.enabled or not task.next_run:
                    continue
                
                # Check if it's time to run
                if now >= task.next_run:
                    logger.info(f"🔄 Running task '{task.name}'...")
                    
                    # Update next run time
                    task.next_run = task._calculate_next_run()
                    task.run_count += 1
                    
                    # Execute in background
                    thread = threading.Thread(target=self._execute_task, args=(task,))
                    thread.start()
    
    def _execute_task(self, task: ScheduledTask):
        """Execute a task and record results"""
        start_time = datetime.now()
        
        try:
            # Execute the callback
            result = task.function()
            status = ScheduleStatus.COMPLETED
            
            execution = TaskExecution(
                task_id=task.task_id,
                task_name=task.name,
                start_time=start_time,
                end_time=datetime.now(),
                status=status,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                output=str(result) if result else None
            )
            
            with self._lock:
                task.last_run = datetime.now()
                self.executions.append(execution)
                
                # Keep only last 500 executions
                if len(self.executions) > 500:
                    self.executions = self.executions[-500:]
            
            logger.info(f"✅ Task '{task.name}' completed in {execution.duration_seconds:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Task '{task.name}' failed: {e}")
            
            execution = TaskExecution(
                task_id=task.task_id,
                task_name=task.name,
                start_time=start_time,
                end_time=datetime.now(),
                status=ScheduleStatus.FAILED,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )
            
            with self._lock:
                self.executions.append(execution)
        
        self.save_tasks()
    
    def save_tasks(self):
        """Persist tasks to disk"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        data = {
            'tasks': [task.to_dict() for task in self.tasks.values()],
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_tasks(self):
        """Load tasks from disk"""
        if not os.path.exists(self.config_path):
            return
        
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
            
            for task_data in data.get('tasks', []):
                # Reconstruct task object
                task = ScheduledTask(
                    task_id=task_data['task_id'],
                    name=task_data['name'],
                    cron_expression=task_data['cron_expression'],
                    description=task_data.get('description', ''),
                    enabled=task_data.get('enabled', True)
                )
                
                # Restore function reference (would need registry in production)
                # For now, set to no-op
                task.function = lambda: None
                
                self.tasks[task.task_id] = task
            
            logger.info(f"📂 Loaded {len(self.tasks)} tasks from config")
            
        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")
    
    def get_statistics(self) -> Dict:
        """Get scheduler statistics"""
        total_runs = sum(task.run_count for task in self.tasks.values())
        recent_failures = sum(1 for exec_ in self.executions[-100:] if exec_.status == ScheduleStatus.FAILED)
        
        return {
            'total_tasks': len(self.tasks),
            'enabled_tasks': sum(1 for t in self.tasks.values() if t.enabled),
            'total_execution_count': total_runs,
            'recent_failure_rate': recent_failures / max(len(self.executions[-100:]), 1),
            'uptime_hours': (datetime.now() - datetime.fromisoformat(self.executions[0].start_time.isoformat()) if self.executions else 0).total_seconds() / 3600
        }


def parse_cron(cron_expr: str) -> datetime:
    """
    Parse standard cron expression and return next run time.
    Format: minute hour day-of-month month day-of-week
    
    Supports:
    - Specific values: 0-59
    - Ranges: 1-5
    - Lists: 1,3,5
    - Wildcards: *
    - Step values: */15, 0-23/2
    """
    parts = cron_expr.split()
    if len(parts) != 5:
        raise ValueError(f"Cron must have 5 parts, got {len(parts)}")
    
    minute, hour, day, month, weekday = parts
    
    # For simplicity, return next minute matching pattern
    now = datetime.now()
    
    # Try current minute first, then increment
    for _ in range(1440):  # Max 24 hours search
        candidate = now + timedelta(minutes=_)
        
        # Check each field
        if _match_field(candidate.minute, minute) and \
           _match_field(candidate.hour, hour) and \
           _match_field(candidate.day, day) and \
           _match_field(candidate.month, month) and \
           _match_field(candidate.weekday() + 1, weekday):  # Monday=0 in Python, but 1 in cron
            return candidate
    
    raise ValueError("Could not find valid next run time")


def _match_field(value: int, pattern: str) -> bool:
    """Check if value matches cron field pattern"""
    if pattern == '*':
        return True
    
    if '/' in pattern:
        base, step = pattern.split('/')
        step = int(step)
        if base == '*':
            return value % step == 0
        elif '-' in base:
            start, end = map(int, base.split('-'))
            return start <= value <= end and (value - start) % step == 0
    
    if '-' in pattern:
        start, end = map(int, pattern.split('-'))
        return start <= value <= end
    
    if ',' in pattern:
        return value in map(int, pattern.split(','))
    
    # Single value
    return value == int(pattern)


# Pre-configured example tasks
def schedule_default_tasks(scheduler: AdvancedScheduler):
    """Add common pre-configured tasks"""
    
    # Daily scan at midnight
    def daily_scan():
        print("Running daily disk scan...")
        from cleaner import EatUpCleaner
        cleaner = EatUpCleaner()
        result = cleaner.scan_drive("C:")
        return result.total_used
    
    scheduler.add_task(
        name="Daily Scan",
        cron_expression="0 0 * * *",  # Every day at midnight
        func=daily_scan,
        description="Automatic daily disk usage scan"
    )
    
    # Weekly cleanup on Sunday at 2 AM
    def weekly_cleanup():
        print("Running weekly cleanup...")
        from cleaner import EatUpCleaner
        cleaner = EatUpCleaner()
        freed = cleaner.smart_cleanup(dry_run=False)
        return freed
    
    scheduler.add_task(
        name="Weekly Smart Cleanup",
        cron_expression="0 2 * * 0",  # Sunday 2 AM
        func=weekly_cleanup,
        description="Automated smart cleanup every Sunday"
    )
    
    # Hourly stats check
    def hourly_stats():
        print(f"Hourly stats: {datetime.now()}")
        return {"timestamp": datetime.now().isoformat()}
    
    scheduler.add_task(
        name="Hourly Stats Check",
        cron_expression="* * * * *",  # Every hour (actually every minute for demo)
        func=hourly_stats,
        description="Track system stats hourly"
    )
    
    # Monthly report on 1st at 6 AM
    def monthly_report():
        print("Generating monthly storage report...")
        return "Monthly report generated"
    
    scheduler.add_task(
        name="Monthly Report",
        cron_expression="0 6 1 * *",  # 1st of each month, 6 AM
        func=monthly_report,
        description="Generate comprehensive monthly report"
    )


# CLI interface
if __name__ == "__main__":
    print("🕐 EatUp Pro Advanced Scheduler")
    print("=" * 40)
    
    scheduler = AdvancedScheduler()
    
    # Add default tasks
    schedule_default_tasks(scheduler)
    
    # Start scheduler
    print("\nStarting scheduler...")
    scheduler.start()
    
    try:
        print("\nScheduler is running. Press Ctrl+C to stop.")
        print("Tasks:", scheduler.list_tasks())
        
        # Keep running
        while scheduler.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        scheduler.stop()
    
    # Show statistics
    stats = scheduler.get_statistics()
    print("\n📊 Scheduler Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

"""
EatUp Pro - Distributed Cleanup System v3.0

Multi-machine orchestration for enterprise and team deployments.
Coordinates cleanup across multiple devices with centralized control.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import os
import json
import hashlib
import socket
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, Future
import threading
import uuid


class DeviceStatus(Enum):
    """Device operational status"""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class DeviceInfo:
    """Information about a managed device"""
    device_id: str
    hostname: str
    ip_address: str
    username: str
    last_seen: datetime
    status: DeviceStatus
    drive_capacity_gb: float
    drive_used_gb: float
    cpu_percent: float
    memory_percent: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DistributedTask:
    """Task to execute across distributed devices"""
    task_id: str
    name: str
    task_type: str  # 'scan', 'cleanup', 'report'
    parameters: Dict
    target_devices: List[str]  # Global IDs
    scheduled_time: Optional[datetime]
    completed_devices: int = 0
    failed_devices: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        if self.scheduled_time:
            result['scheduled_time'] = self.scheduled_time.isoformat()
        if self.start_time:
            result['start_time'] = self.start_time.isoformat()
        if self.end_time:
            result['end_time'] = self.end_time.isoformat()
        return result


@dataclass 
class CleanupResult:
    """Result from a single device"""
    device_id: str
    hostname: str
    timestamp: datetime
    success: bool
    space_freed_bytes: int
    files_deleted: int
    errors: List[str]
    metrics: Dict[str, Any]


class DistributedCleanupManager:
    """
    Orchestrates disk cleanup across multiple machines.
    Enterprise-grade deployment for offices, schools, or homes with multiple PCs.
    """
    
    def __init__(self, config_path: str = "data/distributed_config.json"):
        self.config_path = config_path
        self.devices: Dict[str, DeviceInfo] = {}
        self.tasks: Dict[str, DistributedTask] = {}
        self.results: List[CleanupResult] = []
        self._lock = threading.Lock()
        
        # Communication channel (simulated for demo)
        self.agent_port = 8765
        self.manager_socket = None
        
        # Load existing configuration
        self.load_config()
    
    def register_device(self, hostname: str, ip_address: str, 
                       credentials: Dict) -> str:
        """Register a new device to the distributed system"""
        device_id = str(uuid.uuid4())[:8]
        
        device_info = DeviceInfo(
            device_id=device_id,
            hostname=hostname,
            ip_address=ip_address,
            username=credentials.get('username', 'admin'),
            last_seen=datetime.now(),
            status=DeviceStatus.ONLINE,
            drive_capacity_gb=1000.0,  # Would be queried in production
            drive_used_gb=500.0,
            cpu_percent=25.0,
            memory_percent=45.0
        )
        
        with self._lock:
            self.devices[device_id] = device_info
        
        self.save_config()
        
        print(f"✅ Registered device '{hostname}' (ID: {device_id})")
        return device_id
    
    def scan_network(self, network_range: str = "192.168.1.0/24") -> List[str]:
        """
        Scan local network for available devices.
        In production: Uses SSH/TCP probes to discover machines.
        """
        print(f"🔍 Scanning network range: {network_range}")
        
        # Simulated scan
        discovered_devices = [
            {"id": f"dev_{i:02d}", "hostname": f"PC-{chr(65+i)}", "ip": f"192.168.1.{10+i}"}
            for i in range(5)
        ]
        
        registered_ids = []
        for dev in discovered_devices:
            self.register_device(dev['hostname'], dev['ip'], {'username': 'admin'})
            registered_ids.append(dev['id'])
        
        return registered_ids
    
    def create_cleanup_task(self, task_name: str, 
                           target_devices: List[str],
                           task_type: str = "smart_cleanup",
                           parameters: Dict = None,
                           schedule_delay_hours: int = 0) -> str:
        """Create a new distributed cleanup task"""
        
        task_id = str(uuid.uuid4())[:8]
        scheduled_time = None
        
        if schedule_delay_hours > 0:
            scheduled_time = datetime.now() + timedelta(hours=schedule_delay_hours)
        
        task = DistributedTask(
            task_id=task_id,
            name=task_name,
            task_type=task_type,
            parameters=parameters or {},
            target_devices=target_devices,
            scheduled_time=scheduled_time
        )
        
        with self._lock:
            self.tasks[task_id] = task
        
        self.save_config()
        
        if scheduled_time:
            print(f"⏰ Created scheduled task '{task_name}' for {scheduled_time}")
        else:
            print(f"⚡ Created immediate task '{task_name}' for {len(target_devices)} devices")
        
        return task_id
    
    def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute task across all target devices"""
        with self._lock:
            if task_id not in self.tasks:
                raise ValueError(f"Task {task_id} not found")
            
            task = self.tasks[task_id]
            task.status = "running"
            task.start_time = datetime.now()
        
        print(f"\n🚀 Executing task '{task.name}' ({task_id})...")
        
        results = {
            'task_id': task_id,
            'total_devices': len(task.target_devices),
            'successful': 0,
            'failed': 0,
            'total_space_freed_bytes': 0,
            'total_files_deleted': 0,
            'per_device_results': []
        }
        
        # Execute on each device (in parallel using threads)
        with ThreadPoolExecutor(max_workers=len(task.target_devices)) as executor:
            futures: Dict[Future, str] = {}
            
            for device_id in task.target_devices:
                future = executor.submit(
                    self._execute_on_device, 
                    task, 
                    device_id
                )
                futures[future] = device_id
            
            # Collect results as they complete
            for future in futures:
                device_id = futures[future]
                try:
                    result = future.result()
                    
                    with self._lock:
                        task.completed_devices += 1
                        
                        if result.success:
                            results['successful'] += 1
                            results['total_space_freed_bytes'] += result.space_freed_bytes
                            results['total_files_deleted'] += result.files_deleted
                        else:
                            task.failed_devices += 1
                            results['failed'] += 1
                    
                    results['per_device_results'].append(result.to_dict())
                    self.results.append(result)
                    
                except Exception as e:
                    error_result = CleanupResult(
                        device_id=device_id,
                        hostname=self.devices.get(device_id, DeviceInfo("", "", "", "", datetime.now(), DeviceStatus.ERROR, 0, 0, 0, 0)).hostname,
                        timestamp=datetime.now(),
                        success=False,
                        space_freed_bytes=0,
                        files_deleted=0,
                        errors=[str(e)],
                        metrics={}
                    )
                    
                    results['failed'] += 1
                    results['per_device_results'].append(error_result.to_dict())
        
        # Mark task as complete
        with self._lock:
            task.status = "completed" if results['failed'] == 0 else "partially_completed"
            task.end_time = datetime.now()
        
        print(f"\n✅ Task complete!")
        print(f"   Successful: {results['successful']}/{results['total_devices']}")
        print(f"   Total freed: {results['total_space_freed_bytes']/(1024**3):.2f} GB")
        
        return results
    
    def _execute_on_device(self, task: DistributedTask, 
                          device_id: str) -> CleanupResult:
        """Execute task on a specific device (would use SSH/API in production)"""
        
        device = self.devices.get(device_id)
        if not device:
            raise ValueError(f"Device {device_id} not registered")
        
        print(f"   📡 Communicating with {device.hostname}...")
        
        try:
            # In production: Would call remote API via SSH, REST, or gRPC
            # For demo: Generate simulated but realistic results
            
            import random
            space_freed = random.randint(100000000, 2000000000)  # 100MB - 2GB
            files_deleted = random.randint(500, 5000)
            
            result = CleanupResult(
                device_id=device_id,
                hostname=device.hostname,
                timestamp=datetime.now(),
                success=True,
                space_freed_bytes=space_freed,
                files_deleted=files_deleted,
                errors=[],
                metrics={
                    'cpu_during_cleanup': random.uniform(10, 30),
                    'memory_peak': random.uniform(60, 80),
                    'duration_seconds': random.uniform(300, 1800)
                }
            )
            
            print(f"      ✅ Freed {space_freed/(1024**3):.2f} GB on {device.hostname}")
            return result
            
        except Exception as e:
            print(f"      ❌ Error on {device.hostname}: {e}")
            return CleanupResult(
                device_id=device_id,
                hostname=device.hostname,
                timestamp=datetime.now(),
                success=False,
                space_freed_bytes=0,
                files_deleted=0,
                errors=[str(e)],
                metrics={}
            )
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get current status of entire distributed system"""
        
        online_count = sum(1 for d in self.devices.values() if d.status == DeviceStatus.ONLINE)
        total_capacity = sum(d.drive_capacity_gb for d in self.devices.values())
        total_used = sum(d.drive_used_gb for d in self.devices.values())
        
        return {
            'total_devices': len(self.devices),
            'online_devices': online_count,
            'offline_devices': len(self.devices) - online_count,
            'total_capacity_tb': total_capacity / 1024,
            'total_used_tb': total_used / 1024,
            'utilization_percent': (total_used / total_capacity * 100) if total_capacity > 0 else 0,
            'active_tasks': len([t for t in self.tasks.values() if t.status == 'running']),
            'pending_tasks': len([t for t in self.tasks.values() if t.status == 'pending']),
            'last_update': datetime.now().isoformat()
        }
    
    def generate_global_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive report across all devices"""
        
        recent_results = [
            r for r in self.results
            if (datetime.now() - r.timestamp).days <= days
        ]
        
        total_freed = sum(r.space_freed_bytes for r in recent_results if r.success)
        total_deleted = sum(r.files_deleted for r in recent_results if r.success)
        
        # Top performing device (freed most space)
        best_device = max(
            [r for r in recent_results if r.success],
            key=lambda x: x.space_freed_bytes,
            default=None
        )
        
        # Most problems device
        problematic_device = max(
            [r for r in recent_results if not r.success],
            key=lambda x: len(x.errors),
            default=None
        )
        
        return {
            'report_period_days': days,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_operations': len(recent_results),
                'successful_operations': len([r for r in recent_results if r.success]),
                'failed_operations': len([r for r in recent_results if not r.success]),
                'total_space_freed_gb': total_freed / (1024**3),
                'total_files_cleaned': total_deleted
            },
            'top_performer': best_device.to_dict() if best_device else None,
            'most_troubled_device': problematic_device.to_dict() if problematic_device else None,
            'daily_breakdown': self._generate_daily_breakdown(recent_results, days)
        }
    
    def _generate_daily_breakdown(self, results: List[CleanupResult], 
                                 days: int) -> List[Dict]:
        """Group results by day"""
        daily = defaultdict(lambda: {'freed_bytes': 0, 'count': 0, 'success': 0})
        
        for result in results:
            day_key = result.timestamp.date().isoformat()
            daily[day_key]['count'] += 1
            
            if result.success:
                daily[day_key]['freed_bytes'] += result.space_freed_bytes
                daily[day_key]['success'] += 1
        
        breakdown = [
            {
                'date': day,
                'operations': data['count'],
                'successful': data['success'],
                'space_freed_gb': data['freed_bytes'] / (1024**3)
            }
            for day, data in sorted(daily.items())
        ]
        
        return breakdown
    
    def save_config(self):
        """Persist configuration to disk"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        config_data = {
            'devices': {
                dev_id: dev.to_dict() 
                for dev_id, dev in self.devices.items()
            },
            'tasks': {
                task_id: task.to_dict()
                for task_id, task in self.tasks.items()
            },
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def load_config(self):
        """Load configuration from disk"""
        if not os.path.exists(self.config_path):
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
            
            # Reconstruct devices
            for dev_id, dev_data in config_data.get('devices', {}).items():
                dev_data['last_seen'] = datetime.fromisoformat(dev_data['last_seen'])
                self.devices[dev_id] = DeviceInfo(**dev_data)
            
            # Reconstruct tasks
            for task_id, task_data in config_data.get('tasks', {}).items():
                if task_data.get('scheduled_time'):
                    task_data['scheduled_time'] = datetime.fromisoformat(task_data['scheduled_time'])
                if task_data.get('start_time'):
                    task_data['start_time'] = datetime.fromisoformat(task_data['start_time'])
                if task_data.get('end_time'):
                    task_data['end_time'] = datetime.fromisoformat(task_data['end_time'])
                
                self.tasks[task_id] = DistributedTask(**task_data)
            
            print(f"📂 Loaded {len(self.devices)} devices and {len(self.tasks)} tasks")
            
        except Exception as e:
            print(f"❌ Error loading config: {e}")


# CLI interface
if __name__ == "__main__":
    print("🌐 EatUp Pro Distributed Cleanup Manager v3.0")
    print("=" * 60)
    
    manager = DistributedCleanupManager()
    
    # Register some test devices
    print("\n🔍 Registering test devices...")
    device_ids = manager.scan_network()
    
    # Get system status
    status = manager.get_network_status()
    print(f"\n📊 Network Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Create a task
    print("\n📝 Creating cleanup task...")
    task_id = manager.create_cleanup_task(
        name="Network-wide deep clean",
        target_devices=device_ids,
        task_type="smart_cleanup",
        schedule_delay_hours=2
    )
    
    # Show global report
    print("\n📈 Generating global report...")
    report = manager.generate_global_report(days=7)
    print(json.dumps(report, indent=2, default=str))

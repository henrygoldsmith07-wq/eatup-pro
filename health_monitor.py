#!/usr/bin/env python3
"""
EatUp Pro v8.1+ - Health & Performance Monitoring
Real-time system health tracking with predictive alerts
"""

import os
import sys
import json
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import deque
import statistics


class HealthMonitor:
    """Comprehensive system health monitoring with anomaly detection"""
    
    def __init__(self):
        self.metrics_window = 60  # Seconds
        self.data_buffer = deque(maxlen=1000)
        self.alerts: List[Dict] = []
        self.callbacks: List[Callable] = []
        
        self.thresholds = {
            'cpu_critical': 95,
            'cpu_warning': 85,
            'memory_critical': 95,
            'memory_warning': 85,
            'disk_critical': 95,
            'disk_warning': 85,
            'temp_critical': 85,
            'temp_warning': 75
        }
    
    def start_monitoring(self, interval: float = 5.0):
        """Start background monitoring thread"""
        print(f"📊 Starting health monitor (interval: {interval}s)...")
        
        def monitor_loop():
            while True:
                metrics = self.capture_metrics()
                self.data_buffer.append(metrics)
                
                # Check for anomalies
                if self._check_anomalies(metrics):
                    self._trigger_alert(metrics)
                
                # Call registered callbacks
                for callback in self.callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        print(f"Callback error: {e}")
                
                time.sleep(interval)
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        
        return thread
    
    def capture_metrics(self) -> Dict[str, Any]:
        """Capture comprehensive system metrics"""
        import psutil
        
        # CPU metrics
        cpu_times = psutil.cpu_times_percent()
        cpu_freq = psutil.cpu_freq()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk_io = psutil.disk_io_counters()
        partitions = [p for p in psutil.disk_partitions()][:3]
        
        # Network metrics
        net_io = psutil.net_io_counters()
        
        # Processes
        process_count = len(list(psutil.process_iter()))
        
        # Load average (if available)
        try:
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else None
        except OSError:
            load_avg = None
        
        return {
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': psutil.boot_time(),
            'cpu': {
                'percent_user': round(cpu_times.user, 1),
                'percent_system': round(cpu_times.system, 1),
                'percent_idle': round(cpu_times.idle, 1),
                'percent_iowait': round(getattr(cpu_times, 'iowait', 0), 1),
                'frequency_mhz': round(cpu_freq.current if cpu_freq else 0, 2),
                'load_average': list(load_avg) if load_avg else None
            },
            'memory': {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_percent': round(memory.percent, 1),
                'used_gb': round(memory.used / (1024**3), 2),
                'cached_gb': round(getattr(memory, 'cached', 0) / (1024**3), 2),
                'swap_total_gb': round(psutil.swap_memory().total / (1024**3), 2),
                'swap_used_percent': round(psutil.swap_memory().percent, 1)
            },
            'disk_io': {
                'bytes_read': disk_io.read_bytes if disk_io else 0,
                'bytes_written': disk_io.write_bytes if disk_io else 0,
                'read_count': disk_io.read_count if disk_io else 0,
                'write_count': disk_io.write_count if disk_io else 0
            },
            'network': {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errors_in': getattr(net_io, 'errin', 0),
                'errors_out': getattr(net_io, 'errout', 0)
            },
            'processes': {
                'count': process_count,
                'threads': psutil.count_threads() if hasattr(psutil, 'count_threads') else None
            },
            'partitions': [
                {
                    'device': p.device,
                    'mountpoint': p.mountpoint,
                    'total_gb': round(p.size / (1024**3), 2),
                    'free_gb': round(p.free / (1024**3), 2)
                }
                for p in partitions
            ]
        }
    
    def _check_anomalies(self, metrics: Dict) -> bool:
        """Check for threshold violations"""
        has_alerts = False
        
        # CPU checks
        cpu_usage = metrics['cpu']['percent_user'] + metrics['cpu']['percent_system']
        if cpu_usage > self.thresholds['cpu_critical']:
            self.add_alert('CRITICAL', 'High CPU Usage', 
                          f'CPU at {round(cpu_usage)}%', metrics)
            has_alerts = True
        elif cpu_usage > self.thresholds['cpu_warning']:
            self.add_alert('WARNING', 'Elevated CPU Usage',
                          f'CPU at {round(cpu_usage)}%', metrics)
            has_alerts = True
        
        # Memory checks
        mem_percent = metrics['memory']['used_percent']
        if mem_percent > self.thresholds['memory_critical']:
            self.add_alert('CRITICAL', 'Critical Memory Usage',
                          f'Memory at {round(mem_percent)}%', metrics)
            has_alerts = True
        elif mem_percent > self.thresholds['memory_warning']:
            self.add_alert('WARNING', 'High Memory Usage',
                          f'Memory at {round(mem_percent)}%', metrics)
            has_alerts = True
        
        # Disk checks
        for partition in metrics.get('partitions', []):
            if partition['total_gb'] > 0:
                usage_pct = ((partition['total_gb'] - partition['free_gb']) / 
                            partition['total_gb']) * 100
                
                if usage_pct > self.thresholds['disk_critical']:
                    self.add_alert('CRITICAL', 'Disk Space Critical',
                                  f'{partition["mountpoint"]} at {round(usage_pct)}%', metrics)
                    has_alerts = True
                elif usage_pct > self.thresholds['disk_warning']:
                    self.add_alert('WARNING', 'Low Disk Space',
                                  f'{partition["mountpoint"]} at {round(usage_pct)}%', metrics)
                    has_alerts = True
        
        return has_alerts
    
    def add_alert(self, level: str, title: str, message: str, context: Dict):
        """Add alert to queue"""
        alert = {
            'level': level,
            'title': title,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'context': context
        }
        
        self.alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        print(f"🚨 [{level}] {title}: {message}")
    
    def _trigger_alert(self, metrics: Dict):
        """Trigger callback alerts"""
        pass  # Would integrate with notification system
    
    def register_callback(self, callback: Callable[[Dict], None]):
        """Register callback for metric updates"""
        self.callbacks.append(callback)
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current system status summary"""
        if not self.data_buffer:
            return {'status': 'no_data'}
        
        latest = self.data_buffer[-1]
        
        return {
            'status': 'healthy',
            'last_check': latest['timestamp'],
            'cpu_usage': round(
                latest['cpu']['percent_user'] + latest['cpu']['percent_system'], 1
            ),
            'memory_usage': latest['memory']['used_percent'],
            'active_alerts': len([a for a in self.alerts 
                                if a['level'] == 'CRITICAL']),
            'warning_alerts': len([a for a in self.alerts 
                                  if a['level'] == 'WARNING']),
            'uptime_hours': round(time.time() - latest['uptime_seconds'], 1)
        }
    
    def get_health_trend(self, samples: int = 10) -> Dict[str, Any]:
        """Analyze health trends over recent samples"""
        if len(self.data_buffer) < samples:
            return {'error': 'Insufficient data'}
        
        recent = list(self.data_buffer)[-samples:]
        
        # Calculate statistics
        cpu_values = [
            m['cpu']['percent_user'] + m['cpu']['percent_system'] 
            for m in recent
        ]
        
        mem_values = [m['memory']['used_percent'] for m in recent]
        
        return {
            'sample_count': len(recent),
            'cpu': {
                'average': round(statistics.mean(cpu_values), 1),
                'min': round(min(cpu_values), 1),
                'max': round(max(cpu_values), 1),
                'std_dev': round(statistics.stdev(cpu_values), 1) if len(cpu_values) > 1 else 0,
                'trend': self._calculate_trend(cpu_values)
            },
            'memory': {
                'average': round(statistics.mean(mem_values), 1),
                'min': round(min(mem_values), 1),
                'max': round(max(mem_values), 1),
                'std_dev': round(statistics.stdev(mem_values), 1) if len(mem_values) > 1 else 0,
                'trend': self._calculate_trend(mem_values)
            }
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return 'stable'
        
        first_half = statistics.mean(values[:len(values)//2])
        second_half = statistics.mean(values[len(values)//2:])
        
        diff = second_half - first_half
        
        if abs(diff) < 5:
            return 'stable'
        elif diff > 0:
            return 'increasing'
        else:
            return 'decreasing'
    
    def generate_report(self) -> str:
        """Generate comprehensive health report"""
        status = self.get_current_status()
        trend = self.get_health_trend()
        
        report = f"""
{'='*60}
💚 SYSTEM HEALTH REPORT - EatUp Pro v8.1+
{'='*60}

CURRENT STATUS:
  • Overall: {status['status'].upper()}
  • CPU Usage: {status['cpu_usage']}%
  • Memory Usage: {status['memory_usage']}%
  • Active Alerts: {status['active_alerts']} CRITICAL, {status['warning_alerts']} WARNING
  • Uptime: {status['uptime_hours']} hours

HEALTH TRENDS (Last {trend['sample_count']} samples):

CPU Analysis:
  • Average: {trend['cpu']['average']}%
  • Range: {trend['cpu']['min']}% - {trend['cpu']['max']}%
  • Variability: ±{trend['cpu']['std_dev']}%
  • Trend: {trend['cpu']['trend'].upper()}

Memory Analysis:
  • Average: {trend['memory']['average']}%
  • Range: {trend['memory']['min']}% - {trend['memory']['max']}%
  • Variability: ±{trend['memory']['std_dev']}%
  • Trend: {trend['memory']['trend'].upper()}

RECOMMENDATIONS:
"""
        
        if trend['cpu']['trend'] == 'increasing':
            report += "  ⚠️  CPU usage trending upward - investigate high-consumption processes\n"
        
        if status['active_alerts'] > 0:
            report += f"  🚨 Address {status['active_alerts']} critical alerts immediately\n"
        
        if trend['memory']['trend'] == 'increasing':
            report += "  ⚠️  Memory usage growing - consider optimization\n"
        
        if status['status'] == 'healthy':
            report += "  ✅ System operating normally\n"
        
        report += "\n" + "="*60
        
        return report


# Demo mode
if __name__ == '__main__':
    monitor = HealthMonitor()
    
    # Start monitoring
    monitor.start_monitoring(interval=2.0)
    
    # Wait for some data
    time.sleep(5)
    
    # Generate report
    report = monitor.generate_report()
    print(report)

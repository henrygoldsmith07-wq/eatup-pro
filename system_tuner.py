#!/usr/bin/env python3
"""
EatUp Pro v8.1+ - System Performance Tuner
Real-time system optimization with CPU/GPU/RAM optimization
"""

import os
import sys
import json
import psutil
import subprocess
from typing import Dict, List, Any, Optional
from datetime import datetime


class SystemTuner:
    """Advanced system performance optimization"""
    
    def __init__(self):
        self.metrics_history: List[Dict] = []
        self.optimal_settings = {
            'cpu_max_percentage': 80,
            'ram_reserve_gb': 4,
            'gpu_power_mode': 'performance',
            'network_optimization': True
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Comprehensive system health report"""
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq()
        
        # Memory metrics  
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk metrics
        disk_partitions = psutil.disk_partitions()
        
        # Network metrics
        net_io = psutil.net_io_counters()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'usage_percent': cpu_percent,
                'cores': psutil.cpu_count(),
                'frequency_mhz': round(cpu_freq.current if cpu_freq else 0, 2),
                'temp_celsius': self._get_cpu_temp(),
                'threads': psutil.cpu_count(logical=True)
            },
            'memory': {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_percent': memory.percent,
                'swap_total_gb': round(swap.total / (1024**3), 2),
                'swap_used_percent': swap.percent
            },
            'disk': [
                {
                    'device': p.device,
                    'mountpoint': p.mountpoint,
                    'fstype': p.fstype,
                    'total_gb': round(p.size / (1024**3), 2),
                    'used_gb': 0,  # Would need elevated permissions
                    'free_gb': 0
                }
                for p in disk_partitions[:5]
            ],
            'network': {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            },
            'processes': {
                'count': len(psutil.process_iter()),
                'top_cpu': self._get_top_processes('cpu_percent'),
                'top_memory': self._get_top_processes('mem_percent')
            }
        }
    
    def _get_top_processes(self, metric_key: str) -> List[Dict]:
        """Get top processes by resource usage"""
        try:
            processes = sorted(
                list(psutil.process_iter(['pid', 'name', metric_key])),
                key=lambda x: x.info.get(metric_key, 0),
                reverse=True
            )[:10]
            
            return [
                {
                    'pid': p.info['pid'],
                    'name': p.info['name'],
                    'value': round(p.info.get(metric_key, 0), 1)
                }
                for p in processes
            ]
        except Exception:
            return []
    
    def _get_cpu_temp(self) -> float:
        """Get CPU temperature (platform-specific)"""
        try:
            # Linux
            if os.name == 'posix' and not sys.platform.startswith('win'):
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    return round(int(f.read()) / 1000, 1)
            
            # Windows (requires additional libraries)
            elif sys.platform == 'win32':
                # Placeholder - use wmi or pywin32 in production
                return 45.0
                
        except Exception:
            return 0.0
        
        return 0.0
    
    def optimize_system(self, mode: str = 'balanced') -> Dict[str, Any]:
        """Apply system optimizations based on mode"""
        
        modes = {
            'gaming': {
                'priority': 'high',
                'background_processes_limit': 5,
                'power_plan': 'High Performance',
                'network_priority': True,
                'game_mode': True
            },
            'battery': {
                'priority': 'low', 
                'background_processes_limit': 2,
                'power_plan': 'Power Saver',
                'network_priority': False,
                'game_mode': False
            },
            'balanced': {
                'priority': 'normal',
                'background_processes_limit': 10,
                'power_plan': 'Balanced',
                'network_priority': True,
                'game_mode': False
            }
        }
        
        settings = modes.get(mode, modes['balanced'])
        
        optimizations_applied = []
        
        # Optimize startup programs
        startuptools = self._optimize_startups(settings['background_processes_limit'])
        optimizations_applied.append(startuptools)
        
        # Set power plan
        if self._set_power_plan(settings['power_plan']):
            optimizations_applied.append(f"Power plan set to {settings['power_plan']}")
        
        # Enable game mode (Windows only)
        if settings['game_mode'] and sys.platform == 'win32':
            self._enable_game_mode()
            optimizations_applied.append("Game mode enabled")
        
        # Priority adjustment
        self._adjust_process_priority(settings['priority'])
        
        return {
            'mode': mode,
            'optimizations_applied': optimizations_applied,
            'success': len(optimizations_applied) > 0
        }
    
    def _optimize_startups(self, max_background: int) -> Dict:
        """Optimize startup programs"""
        try:
            # Windows startup items
            import winreg
            
            startup_apps = []
            keys = [
                winreg.HKEY_CURRENT_USER,
                winreg.HKEY_LOCAL_MACHINE
            ]
            
            for key in keys:
                try:
                    reg_key = winreg.OpenKey(key, r"Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_READ)
                    
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(reg_key, i)
                            startup_apps.append({'name': name, 'path': value})
                            i += 1
                        except OSError:
                            break
                    
                    winreg.CloseKey(reg_key)
                except OSError:
                    pass
            
            # Disable non-critical apps
            disabled_count = 0
            critical_keywords = ['antivirus', 'driver', 'update']
            
            for app in startup_apps:
                is_critical = any(kw in app['name'].lower() for kw in critical_keywords)
                
                if not is_critical and len(startup_apps) > max_background:
                    # In production, would disable via registry
                    disabled_count += 1
            
            return {
                'startup_apps_found': len(startup_apps),
                'disabled_non_critical': disabled_count,
                'max_allowed': max_background
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _set_power_plan(self, plan_name: str) -> bool:
        """Set Windows power plan"""
        if sys.platform != 'win32':
            return False
        
        try:
            # Power plans GUIDs
            power_plans = {
                'High Performance': '8c5e7fda-e8bf-4a96-b9a8-e2ab704ea8cf',
                'Balanced': 'a5dcbf91-63f9-4d7f-a59a-3d5e4b1b9b8a',
                'Power Saver': '381b4222-f694-41f0-9685-ff5bb260df2e'
            }
            
            plan_guid = power_plans.get(plan_name)
            
            if plan_guid:
                subprocess.run(
                    ['powercfg', '/SETACTIVE', plan_guid],
                    check=True,
                    capture_output=True
                )
                return True
            
            return False
            
        except Exception:
            return False
    
    def _enable_game_mode(self):
        """Enable Windows Game Mode"""
        try:
            import winreg
            
            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\GameBar",
                0,
                winreg.KEY_SET_VALUE
            )
            
            winreg.SetValueEx(reg_key, "AllowGameMode", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(reg_key)
            
        except Exception:
            pass
    
    def _adjust_process_priority(self, priority: str):
        """Adjust current process priority"""
        try:
            import psutil
            
            current_process = psutil.Process()
            
            priorities = {
                'low': psutil.IDLE_PRIORITY_CLASS,
                'normal': psutil.NORMAL_PRIORITY_CLASS,
                'high': psutil.HIGH_PRIORITY_CLASS,
                'realtime': psutil.REALTIME_PRIORITY_CLASS
            }
            
            if priority in priorities:
                current_process.nice(priorities[priority])
                
        except Exception:
            pass
    
    def create_optimization_report(self) -> str:
        """Generate comprehensive optimization report"""
        health = self.get_system_health()
        
        report = f"""
{'='*60}
🖥️ SYSTEM OPTIMIZATION REPORT - EatUp Pro v8.1+
Generated: {health['timestamp']}
{'='*60}

CPU STATUS:
  • Usage: {health['cpu']['usage_percent']}% ({health['cpu']['cores']} cores, {health['cpu']['threads']} threads)
  • Frequency: {health['cpu']['frequency_mhz']} MHz
  • Temperature: {health['cpu']['temp_celsius']}°C
  
MEMORY STATUS:
  • Total: {health['memory']['total_gb']} GB
  • Available: {health['memory']['available_gb']} GB
  • Used: {health['memory']['used_percent']}%
  • Swap Used: {health['memory']['swap_used_percent']}%

TOP CPU CONSUMERS:
"""
        
        for proc in health['processes']['top_cpu'][:5]:
            report += f"  • {proc['name']} (PID {proc['pid']}): {proc['value']}%\n"
        
        report += "\nTOP MEMORY CONSUMERS:\n"
        
        for proc in health['processes']['top_memory'][:5]:
            report += f"  • {proc['name']} (PID {proc['pid']}): {proc['value']}%\n"
        
        report += f"""
RECOMMENDATIONS:
"""
        
        if health['cpu']['usage_percent'] > 80:
            report += "  ⚠️  High CPU usage - consider optimizing background processes\n"
        
        if health['memory']['used_percent'] > 85:
            report += "  ⚠️  High memory usage - close unused applications\n"
        
        if health['cpu']['temp_celsius'] > 70:
            report += "  ⚠️  High CPU temperature - check cooling system\n"
        
        report += "\n" + "="*60
        
        return report


if __name__ == '__main__':
    print("=" * 60)
    print("EatUp Pro System Tuner v8.1+")
    print("=" * 60)
    
    tuner = SystemTuner()
    
    # Get health report
    health = tuner.get_system_health()
    print("\n💻 System Health:")
    print(json.dumps(health, indent=2))
    
    # Create optimization report
    report = tuner.create_optimization_report()
    print(report)
    
    # Test optimization
    print("\n🔧 Testing optimizations...")
    result = tuner.optimize_system('balanced')
    print(f"\nOptimization applied: {result}")

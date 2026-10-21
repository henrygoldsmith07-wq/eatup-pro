"""
EatUp Pro - Real-Time Disk Monitor
WebSocket-based live disk usage monitoring with animated visualizations
"""

import os
import time
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Callable, List
import psutil


class RealTimeMonitor:
    """Real-time disk usage monitor with event notifications"""
    
    def __init__(self, update_interval: float = 1.0):
        self.update_interval = update_interval
        self.running = False
        self.monitoring_thread = None
        self.callbacks: List[Callable] = []
        self.history = []
        self.max_history_size = 3600  # Store last hour of data
        
    def start_monitoring(self, drives: List[str] = None):
        """Start real-time monitoring in background thread"""
        
        if drives is None:
            drives = ['C:']
        
        self.running = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(drives,),
            daemon=True
        )
        self.monitoring_thread.start()
        
        print(f"✅ Real-time monitoring started for {drives}")
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        print("⏹️ Monitoring stopped")
    
    def _monitoring_loop(self, drives: List[str]):
        """Background monitoring loop"""
        
        while self.running:
            try:
                # Get current status for all monitored drives
                for drive in drives:
                    status = self._get_disk_status(drive)
                    
                    # Store in history
                    self.history.append({
                        'timestamp': datetime.now().isoformat(),
                        'drive': drive,
                        **status
                    })
                    
                    # Trim old data
                    if len(self.history) > self.max_history_size:
                        self.history = self.history[-self.max_history_size:]
                    
                    # Notify callbacks
                    for callback in self.callbacks:
                        try:
                            callback(drive, status)
                        except Exception as e:
                            print(f"Callback error: {e}")
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(self.update_interval)
    
    def _get_disk_status(self, drive: str) -> Dict[str, Any]:
        """Get current disk status for a drive"""
        
        try:
            usage = psutil.disk_usage(drive)
            
            return {
                'total_bytes': usage.total,
                'used_bytes': usage.used,
                'free_bytes': usage.free,
                'percent_used': usage.percent,
                'total_gb': usage.total / (1024**3),
                'used_gb': usage.used / (1024**3),
                'free_gb': usage.free / (1024**3)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'total_gb': 0,
                'used_gb': 0,
                'free_gb': 0,
                'percent_used': 0
            }
    
    def on_status_change(self, callback: Callable):
        """Register callback for status changes"""
        self.callbacks.append(callback)
    
    def get_trends(self, minutes: int = 60) -> Dict[str, Any]:
        """Calculate trends from recent history"""
        
        cutoff_time = datetime.now().timestamp() - (minutes * 60)
        recent_data = [
            item for item in self.history
            if datetime.fromisoformat(item['timestamp']).timestamp() > cutoff_time
        ]
        
        if len(recent_data) < 2:
            return {
                'trend_direction': 'stable',
                'growth_rate_gb_per_hour': 0,
                'peak_usage_percent': 0,
                'lowest_usage_percent': 0,
                'average_usage_percent': 0
            }
        
        # Sort by timestamp
        recent_data.sort(key=lambda x: x['timestamp'])
        
        first = recent_data[0]
        last = recent_data[-1]
        
        # Calculate growth rate
        time_delta_minutes = minutes
        used_delta_gb = (last['used_gb'] - first['used_gb'])
        
        growth_rate_gb_per_hour = (used_delta_gb / time_delta_minutes) * 60
        
        # Determine trend
        if growth_rate_gb_per_hour > 5:
            direction = 'increasing'
        elif growth_rate_gb_per_hour < -5:
            direction = 'decreasing'
        else:
            direction = 'stable'
        
        return {
            'trend_direction': direction,
            'growth_rate_gb_per_hour': round(growth_rate_gb_per_hour, 3),
            'peak_usage_percent': max(d['percent_used'] for d in recent_data),
            'lowest_usage_percent': min(d['percent_used'] for d in recent_data),
            'average_usage_percent': sum(d['percent_used'] for d in recent_data) / len(recent_data)
        }
    
    def predict_space_exhaustion(self, days: int = 30) -> Dict[str, Any]:
        """Predict when drive will run out of space based on growth rate"""
        
        trends = self.get_trends(minutes=60)  # Last hour
        
        if trends['growth_rate_gb_per_hour'] <= 0:
            return {
                'will_run_out': False,
                'days_until_full': None,
                'reason': 'No positive growth detected'
            }
        
        free_gb = 100  # Assume fresh scan data available
        
        # Days until full
        daily_growth = trends['growth_rate_gb_per_hour'] * 24
        days_until_full = free_gb / daily_growth if daily_growth > 0 else float('inf')
        
        return {
            'will_run_out': days_until_full <= days,
            'days_until_full': round(days_until_full, 1),
            'daily_growth_gb': round(daily_growth, 2),
            'recommendation': 'Clean up now!' if days_until_full < 7 else 'Monitor regularly'
        }


# WebSockets integration (Flask-SocketIO)
try:
    from flask_socketio import SocketIO, emit
    
    class WebSocketMonitor:
        """WebSocket endpoint for real-time updates"""
        
        def __init__(self, socketio: SocketIO, monitor: RealTimeMonitor):
            self.socketio = socketio
            self.monitor = monitor
            
            # Register callbacks
            self.monitor.on_status_change(self._broadcast_update)
            
        def _broadcast_update(self, drive, status):
            """Broadcast disk status to connected clients"""
            
            self.socketio.emit('disk_update', {
                'drive': drive,
                'timestamp': datetime.now().isoformat(),
                **status
            }, namespace='/disk')
        
        def start_listening(self):
            """Start listening for client connections"""
            
            @self.socketio.on('connect', namespace='/disk')
            def on_connect():
                print('Client connected to disk monitoring')
                emit('status', {'message': 'Connected'})
            
            @self.socketio.on('disconnect', namespace='/disk')
            def on_disconnect():
                print('Client disconnected from disk monitoring')
            
            print("✅ WebSocket server ready for disk monitoring")

except ImportError:
    print("Flask-SocketIO not installed. Real-time websockets disabled.")
    WebSocketMonitor = None


if __name__ == "__main__":
    import json
    
    # Test the monitor
    monitor = RealTimeMonitor(update_interval=2.0)
    
    def on_update(drive, status):
        print(f"\r{drive}: {status['percent_used']:.1f}% used", end='', flush=True)
    
    monitor.on_status_change(on_update)
    monitor.start_monitoring(['C:'])
    
    # Run for 30 seconds then show stats
    time.sleep(30)
    
    print("\n\nTrends:")
    trends = monitor.get_trends(minutes=30)
    print(json.dumps(trends, indent=2))
    
    print("\nPrediction:")
    prediction = monitor.predict_space_exhaustion(days=30)
    print(json.dumps(prediction, indent=2))
    
    monitor.stop_monitoring()

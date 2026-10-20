"""
EatUp Pro - SQLite Analytics Database
Handles persistent storage of scan history, cleanup operations, and AI recommendations
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class AnalyticsDatabase:
    """SQLite database for storing analytics and historical data"""
    
    def __init__(self, db_path: str = "data/analytics.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Scans table - stores each drive scan result
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scans (
                id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                drive TEXT NOT NULL,
                total_used_bytes INTEGER NOT NULL,
                total_space_bytes INTEGER NOT NULL,
                utilization_percent REAL,
                categories_json TEXT,  -- JSON object of category sizes
                temp_files_count INTEGER,
                duplicate_groups_count INTEGER,
                large_files_count INTEGER,
                cleanable_bytes INTEGER,
                scan_duration_seconds REAL,
                status TEXT DEFAULT 'completed'
            )
        ''')
        
        # Cleanup_history table - tracks all cleanup operations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cleanup_history (
                id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                scan_id TEXT REFERENCES scans(id),
                cleanup_type TEXT NOT NULL,  -- temp, duplicates, large, smart
                files_deleted INTEGER DEFAULT 0,
                space_freed_bytes INTEGER DEFAULT 0,
                duration_seconds REAL,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT
            )
        ''')
        
        # Recommendations table - AI suggestions and user decisions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommendations (
                id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                scan_id TEXT REFERENCES scans(id),
                filepath TEXT NOT NULL,
                category TEXT,
                size_bytes INTEGER,
                age_days INTEGER,
                safety_score REAL,
                action TEXT NOT NULL,  -- delete, keep, review, archive
                confidence REAL,
                reason TEXT,
                risk_level TEXT,  -- safe, moderate, risky
                user_decision TEXT,  -- actual user choice (delete/keep/skip)
                user_decision_at DATETIME
            )
        ''')
        
        # User_preferences table - stores user settings and preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Trends_cache table - pre-computed trend data for fast dashboard loading
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trends_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calculation_date DATE DEFAULT CURRENT_DATE,
                daily_growth_mb REAL,
                weekly_growth_mb REAL,
                monthly_growth_mb REAL,
                peak_usage_date DATE,
                lowest_usage_date DATE,
                average_utilization REAL,
                prediction_next_30_days_mb REAL
            )
        ''')
        
        self.conn.commit()
        print("✅ Database initialized successfully")
    
    # ==================== SCAN MANAGEMENT ====================
    
    def save_scan(self, scan_data: Dict[str, Any], duration: float = None):
        """Save a scan result to the database"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO scans (id, drive, total_used_bytes, total_space_bytes, 
                             utilization_percent, categories_json, temp_files_count,
                             duplicate_groups_count, large_files_count, cleanable_bytes,
                             scan_duration_seconds, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            scan_data.get('scan_id'),
            scan_data.get('drive', 'C:'),
            scan_data.get('total_used_bytes'),
            scan_data.get('total_space_bytes'),
            scan_data.get('utilization_percent'),
            scan_data.get('categories_json'),
            scan_data.get('temp_files_count'),
            scan_data.get('duplicate_groups_count'),
            scan_data.get('large_files_count'),
            scan_data.get('cleanable_bytes'),
            duration,
            scan_data.get('status', 'completed')
        ))
        
        self.conn.commit()
        return scan_data.get('scan_id')
    
    def get_recent_scans(self, limit: int = 10) -> List[Dict]:
        """Get recent scan history"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM scans ORDER BY timestamp DESC LIMIT ?
        ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_scan_by_id(self, scan_id: str) -> Optional[Dict]:
        """Get a specific scan by ID"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM scans WHERE id = ?', (scan_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # ==================== CLEANUP HISTORY ====================
    
    def record_cleanup(self, cleanup_data: Dict[str, Any]) -> str:
        """Record a cleanup operation"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO cleanup_history (id, scan_id, cleanup_type, files_deleted,
                                       space_freed_bytes, duration_seconds, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            cleanup_data.get('cleanup_id'),
            cleanup_data.get('scan_id'),
            cleanup_data.get('cleanup_type'),
            cleanup_data.get('files_deleted', 0),
            cleanup_data.get('space_freed_bytes', 0),
            cleanup_data.get('duration_seconds'),
            cleanup_data.get('success', True),
            cleanup_data.get('error_message')
        ))
        
        self.conn.commit()
        return cleanup_data.get('cleanup_id')
    
    def get_cleanup_history(self, limit: int = 20) -> List[Dict]:
        """Get recent cleanup operations"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT ch.*, s.total_used_bytes as post_cleanup_usage
            FROM cleanup_history ch
            LEFT JOIN scans s ON ch.scan_id = s.id
            ORDER BY ch.timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_total_space_saved(self, days: int = 30) -> int:
        """Calculate total space saved over last N days"""
        cursor = self.conn.cursor()
        cutoff_date = (datetime.now().timestamp() - (days * 86400))
        
        cursor.execute('''
            SELECT SUM(space_freed_bytes) as total_saved
            FROM cleanup_history
            WHERE timestamp > datetime(?, 'unixepoch')
        ''', (cutoff_date,))
        
        row = cursor.fetchone()
        return row['total_saved'] or 0
    
    # ==================== RECOMMENDATIONS ====================
    
    def save_recommendation(self, rec_data: Dict[str, Any]) -> str:
        """Save an AI recommendation"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO recommendations (id, scan_id, filepath, category, size_bytes,
                                        age_days, safety_score, action, confidence,
                                        reason, risk_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rec_data.get('recommendation_id'),
            rec_data.get('scan_id'),
            rec_data.get('filepath'),
            rec_data.get('category'),
            rec_data.get('size_bytes'),
            rec_data.get('age_days'),
            rec_data.get('safety_score'),
            rec_data.get('action'),
            rec_data.get('confidence'),
            rec_data.get('reason'),
            rec_data.get('risk_level')
        ))
        
        self.conn.commit()
        return rec_data.get('recommendation_id')
    
    def update_user_decision(self, recommendation_id: str, decision: str):
        """Record user's decision on a recommendation"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE recommendations SET user_decision = ?, user_decision_at = ?
            WHERE id = ?
        ''', (decision, datetime.now().isoformat(), recommendation_id))
        self.conn.commit()
    
    def get_recommendations_for_scan(self, scan_id: str) -> List[Dict]:
        """Get all recommendations for a specific scan"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM recommendations WHERE scan_id = ? ORDER BY safety_score ASC
        ''', (scan_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # ==================== USER PREFERENCES ====================
    
    def save_preference(self, key: str, value: Any):
        """Save user preference"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', (key, json.dumps(value) if not isinstance(value, str) else value, datetime.now().isoformat()))
        self.conn.commit()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM user_preferences WHERE key = ?', (key,))
        row = cursor.fetchone()
        
        if row:
            try:
                return json.loads(row['value'])
            except (json.JSONDecodeError, TypeError):
                return row['value']
        return default
    
    # ==================== TREND ANALYSIS ====================
    
    def calculate_trends(self, days: int = 90) -> Dict[str, Any]:
        """Calculate storage usage trends"""
        cursor = self.conn.cursor()
        cutoff_date = (datetime.now().timestamp() - (days * 86400))
        
        # Get all scans in date range
        cursor.execute('''
            SELECT timestamp, total_used_bytes, utilization_percent
            FROM scans
            WHERE timestamp > datetime(?, 'unixepoch')
            ORDER BY timestamp ASC
        ''', (cutoff_date,))
        
        scans = [dict(row) for row in cursor.fetchall()]
        
        if len(scans) < 2:
            return {
                'daily_growth_mb': 0,
                'weekly_growth_mb': 0,
                'monthly_growth_mb': 0,
                'trend_direction': 'stable',
                'average_utilization': 0,
                'data_points': 0
            }
        
        # Calculate growth rates
        first_scan = scans[0]
        last_scan = scans[-1]
        
        days_span = (datetime.fromisoformat(last_scan['timestamp']).timestamp() -
                    datetime.fromisoformat(first_scan['timestamp']).timestamp()) / 86400
        
        used_delta = (last_scan['total_used_bytes'] - first_scan['total_used_bytes']) / (1024**2)
        
        daily_growth = used_delta / max(1, days_span)
        weekly_growth = daily_growth * 7
        monthly_growth = daily_growth * 30
        
        # Determine trend direction
        if daily_growth > 100:  # > 100MB/day growth
            trend_direction = 'increasing'
        elif daily_growth < -100:
            trend_direction = 'decreasing'
        else:
            trend_direction = 'stable'
        
        # Calculate average utilization
        avg_util = sum(s['utilization_percent'] for s in scans) / len(scans)
        
        # Find peak and low dates
        peak = max(scans, key=lambda x: x['utilization_percent'])
        low = min(scans, key=lambda x: x['utilization_percent'])
        
        # Predict next 30 days (linear projection)
        predicted_growth = daily_growth * 30
        
        return {
            'daily_growth_mb': round(daily_growth, 2),
            'weekly_growth_mb': round(weekly_growth, 2),
            'monthly_growth_mb': round(monthly_growth, 2),
            'trend_direction': trend_direction,
            'average_utilization': round(avg_util, 2),
            'peak_usage_date': peak['timestamp'],
            'lowest_usage_date': low['timestamp'],
            'prediction_next_30_days_mb': round(predicted_growth, 2),
            'data_points': len(scans)
        }
    
    def cache_trends(self, trends: Dict[str, Any]):
        """Cache computed trends for fast dashboard loading"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO trends_cache (calculation_date, daily_growth_mb, weekly_growth_mb,
                                     monthly_growth_mb, average_utilization, prediction_next_30_days_mb)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().date(),
            trends.get('daily_growth_mb'),
            trends.get('weekly_growth_mb'),
            trends.get('monthly_growth_mb'),
            trends.get('average_utilization'),
            trends.get('prediction_next_30_days_mb')
        ))
        
        self.conn.commit()
    
    def get_cached_trends(self, max_age_hours: int = 24) -> Optional[Dict]:
        """Get cached trends if still fresh"""
        cursor = self.conn.cursor()
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        
        cursor.execute('''
            SELECT * FROM trends_cache
            WHERE calculation_date > datetime(?, 'unixepoch')
            ORDER BY id DESC
            LIMIT 1
        ''', (cutoff,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # ==================== STATISTICS ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about app usage"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total scans performed
        cursor.execute('SELECT COUNT(*) as count FROM scans')
        stats['total_scans'] = cursor.fetchone()['count']
        
        # Total cleanup operations
        cursor.execute('SELECT COUNT(*) as count FROM cleanup_history')
        stats['total_cleanups'] = cursor.fetchone()['count']
        
        # Total space freed
        cursor.execute('SELECT SUM(space_freed_bytes) as total FROM cleanup_history')
        stats['total_space_freed_mb'] = cursor.fetchone()['total'] / (1024 ** 2)
        
        # Total recommendations generated
        cursor.execute('SELECT COUNT(*) as count FROM recommendations')
        stats['total_recommendations'] = cursor.fetchone()['count']
        
        # Recommendation acceptance rate
        cursor.execute('''
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN user_decision = 'delete' THEN 1 ELSE 0 END) as deleted
            FROM recommendations WHERE user_decision IS NOT NULL
        ''')
        row = cursor.fetchone()
        if row['total'] > 0:
            stats['recommendation_acceptance_rate'] = round(
                (row['deleted'] / row['total']) * 100, 1
            )
        else:
            stats['recommendation_acceptance_rate'] = 0
        
        return stats
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# Import at module level
import json


if __name__ == "__main__":
    # Test the database
    db = AnalyticsDatabase()
    
    # Test saving a scan
    test_scan = {
        'scan_id': 'test_001',
        'drive': 'C:',
        'total_used_bytes': 500_000_000_000,
        'total_space_bytes': 1000_000_000_000,
        'utilization_percent': 50.0,
        'categories_json': '{"Documents": 200, "Videos": 150, "Other": 150}',
        'temp_files_count': 500,
        'duplicate_groups_count': 10,
        'large_files_count': 25,
        'cleanable_bytes': 50_000_000_000
    }
    
    scan_id = db.save_scan(test_scan)
    print(f"Saved scan: {scan_id}")
    
    # Get recent scans
    recent = db.get_recent_scans()
    print(f"Recent scans: {len(recent)}")
    
    # Get trends
    trends = db.calculate_trends(days=90)
    print(f"Trends: {trends}")
    
    # Get statistics
    stats = db.get_statistics()
    print(f"Statistics: {stats}")
    
    db.close()

"""
EatUp Pro - Mobile Companion Backend API v2.0

Provides REST API endpoints for mobile apps (iOS/Android) to sync data across devices.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import json
import uuid
import sqlite3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import hashlib
import base64


def create_mobile_api(app_name: str = "eatup-mobile-api"):
    """Create Flask app configured for mobile API usage"""
    
    app = Flask(app_name)
    CORS(app)  # Allow cross-origin requests from mobile apps
    
    # Database setup
    DB_PATH = "data/mobile_api.db"
    _init_database()
    
    @app.route('/api/v1/mobile/health', methods=['GET'])
    def health_check():
        """Check if API is running"""
        return jsonify({
            'status': 'healthy',
            'version': '2.0.0',
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/api/v1/mobile/auth/register', methods=['POST'])
    def register_user():
        """Register new mobile user"""
        try:
            data = request.json
            username = data.get('username')
            password_hash = data.get('password')  # In production, hash properly!
            email = data.get('email', '')
            
            if not username or not password_hash:
                return jsonify({'error': 'Username and password required'}), 400
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'error': 'User already exists'}), 409
            
            # Create new user
            user_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO users (user_id, username, password_hash, email, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, password_hash, email, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'user_id': user_id,
                'message': 'Registration successful'
            }), 201
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/mobile/auth/login', methods=['POST'])
    def login_user():
        """Authenticate user and issue token"""
        try:
            data = request.json
            username = data.get('username')
            password = data.get('password')
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id FROM users 
                WHERE username = ? AND password_hash = ?
            """, (username, password))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return jsonify({'error': 'Invalid credentials'}), 401
            
            # Generate simple session token
            token = hashlib.sha256(f"{username}{datetime.now()}".encode()).hexdigest()
            
            # Store token
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    token TEXT PRIMARY KEY,
                    user_id TEXT,
                    device_info TEXT,
                    created_at TEXT,
                    expires_at TEXT
                )
            """)
            
            expires = (datetime.now() + timedelta(days=30)).isoformat()
            cursor.execute("""
                INSERT INTO tokens (token, user_id, device_info, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (token, result[0], request.remote_addr, 
                  datetime.now().isoformat(), expires))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'token': token,
                'user_id': result[0]
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/mobile/sync/scans', methods=['GET'])
    def get_scan_history():
        """Get all scan history for authenticated user"""
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verify token
        cursor.execute("""
            SELECT user_id FROM tokens WHERE token = ? AND expires_at > ?
        """, (token, datetime.now().isoformat()))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        user_id = result[0]
        
        # Get scan history
        cursor.execute("""
            SELECT * FROM scans 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 100
        """, (user_id,))
        
        columns = [desc[0] for desc in cursor.description]
        scans = []
        
        for row in cursor.fetchall():
            scan_dict = dict(zip(columns, row))
            scans.append(scan_dict)
        
        conn.close()
        
        return jsonify({
            'scans': scans,
            'count': len(scans)
        })
    
    @app.route('/api/v1/mobile/sync/scans', methods=['POST'])
    def save_scan():
        """Save scan results for user"""
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.json
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verify token
        cursor.execute("SELECT user_id FROM tokens WHERE token = ?", (token,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'Invalid token'}), 401
        
        user_id = result[0]
        
        # Save scan
        scan_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO scans (scan_id, user_id, drive, total_used_bytes, categories_json, 
                              temp_files_count, duplicates_count, large_files_count, 
                              cleanable_size, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scan_id, user_id, 
            data.get('drive', 'C:'),
            data.get('total_used_bytes', 0),
            json.dumps(data.get('categories', {})),
            data.get('temp_files_count', 0),
            data.get('duplicates_count', 0),
            data.get('large_files_count', 0),
            data.get('cleanable_size', 0),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'scan_id': scan_id
        })
    
    @app.route('/api/v1/mobile/sync/achievements', methods=['GET'])
    def get_achievements():
        """Get user's achievements and stats"""
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        # For demo, return mock data
        # In production, query from database
        return jsonify({
            'user_stats': {
                'level': 5,
                'xp': 2500,
                'xp_to_next': 3000,
                'total_cleanups': 47,
                'space_freed_total_gb': 125.5,
                'consecutive_days': 12
            },
            'unlocked_achievements': [
                {'id': 'first_step', 'name': 'First Step', 'tier': 'bronze', 'unlocked_at': '2026-10-15'},
                {'id': 'gigabyte_hero', 'name': 'Gigabyte Hero', 'tier': 'silver', 'unlocked_at': '2026-10-16'},
                {'id': 'cleanup_warrior', 'name': 'Cleanup Warrior', 'tier': 'bronze', 'unlocked_at': '2026-10-18'}
            ],
            'available_achievements': [
                {'id': 'ten_gig_master', 'name': 'Ten Gigabyte Master', 'tier': 'gold', 'progress': 8, 'target': 10}
            ]
        })
    
    @app.route('/api/v1/mobile/sync/stats', methods=['GET'])
    def get_usage_stats():
        """Get current storage statistics"""
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        try:
            # Fetch real data from local API server
            import requests
            response = requests.get('http://localhost:5000/api/v1/usage/stats')
            
            if response.ok:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Failed to fetch stats'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e), 'stats': get_mock_stats()})
    
    @app.route('/api/v1/mobile/sync/trends', methods=['GET'])
    def get_trend_data():
        """Get storage trend data for charts"""
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        days = request.args.get('days', 30, type=int)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, total_used_bytes 
            FROM scans 
            WHERE user_id = (SELECT user_id FROM tokens WHERE token = ?)
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (token, days))
        
        trends = []
        for row in cursor.fetchall():
            trends.append({
                'date': row[0],
                'used_gb': row[1] / (1024**3)
            })
        
        conn.close()
        
        # Sort by date ascending for chart
        trends.sort(key=lambda x: x['date'])
        
        return jsonify({
            'trends': trends,
            'days': days
        })
    
    @app.route('/api/v1/mobile/cleanup/start', methods=['POST'])
    def start_cleanup():
        """Start cleanup operation from mobile app"""
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.json
        cleanup_type = data.get('type', 'smart')
        
        try:
            import requests
            response = requests.post(
                'http://localhost:5000/api/v1/cleanup/run',
                json={'type': cleanup_type}
            )
            
            if response.ok:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Cleanup failed'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/mobile/reports/download/<scan_id>', methods=['GET'])
    def download_report(scan_id):
        """Download scan report as JSON"""
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM scans WHERE scan_id = ?", (scan_id,))
        scan = cursor.fetchone()
        
        if not scan:
            conn.close()
            return jsonify({'error': 'Scan not found'}), 404
        
        conn.close()
        
        # Create downloadable JSON
        columns = [desc[0] for desc in cursor.description]
        scan_dict = dict(zip(columns, scan))
        
        # Return as file download
        json_str = json.dumps(scan_dict, indent=2, default=str)
        
        return jsonify({
            'download_url': f'data:application/json,{json_str}',
            'filename': f'scan_{scan_id[:8]}.json'
        })
    
    @app.route('/api/v1/mobile/settings', methods=['GET'])
    def get_settings():
        """Get user settings"""
        return jsonify({
            'backup_enabled': True,
            'auto_scan_daily': False,
            'notifications_enabled': True,
            'theme': 'dark',
            'language': 'en',
            'sync_interval_minutes': 30
        })
    
    @app.route('/api/v1/mobile/settings', methods=['POST'])
    def update_settings():
        """Update user settings"""
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.json
        # In production, save to database
        
        return jsonify({'success': True})
    
    return app


def _init_database():
    """Initialize mobile API database"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            created_at TEXT
        )
    """)
    
    # Scans table (mobile-friendly)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            scan_id TEXT PRIMARY KEY,
            user_id TEXT,
            drive TEXT,
            total_used_bytes INTEGER,
            categories_json TEXT,
            temp_files_count INTEGER,
            duplicates_count INTEGER,
            large_files_count INTEGER,
            cleanable_size INTEGER,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Cleanup history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cleanup_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            cleanup_type TEXT,
            space_freed_bytes INTEGER,
            files_deleted INTEGER,
            timestamp TEXT
        )
    """)
    
    # Achievements
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            achievement_id TEXT,
            unlocked_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Tokens table for auth
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            user_id TEXT,
            device_info TEXT,
            created_at TEXT,
            expires_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    conn.commit()
    conn.close()


def get_mock_stats():
    """Mock stats for offline mode"""
    return {
        'total_used_gb': 245.5,
        'total_space_gb': 500.0,
        'utilization_percent': 49.1,
        'categories': {
            'Applications': 45.0,
            'Videos': 98.2,
            'Documents': 32.1,
            'Images': 24.5,
            'Music': 15.3,
            'Downloads': 12.4,
            'System': 13.0,
            'Other': 5.0
        }
    }


# CLI usage
if __name__ == "__main__":
    print("📱 EatUp Pro Mobile API Server")
    print("=" * 40)
    print("\nStarting mobile companion backend...")
    print("Visit: http://localhost:5001")
    print("\nEndpoints:")
    print("  POST /api/v1/mobile/auth/register     - Register new user")
    print("  POST /api/v1/mobile/auth/login        - Login and get token")
    print("  GET  /api/v1/mobile/sync/scans        - Get scan history")
    print("  POST /api/v1/mobile/sync/scans        - Save scan results")
    print("  GET  /api/v1/mobile/sync/achievements - Get achievements")
    print("  GET  /api/v1/mobile/sync/stats        - Get usage stats")
    print("  GET  /api/v1/mobile/sync/trends       - Get trend data")
    print("  POST /api/v1/mobile/cleanup/start     - Start cleanup")
    print("\nRun with: python mobile_api.py")
    
    app = create_mobile_api()
    app.run(host='0.0.0.0', port=5001, debug=False)

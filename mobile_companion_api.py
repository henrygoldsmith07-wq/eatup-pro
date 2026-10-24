#!/usr/bin/env python3
"""
EatUp Pro v8.1 - Mobile Companion Backend API
Full REST API with authentication for iOS/Android companion apps
"""

from flask import Flask, request, jsonify, g
from functools import wraps
import sqlite3
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['DATABASE'] = 'data/eatup_storage.db'
app.config['JWT_EXPIRY_HOURS'] = 24


# Authentication system
def generate_token(user_id: str) -> str:
    """Generate JWT-like token for mobile auth"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=app.config['JWT_EXPIRY_HOURS']),
        'iat': datetime.utcnow()
    }
    token_data = json.dumps(payload)
    signature = hashlib.sha256((token_data + app.config['SECRET_KEY']).encode()).hexdigest()
    return f"{token_data}.{signature}"


def verify_token(token: str) -> Optional[Dict]:
    """Verify authentication token"""
    try:
        if '.' not in token:
            return None
        
        payload_str, signature = token.rsplit('.', 1)
        expected_sig = hashlib.sha256((payload_str + app.config['SECRET_KEY']).encode()).hexdigest()
        
        if signature != expected_sig:
            return None
        
        payload = json.loads(payload_str)
        
        # Check expiration
        exp = datetime.fromtimestamp(payload['exp'])
        if datetime.utcnow() > exp:
            return None
        
        return payload
        
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None


def require_auth(f):
    """Authentication decorator for protected endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 403
        
        g.current_user = payload
        return f(*args, **kwargs)
    
    return decorated


# Database helper
def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/v2/auth/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.get_json()
    
    required_fields = ['username', 'email', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    db = get_db()
    
    # Check if user exists
    cursor = db.execute(
        'SELECT id FROM users WHERE email = ? OR username = ?',
        (data['email'], data['username'])
    )
    
    if cursor.fetchone():
        return jsonify({'error': 'User already exists'}), 409
    
    # Hash password
    hashed_password = hashlib.sha256(data['password'].encode()).hexdigest()
    
    # Create user
    db.execute(
        '''INSERT INTO users (username, email, password_hash, created_at)
           VALUES (?, ?, ?, ?)''',
        (data['username'], data['email'], hashed_password, datetime.now().isoformat())
    )
    
    db.commit()
    
    # Generate token
    user_id = db.lastrowid
    token = generate_token(str(user_id))
    
    return jsonify({
        'success': True,
        'token': token,
        'user': {'id': user_id, 'username': data['username']}
    }), 201


@app.route('/api/v2/auth/login', methods=['POST'])
def login():
    """Login and get authentication token"""
    data = request.get_json()
    
    if 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password required'}), 400
    
    db = get_db()
    
    # Verify credentials
    cursor = db.execute(
        '''SELECT id, username, email FROM users 
           WHERE email = ? AND password_hash = ?''',
        (data['email'], hashlib.sha256(data['password'].encode()).hexdigest())
    )
    
    user = cursor.fetchone()
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Generate token
    token = generate_token(str(user['id']))
    
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email']
        }
    })


@app.route('/api/v2/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user info"""
    db = get_db()
    
    cursor = db.execute(
        'SELECT id, username, email, created_at FROM users WHERE id = ?',
        (g.current_user['user_id'],)
    )
    
    user = cursor.fetchone()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': dict(user),
        'stats': get_user_stats(user['id'])
    })


# ============================================================================
# SCAN HISTORY ENDPOINTS
# ============================================================================

@app.route('/api/v2/scans', methods=['GET'])
@require_auth
def list_scans():
    """List all scans for current user"""
    db = get_db()
    
    cursor = db.execute(
        '''SELECT scan_id, drive, status, total_used, total_space, 
                  created_at FROM scans 
           WHERE user_id = ? ORDER BY created_at DESC
           LIMIT 50''',
        (g.current_user['user_id'],)
    )
    
    scans = [dict(row) for row in cursor.fetchall()]
    
    return jsonify({'scans': scans, 'total': len(scans)})


@app.route('/api/v2/scans/<scan_id>', methods=['GET'])
@require_auth
def get_scan(scan_id):
    """Get specific scan results"""
    db = get_db()
    
    cursor = db.execute(
        '''SELECT * FROM scan_results 
           WHERE scan_id = ? AND user_id = ?''',
        (scan_id, g.current_user['user_id'])
    )
    
    result = cursor.fetchone()
    
    if not result:
        return jsonify({'error': 'Scan not found'}), 404
    
    return jsonify({'scan': dict(result)})


@app.route('/api/v2/scans', methods=['POST'])
@require_auth
def create_scan():
    """Save scan results from mobile device"""
    data = request.get_json()
    
    required = ['drive', 'status', 'categories', 'total_used', 'total_space']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required fields'}), 400
    
    db = get_db()
    
    scan_id = f"scan_{secrets.token_hex(8)}"
    created_at = datetime.now().isoformat()
    
    db.execute(
        '''INSERT INTO scans (scan_id, user_id, drive, status, 
                             total_used, total_space, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (scan_id, g.current_user['user_id'], data['drive'], data['status'],
         data['total_used'], data['total_space'], created_at)
    )
    
    # Store categories JSON
    db.execute(
        '''INSERT INTO scan_categories (scan_id, categories_json)
           VALUES (?, ?)''',
        (scan_id, json.dumps(data['categories']))
    )
    
    db.commit()
    
    return jsonify({
        'success': True,
        'scan_id': scan_id,
        'message': 'Scan saved successfully'
    }), 201


# ============================================================================
# ACHIEVEMENT & STATS ENDPOINTS
# ============================================================================

def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Calculate user statistics"""
    db = get_db()
    
    # Get total space saved
    cursor = db.execute(
        '''SELECT COALESCE(SUM(space_saved_bytes), 0) as total_saved
           FROM cleanup_history WHERE user_id = ?''',
        (user_id,)
    )
    total_saved = cursor.fetchone()['total_saved']
    
    # Get achievements count
    cursor = db.execute(
        '''SELECT COUNT(*) as count FROM achievements 
           WHERE user_id = ? AND unlocked = 1''',
        (user_id,)
    )
    unlocked_achievements = cursor.fetchone()['count']
    
    # Calculate level based on XP (simplified)
    xp = total_saved // (1024**3)  # 1 GB = 1 XP
    level = min(100, max(1, xp // 100))
    
    return {
        'total_space_saved_gb': total_saved / (1024**3),
        'unlocked_achievements': unlocked_achievements,
        'level': level,
        'total_xp': xp
    }


@app.route('/api/v2/stats', methods=['GET'])
@require_auth
def get_stats():
    """Get comprehensive user statistics"""
    db = get_db()
    
    stats = get_user_stats(g.current_user['user_id'])
    
    # Recent activity (last 7 days)
    seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
    
    cursor = db.execute(
        '''SELECT COUNT(*) as cleanup_count, 
                  COALESCE(SUM(space_saved_bytes), 0) as recent_savings
           FROM cleanup_history 
           WHERE user_id = ? AND timestamp > ?''',
        (g.current_user['user_id'], seven_days_ago)
    )
    
    activity = cursor.fetchone()
    
    stats['last_7_days'] = {
        'cleanups_performed': activity['cleanup_count'],
        'space_saved_gb': activity['recent_savings'] / (1024**3)
    }
    
    return jsonify(stats)


@app.route('/api/v2/achievements', methods=['GET'])
@require_auth
def list_achievements():
    """List all available achievements"""
    db = get_db()
    
    # All achievements
    cursor = db.execute('SELECT * FROM achievements')
    all_achievements = [dict(row) for row in cursor.fetchall()]
    
    # User's unlocked achievements
    cursor = db.execute(
        '''SELECT achievement_id FROM user_achievements 
           WHERE user_id = ? AND unlocked = 1''',
        (g.current_user['user_id'],)
    )
    unlocked_ids = {row['achievement_id'] for row in cursor.fetchall()}
    
    # Add unlock status
    for achievement in all_achievements:
        achievement['unlocked'] = achievement['id'] in unlocked_ids
    
    return jsonify({'achievements': all_achievements})


# ============================================================================
# SCHEDULED TASKS ENDPOINTS
# ============================================================================

@app.route('/api/v2/schedules', methods=['GET'])
@require_auth
def list_schedules():
    """List scheduled tasks"""
    db = get_db()
    
    cursor = db.execute(
        '''SELECT schedule_id, name, cron_expression, task_type,
                  enabled, next_run FROM schedules 
           WHERE user_id = ? ORDER BY next_run''',
        (g.current_user['user_id'],)
    )
    
    schedules = [dict(row) for row in cursor.fetchall()]
    
    return jsonify({'schedules': schedules})


@app.route('/api/v2/schedules', methods=['POST'])
@require_auth
def create_schedule():
    """Create new scheduled task"""
    data = request.get_json()
    
    required = ['name', 'cron_expression', 'task_type']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required fields'}), 400
    
    db = get_db()
    
    schedule_id = f"sched_{secrets.token_hex(6)}"
    next_run = calculate_next_cron(data['cron_expression'])
    
    db.execute(
        '''INSERT INTO schedules (schedule_id, user_id, name, 
                                  cron_expression, task_type, enabled, next_run)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (schedule_id, g.current_user['user_id'], data['name'],
         data['cron_expression'], data['task_type'], 
         data.get('enabled', True), next_run)
    )
    
    db.commit()
    
    return jsonify({
        'success': True,
        'schedule_id': schedule_id,
        'next_run': next_run
    }), 201


def calculate_next_cron(cron_expr: str) -> str:
    """Calculate next run time from cron expression (simplified)"""
    # In production, use proper cron library like croniter
    parts = cron_expr.split()
    
    if len(parts) != 5:
        return datetime.now().isoformat()
    
    minute, hour, day, month, weekday = parts
    
    # Basic parsing (production should use croniter)
    next_time = datetime.now() + timedelta(hours=1)
    
    return next_time.isoformat()


# ============================================================================
# REAL-TIME SYNC ENDPOINTS
# ============================================================================

@app.route('/api/v2/sync/status', methods=['GET'])
@require_auth
def sync_status():
    """Get sync status between devices"""
    db = get_db()
    
    # Last sync times
    cursor = db.execute(
        '''SELECT MAX(last_sync) as last_full_sync FROM sync_history 
           WHERE user_id = ?''',
        (g.current_user['user_id'],)
    )
    
    last_sync = cursor.fetchone()['last_full_sync']
    
    # Pending changes
    cursor = db.execute(
        '''SELECT COUNT(*) as pending FROM pending_changes 
           WHERE user_id = ? AND synced = 0''',
        (g.current_user['user_id'],)
    )
    
    pending = cursor.fetchone()['pending']
    
    return jsonify({
        'last_sync': last_sync,
        'pending_changes': pending,
        'sync_enabled': True
    })


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/v2/health', methods=['GET'])
def health():
    """API health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0.0',
        'service': 'eatup-mobile-backend',
        'timestamp': datetime.now().isoformat()
    })


# ============================================================================
# INITIALIZE DATABASE (on first run)
# ============================================================================

def init_database():
    """Initialize database schema"""
    db_path = app.config['DATABASE']
    
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
    
    conn = sqlite3.connect(db_path)
    
    conn.executescript('''
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Scans table
    CREATE TABLE IF NOT EXISTS scans (
        scan_id TEXT PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        drive TEXT NOT NULL,
        status TEXT DEFAULT 'completed',
        total_used INTEGER NOT NULL,
        total_space INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Scan categories storage
    CREATE TABLE IF NOT EXISTS scan_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id TEXT REFERENCES scans(scan_id),
        categories_json TEXT NOT NULL
    );
    
 -- Cleanup history
    CREATE TABLE IF NOT EXISTS cleanup_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id),
        scan_id TEXT,
        space_saved_bytes INTEGER NOT NULL,
        files_cleaned INTEGER DEFAULT 0,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Achievements catalog
    CREATE TABLE IF NOT EXISTS achievements (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        icon_url TEXT,
        xp_reward INTEGER,
        requirements JSON,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    
    -- User achievements
    CREATE TABLE IF NOT EXISTS user_achievements (
        user_id INTEGER REFERENCES users(id),
        achievement_id TEXT REFERENCES achievements(id),
        unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP,
        unlocked INTEGER DEFAULT 1,
        PRIMARY KEY (user_id, achievement_id)
    );
    
    -- Scheduled tasks
    CREATE TABLE IF NOT EXISTS schedules (
        schedule_id TEXT PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        name TEXT NOT NULL,
        cron_expression TEXT NOT NULL,
        task_type TEXT NOT NULL,
        enabled INTEGER DEFAULT 1,
        next_run TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Sync history
    CREATE TABLE IF NOT EXISTS sync_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id),
        device_info TEXT,
        last_sync TEXT DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Seed achievements
    INSERT OR IGNORE INTO achievements (id, name, description, xp_reward) VALUES
        ('first_scan', 'Curious Mind', 'Performed your first disk scan', 10),
        ('space_saver', 'Storage Wizard', 'Saved 1GB of space', 50),
        ('detection_expert', 'Duplicate Hunter', 'Found and removed duplicates', 30),
        ('consistent', 'Daily Cleaner', 'Cleaned for 7 consecutive days', 100),
        ('mega_cleaner', 'Disk Master', 'Saved 10GB of space', 500);
    
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Mobile backend database initialized")


if __name__ == '__main__':
    init_database()
    
    print("\n📱 EatUp Pro Mobile Backend API v2.0")
    print("=" * 50)
    print("\nEndpoints:")
    print("  POST   /api/v2/auth/register     - Register new user")
    print("  POST   /api/v2/auth/login        - Login and get token")
    print("  GET    /api/v2/auth/me           - Current user info")
    print("  GET    /api/v2/scans             - List scan history")
    print("  POST   /api/v2/scans             - Save scan results")
    print("  GET    /api/v2/stats             - User statistics")
    print("  GET    /api/v2/achievements      - Achievement list")
    print("  GET    /api/v2/schedules         - Scheduled tasks")
    print("  GET    /api/v2/health            - Health check")
    print("\nRun with: python mobile_companion_api.py")
    print("\nNote: Production use requires HTTPS and proper security\n")
    
    # Start server (for development)
    # app.run(debug=True, host='0.0.0.0', port=5001)

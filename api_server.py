#!/usr/bin/env python3
"""
EatUp Pro - REST API Server
Provides web-based interface for all functionality
"""

import os
import sys
import hmac
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from functools import wraps
import threading
import uuid
import psutil

# Import local modules
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
from cleaner import EatUpCleaner, CleanupResult, GB
from scheduler import SchedulerManager
from cloud_storage import CloudStorageManager
from data.analytics_db import AnalyticsDatabase

API_VERSION = '1.2.0'
START_TIME = time.time()
HOST = os.getenv('HOST', '127.0.0.1')
LOCAL_HOSTNAMES = {'localhost', '127.0.0.1', '[::1]'}
UI_PAGES = {'index.html', 'app.html', 'features.html', 'analytics_dashboard.html'}

app = Flask(__name__, static_folder=None)

# The UI is served from this server, so cross-origin access is off unless
# explicitly configured (comma-separated origins).
cors_origins = [o.strip() for o in os.getenv('CORS_ORIGINS', '').split(',') if o.strip()]
if cors_origins:
    CORS(app, origins=cors_origins)

# Global instances
cleaner = None
scheduler = None
cloud_manager = None
db = None

# Scan jobs: scan_id -> {'status', 'drive', 'error', 'started_at', 'finished_at'}
scan_jobs = {}
scan_lock = threading.Lock()
latest_scan_id = None


def get_cleaner():
    """Lazy initialization of cleaner"""
    global cleaner
    if cleaner is None:
        cleaner = EatUpCleaner()
    return cleaner


def get_scheduler():
    """Lazy initialization of scheduler"""
    global scheduler
    if scheduler is None:
        scheduler = SchedulerManager()
    return scheduler


def get_cloud_manager():
    """Lazy initialization of cloud manager"""
    global cloud_manager
    if cloud_manager is None:
        cloud_manager = CloudStorageManager()
    return cloud_manager


def get_db():
    """Lazy initialization of analytics database"""
    global db
    if db is None:
        db = AnalyticsDatabase()
    return db


@app.before_request
def reject_foreign_hosts():
    """Block DNS-rebinding attacks while bound to loopback"""
    if HOST in ('127.0.0.1', 'localhost', '::1'):
        hostname = request.host
        if not hostname.endswith(']'):  # Strip the port, keeping bracketed IPv6
            hostname = hostname.rsplit(':', 1)[0]
        if hostname not in LOCAL_HOSTNAMES:
            abort(403)


# Helper decorators
def require_auth(f):
    """Require the API key when one is configured, and a JSON body on writes.

    Requiring application/json forces a CORS preflight, so other websites open
    in the user's browser cannot trigger destructive endpoints.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        expected = os.getenv('API_KEY')
        api_key = request.headers.get('X-API-Key', '')
        if expected and not hmac.compare_digest(api_key, expected):
            return jsonify({'error': 'Unauthorized'}), 401
        if request.method == 'POST' and not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 415
        return f(*args, **kwargs)
    return decorated


def is_scan_running():
    return any(job['status'] == 'running' for job in scan_jobs.values())


# ==================== WEB UI ====================

@app.route('/')
def ui_index():
    return send_from_directory(BASE_DIR, 'index.html')


@app.route('/<page>')
def ui_page(page):
    if page not in UI_PAGES:
        abort(404)
    return send_from_directory(BASE_DIR, page)


# ==================== HEALTH & STATUS ====================

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': API_VERSION,
        'timestamp': datetime.now().isoformat(),
        'uptime_seconds': round(time.time() - START_TIME)
    })


# ==================== CORE CLEANING OPERATIONS ====================

@app.route('/api/v1/scan/start', methods=['POST'])
@require_auth
def scan_start():
    """Start a new drive scan in the background"""
    data = request.json or {}
    drive = data.get('drive', 'C:')
    if not isinstance(drive, str) or not drive.strip():
        return jsonify({'error': 'drive must be a non-empty string'}), 400
    with_duplicates = data.get('find_duplicates', True)
    
    with scan_lock:
        running = next((sid for sid, job in scan_jobs.items() if job['status'] == 'running'), None)
        if running:
            return jsonify({'error': 'A scan is already running', 'scan_id': running}), 409
        scan_id = str(uuid.uuid4())
        scan_jobs[scan_id] = {'status': 'running', 'drive': drive, 'error': None,
                              'started_at': time.time(), 'finished_at': None}
    
    threading.Thread(target=run_scan, args=(scan_id, drive, with_duplicates), daemon=True).start()
    
    return jsonify({
        'status': 'starting',
        'message': f'Started scanning {drive}',
        'scan_id': scan_id
    })


def run_scan(scan_id, drive, with_duplicates):
    """Background worker: scan, optionally find duplicates, persist the result"""
    global latest_scan_id
    job = scan_jobs[scan_id]
    try:
        cleaner_obj = get_cleaner()
        results = cleaner_obj.scan_drive(drive)
        if with_duplicates:
            cleaner_obj.find_duplicates()
        
        duration = time.time() - job['started_at']
        get_db().save_scan({
            'scan_id': scan_id,
            'drive': drive,
            'total_used_bytes': results.total_used,
            'total_space_bytes': results.total_space,
            'utilization_percent': (results.total_used / results.total_space * 100) if results.total_space > 0 else 0,
            'categories_json': json.dumps(results.categories),
            'temp_files_count': len(results.temp_files),
            'duplicate_groups_count': len(results.duplicates),
            'large_files_count': len(results.large_files),
            'cleanable_bytes': results.cleanable_size,
            'status': 'complete'
        }, duration=duration)
        job['status'] = 'complete'
        latest_scan_id = scan_id
    except Exception as e:
        job['status'] = 'failed'
        job['error'] = str(e)
    finally:
        job['finished_at'] = time.time()


@app.route('/api/v1/scan/status/<scan_id>', methods=['GET'])
def scan_status(scan_id):
    """Get scan status"""
    job = scan_jobs.get(scan_id)
    if job is None:
        return jsonify({'error': 'Unknown scan_id'}), 404
    
    messages = {
        'running': 'Scanning in progress...',
        'complete': 'Scan completed successfully',
        'failed': f"Scan failed: {job['error']}"
    }
    return jsonify({
        'scan_id': scan_id,
        'status': job['status'],
        'progress': 100 if job['status'] == 'complete' else None,
        'files_scanned': get_cleaner().files_scanned,
        'message': messages[job['status']]
    })


@app.route('/api/v1/scan/results/<scan_id>', methods=['GET'])
def scan_results(scan_id):
    """Get scan results"""
    if scan_id != latest_scan_id:
        return jsonify({'error': 'Results are only kept for the latest completed scan'}), 404
    
    results = get_cleaner().scan_results
    return jsonify({
        'drive': results.drive,
        'total_used_gb': results.total_used / GB,
        'total_space_gb': results.total_space / GB,
        'utilization_percent': (results.total_used / results.total_space * 100) if results.total_space > 0 else 0,
        'categories': {k: v / GB for k, v in results.categories.items()},
        'files_scanned': results.files_scanned,
        'large_files_count': len(results.large_files),
        'large_files': [{'path': f.path, 'size_gb': f.size / GB, 'age_days': f.age_days}
                        for f in results.large_files[:20]],
        'duplicate_groups': len(results.duplicates),
        'duplicate_gb': get_cleaner().duplicate_bytes() / GB,
        'temp_files_count': len(results.temp_files),
        'temp_gb': sum(f.size for f in results.temp_files) / GB,
        'cleanable_gb': results.cleanable_size / GB
    })


@app.route('/api/v1/cleanup/run', methods=['POST'])
@require_auth
def cleanup_run():
    """Run cleanup operation"""
    try:
        data = request.json or {}
        cleanup_type = data.get('type', 'smart')
        dry_run = bool(data.get('dry_run', False))
        
        cleaner_obj = get_cleaner()
        if is_scan_running():
            return jsonify({'error': 'Wait for the running scan to finish'}), 409
        if not cleaner_obj.scan_results:
            return jsonify({'error': 'Run a scan before cleaning up'}), 400
        
        started = time.time()
        if cleanup_type == 'temp':
            result = cleaner_obj.cleanup_temp_files(dry_run=dry_run)
        elif cleanup_type == 'duplicates':
            result = cleaner_obj.cleanup_duplicates(dry_run=dry_run)
        elif cleanup_type == 'large':
            try:
                min_size = float(data.get('min_size_gb', 1))
            except (TypeError, ValueError):
                return jsonify({'error': 'min_size_gb must be a number'}), 400
            if min_size <= 0:
                return jsonify({'error': 'min_size_gb must be positive'}), 400
            result = cleaner_obj.cleanup_large_files(min_size_gb=min_size, dry_run=dry_run)
        elif cleanup_type == 'smart':
            result = cleaner_obj.smart_cleanup(dry_run=dry_run)
        else:
            return jsonify({'error': f'Unknown cleanup type: {cleanup_type}'}), 400
        
        cleanup_id = str(uuid.uuid4())
        if not dry_run:
            get_db().record_cleanup({
                'cleanup_id': cleanup_id,
                'scan_id': latest_scan_id,
                'cleanup_type': cleanup_type,
                'files_deleted': result.files_deleted,
                'space_freed_bytes': result.freed_bytes,
                'duration_seconds': time.time() - started,
                'success': not result.errors,
                'error_message': f'{len(result.errors)} files could not be removed' if result.errors else None
            })
        
        return jsonify({
            'status': 'preview' if dry_run else 'success',
            'cleanup_type': cleanup_type,
            'space_freed_mb': result.freed_bytes / (1024**2),
            'space_freed_bytes': result.freed_bytes,
            'files_deleted': result.files_deleted,
            'errors': result.errors[:20],
            'cleanup_id': cleanup_id,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== USAGE STATISTICS ====================

@app.route('/api/v1/usage/stats', methods=['GET'])
def usage_stats():
    """Get current disk usage statistics"""
    try:
        stats = psutil.disk_usage(os.path.abspath(os.sep))
        
        return jsonify({
            'total_bytes': stats.total,
            'used_bytes': stats.used,
            'free_bytes': stats.free,
            'percent_used': stats.percent,
            'total_gb': stats.total / (1024**3),
            'used_gb': stats.used / (1024**3),
            'free_gb': stats.free / (1024**3)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== SCHEDULED TASKS ====================

@app.route('/api/v1/schedule/create', methods=['POST'])
@require_auth
def schedule_create():
    """Create a new scheduled task"""
    try:
        data = request.json or {}
        
        scheduler_obj = get_scheduler()
        
        task_id = scheduler_obj.add_task(
            name=data.get('name', 'Scheduled Task'),
            drive=data.get('drive', 'C:'),
            frequency=data.get('frequency', 'daily'),
            time=data.get('time', '02:00'),
            actions=data.get('actions', ['scan']),
            enabled=data.get('enabled', True)
        )
        
        return jsonify({
            'status': 'created',
            'task_id': task_id,
            'name': data.get('name')
        })
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/schedule/list', methods=['GET'])
def schedule_list():
    """List all scheduled tasks"""
    try:
        scheduler_obj = get_scheduler()
        
        runs = scheduler_obj.get_next_scheduled_runs()
        logs = scheduler_obj.get_recent_logs(limit=10)
        
        return jsonify({
            'tasks': runs,
            'recent_logs': logs
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/schedule/<task_id>/run', methods=['POST'])
@require_auth
def schedule_run(task_id):
    """Manually run a scheduled task"""
    try:
        scheduler_obj = get_scheduler()
        
        log = scheduler_obj.run_task(task_id)
        
        return jsonify({
            'status': 'completed',
            'files_processed': log.files_processed,
            'space_freed_mb': log.space_freed_mb,
            'duration_seconds': (log.completed_at - log.started_at).total_seconds() if log.completed_at else None
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== CLOUD STORAGE ====================

@app.route('/api/v1/cloud/connect/google-drive', methods=['POST'])
@require_auth
def cloud_connect_google_drive():
    """Connect to Google Drive"""
    try:
        cloud_manager = get_cloud_manager()
        
        # Return OAuth URL
        auth_url = "https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=urn:ietf:wg:oauth:2.0:oob&scope=https://www.googleapis.com/auth/drive.readonly&access_type=offline"
        
        return jsonify({
            'status': 'auth_required',
            'auth_url': auth_url,
            'message': 'Please complete OAuth flow and provide authorization code'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/cloud/connect/dropbox', methods=['POST'])
@require_auth
def cloud_connect_dropbox():
    """Connect to Dropbox"""
    try:
        data = request.json or {}
        app_key = data.get('app_key')
        app_secret = data.get('app_secret')
        
        cloud_manager = get_cloud_manager()
        
        success = cloud_manager.authenticate_dropbox(app_key, app_secret)
        
        if success:
            return jsonify({
                'status': 'connected',
                'service': 'dropbox'
            })
        else:
            return jsonify({'error': 'Authentication failed'}), 401
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/cloud/files', methods=['GET'])
@require_auth
def cloud_get_files():
    """Get files from all connected cloud services"""
    try:
        cloud_manager = get_cloud_manager()
        
        limit = request.args.get('limit', 100, type=int)
        files = cloud_manager.get_all_files(limit=limit)
        
        return jsonify({
            'count': len(files),
            'files': [{
                'id': f.id,
                'name': f.name,
                'size': f.size,
                'path': f.path,
                'cloud_service': f.cloud_service,
                'modified': f.modified.isoformat() if hasattr(f.modified, 'isoformat') else str(f.modified)
            } for f in files]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/cloud/stats', methods=['GET'])
@require_auth
def cloud_stats():
    """Get cloud storage statistics"""
    try:
        cloud_manager = get_cloud_manager()
        
        stats = cloud_manager.calculate_cloud_stats()
        
        return jsonify({
            'total_space_gb': stats.total_space / (1024**3),
            'used_space_gb': stats.used_space / (1024**3),
            'free_space_gb': stats.free_space / (1024**3),
            'utilization_percent': stats.utilization_percent,
            'file_count': stats.file_count,
            'services_connected': stats.services_connected
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== ANALYTICS ====================

@app.route('/api/v1/analytics/trends', methods=['GET'])
def analytics_trends():
    """Get historical usage trends"""
    try:
        days = request.args.get('days', 90, type=int)
        
        # Computing over the scans table is cheap; a day-old cache would hide new scans
        trends = get_db().calculate_trends(days=days)
        trends['days_analyzed'] = days
        
        return jsonify(trends)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/analytics/scans', methods=['GET'])
def analytics_scans():
    """Get list of recent scans"""
    try:
        db = get_db()
        limit = request.args.get('limit', 10, type=int)
        
        scans = db.get_recent_scans(limit=limit)
        
        return jsonify({
            'count': len(scans),
            'scans': [{
                'id': s['id'],
                'timestamp': s['timestamp'],
                'drive': s['drive'],
                'total_used_gb': s['total_used_bytes'] / (1024**3),
                'utilization_percent': s['utilization_percent'],
                'status': s['status']
            } for s in scans]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/analytics/cleanup-history', methods=['GET'])
def analytics_cleanup_history():
    """Get history of cleanup operations"""
    try:
        db = get_db()
        limit = request.args.get('limit', 20, type=int)
        
        history = db.get_cleanup_history(limit=limit)
        
        return jsonify({
            'count': len(history),
            'cleanups': [{
                'id': h['id'],
                'timestamp': h['timestamp'],
                'type': h['cleanup_type'],
                'files_deleted': h['files_deleted'],
                'space_freed_mb': h['space_freed_bytes'] / (1024**2),
                'success': h['success']
            } for h in history]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/analytics/statistics', methods=['GET'])
def analytics_statistics():
    """Get overall app statistics"""
    try:
        db = get_db()
        stats = db.get_statistics()
        
        # Add total space saved last 30 days
        stats['total_space_saved_last_30_days_mb'] = db.get_total_space_saved(days=30) / (1024**2)
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== EXPORT FUNCTIONS ====================

@app.route('/api/v1/export/report', methods=['GET'])
@require_auth
def export_report():
    """Export scan report as JSON"""
    try:
        report = get_cleaner().build_report()
        if report is None:
            return jsonify({'error': 'No scan results available'}), 404
        
        response = jsonify(report)
        filename = f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== AI & INTELLIGENCE ====================

@app.route('/api/v1/ai/analyze', methods=['POST'])
@require_auth
def ai_analyze():
    """AI-powered analysis of scan results"""
    try:
        data = request.json or {}
        
        # Placeholder for AI analysis
        analysis = {
            'confidence_score': 0.85,
            'risk_assessment': 'low',
            'recommendations': [
                {
                    'type': 'delete_temp_files',
                    'confidence': 0.95,
                    'reason': 'Safe to remove temporary files'
                },
                {
                    'type': 'review_duplicates',
                    'confidence': 0.72,
                    'reason': 'Some duplicates may be important backups'
                }
            ],
            'anomalies_detected': []
        }
        
        return jsonify(analysis)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== ERROR HANDLING ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ==================== MAIN ENTRY POINT ====================

def main():
    """Start the API server"""
    import argparse

    parser = argparse.ArgumentParser(description='EatUp Pro API server')
    parser.add_argument('--port', type=int, default=int(os.getenv('PORT', 5000)),
                        help='Port to listen on (default: $PORT or 5000)')
    args = parser.parse_args()
    port = args.port
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    print(f"Starting EatUp Pro API Server on {HOST}:{port}")
    print(f"App: http://localhost:{port}/app.html")
    print(f"Health check: http://localhost:{port}/api/v1/health")
    
    app.run(host=HOST, port=port, debug=debug)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
EatUp Pro - REST API Server
Provides web-based interface for all functionality
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from functools import wraps
import threading

# Import local modules
sys.path.append(os.path.dirname(__file__))
from cleaner import EatUpCleaner
from scheduler import SchedulerManager
from cloud_storage import CloudStorageManager

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Global instances
cleaner = None
scheduler = None
cloud_manager = None


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


# Helper decorators
def require_auth(f):
    """Simple authentication decorator (can be enhanced with JWT)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check for API key in header
        api_key = request.headers.get('X-API-Key')
        if os.getenv('API_KEY') and api_key != os.getenv('API_KEY'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


# ==================== HEALTH & STATUS ====================

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'uptime_seconds': get_uptime()
    })


def get_uptime():
    """Get server uptime (simplified)"""
    # In production, track start time at startup
    return 0


# ==================== CORE CLEANING OPERATIONS ====================

@app.route('/api/v1/scan/start', methods=['POST'])
def scan_start():
    """Start a new drive scan"""
    try:
        data = request.json or {}
        drive = data.get('drive', 'C:')
        
        cleaner_obj = get_cleaner()
        
        # Start scan in background thread
        def run_scan():
            result = cleaner_obj.scan_drive(drive)
            return result
        
        thread = threading.Thread(target=run_scan, daemon=True)
        thread.start()
        
        return jsonify({
            'status': 'starting',
            'message': f'Started scanning {drive}',
            'scan_id': generate_scan_id()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/scan/status/<scan_id>', methods=['GET'])
def scan_status(scan_id):
    """Get scan status"""
    # Simplified - in production, store scan results
    return jsonify({
        'scan_id': scan_id,
        'status': 'complete',
        'progress': 100,
        'message': 'Scan completed'
    })


@app.route('/api/v1/scan/results/<scan_id>', methods=['GET'])
def scan_results(scan_id):
    """Get scan results"""
    try:
        cleaner_obj = get_cleaner()
        
        if not cleaner_obj.scan_results:
            raise ValueError("No scan results available")
        
        results = cleaner_obj.scan_results
        
        response_data = {
            'total_used_gb': results.total_used / (1024**3),
            'total_space_gb': results.total_space / (1024**3),
            'utilization_percent': (results.total_used / results.total_space * 100) if results.total_space > 0 else 0,
            'categories': {k: v / (1024**3) for k, v in results.categories.items()},
            'large_files_count': len(results.large_files),
            'duplicate_groups': len(results.duplicates),
            'temp_files_count': len(results.temp_files),
            'cleanable_gb': results.cleanable_size / (1024**3)
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 404


@app.route('/api/v1/cleanup/run', methods=['POST'])
@require_auth
def cleanup_run():
    """Run cleanup operation"""
    try:
        data = request.json or {}
        cleanup_type = data.get('type', 'smart')
        
        cleaner_obj = get_cleaner()
        
        space_freed = 0
        
        if cleanup_type == 'temp':
            space_freed = cleaner_obj.cleanup_temp_files(dry_run=False)
        elif cleanup_type == 'duplicates':
            space_freed = cleaner_obj.cleanup_duplicates(dry_run=False)
        elif cleanup_type == 'large':
            min_size = data.get('min_size_gb', 1)
            space_freed = cleaner_obj.cleanup_large_files(min_size_gb=min_size)
        elif cleanup_type == 'smart':
            space_freed = cleaner_obj.smart_cleanup()
        else:
            return jsonify({'error': f'Unknown cleanup type: {cleanup_type}'}), 400
        
        freed_mb = space_freed / (1024**2)
        
        return jsonify({
            'status': 'success',
            'cleanup_type': cleanup_type,
            'space_freed_mb': freed_mb,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== USAGE STATISTICS ====================

@app.route('/api/v1/usage/stats', methods=['GET'])
def usage_stats():
    """Get current disk usage statistics"""
    try:
        stats = psutil.disk_usage('/')
        
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
        
        # Placeholder - implement full analytics engine
        trends = {
            'days_analyzed': days,
            'data_points': [],
            'trend_direction': 'stable',
            'average_daily_growth_mb': 10.5
        }
        
        return jsonify(trends)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== EXPORT FUNCTIONS ====================

@app.route('/api/v1/export/report', methods=['GET'])
@require_auth
def export_report():
    """Export scan report as JSON"""
    try:
        cleaner_obj = get_cleaner()
        
        filename = cleaner_obj.export_report()
        
        # Send file for download
        return send_file(
            filename,
            as_attachment=True,
            mimetype='application/json',
            download_name=f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
    
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
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    print(f"Starting EatUp Pro API Server on port {port}")
    print(f"Documentation: http://localhost:{port}/docs")
    print(f"Health check: http://localhost:{port}/api/v1/health")
    
    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    main()

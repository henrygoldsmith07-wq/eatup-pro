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
import uuid

# Import local modules
sys.path.append(os.path.dirname(__file__))
from cleaner import EatUpCleaner
from scheduler import SchedulerManager
from cloud_storage import CloudStorageManager
from data.analytics_db import AnalyticsDatabase
from ai_suggestions import AISuggestionEngine

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Global instances
cleaner = None
scheduler = None
cloud_manager = None
db = None
ai_engine = None


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


def get_ai_engine():
    """Lazy initialization of AI suggestion engine"""
    global ai_engine
    if ai_engine is None:
        ai_engine = AISuggestionEngine()
    return ai_engine


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
    try:
        # Check if scan is complete
        cleaner_obj = get_cleaner()
        
        if cleaner_obj.scan_results and not hasattr(cleaner_obj, '_scan_in_progress'):
            # Scan completed, save to database
            db = get_db()
            
            categories_json = json.dumps(cleaner_obj.scan_results.categories)
            
            scan_data = {
                'scan_id': scan_id,
                'drive': 'C:',
                'total_used_bytes': cleaner_obj.scan_results.total_used,
                'total_space_bytes': cleaner_obj.scan_results.total_space,
                'utilization_percent': (cleaner_obj.scan_results.total_used / cleaner_obj.scan_results.total_space * 100) if cleaner_obj.scan_results.total_space > 0 else 0,
                'categories_json': categories_json,
                'temp_files_count': len(cleaner_obj.scan_results.temp_files),
                'duplicate_groups_count': len(cleaner_obj.scan_results.duplicates),
                'large_files_count': len(cleaner_obj.scan_results.large_files),
                'cleanable_bytes': cleaner_obj.scan_results.cleanable_size,
                'status': 'complete'
            }
            
            db.save_scan(scan_data)
            
            return jsonify({
                'scan_id': scan_id,
                'status': 'complete',
                'progress': 100,
                'message': 'Scan completed successfully'
            })
        
        return jsonify({
            'scan_id': scan_id,
            'status': 'running',
            'progress': 50,
            'message': 'Scanning in progress...'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
    """Run cleanup operation with AI recommendations"""
    try:
        data = request.json or {}
        cleanup_type = data.get('type', 'smart')
        
        cleaner_obj = get_cleaner()
        db = get_db()
        ai_engine = get_ai_engine()
        
        # If smart cleanup, analyze first with AI
        if cleanup_type == 'smart':
            print("🤖 Generating AI cleanup plan...")
            
            # Load plugins
            cleaner_obj.load_plugins()
            
            # Analyze scan results with AI
            plan = ai_engine.generate_cleanup_plan(cleaner_obj)
            
            print(f"AI Plan Summary: {plan['summary']}")
            
            # Save recommended deletions to database for tracking
            for file_entry in plan.get('files_to_delete', [])[:50]:
                rec_data = {
                    'recommendation_id': str(uuid.uuid4()),
                    'scan_id': None,
                    'filepath': file_entry['filepath'],
                    'size_bytes': int(file_entry['size_mb'] * 1024 * 1024),
                    'action': 'delete',
                    'confidence': 0.85,
                    'reason': file_entry['reason'],
                    'risk_level': 'safe'
                }
                db.save_recommendation(rec_data)
        
        space_freed = 0
        files_deleted = 0
        
        if cleanup_type == 'temp':
            space_freed = cleaner_obj.cleanup_temp_files(dry_run=False)
            files_deleted = len(cleaner_obj.get_temp_files_list())
        elif cleanup_type == 'duplicates':
            space_freed = cleaner_obj.cleanup_duplicates(dry_run=False)
        elif cleanup_type == 'large':
            min_size = data.get('min_size_gb', 1)
            space_freed = cleaner_obj.cleanup_large_files(min_size_gb=min_size)
        elif cleanup_type == 'smart':
            # Use plugin-aware cleanup
            space_freed = cleaner_obj.smart_cleanup()
            
            # Run cleanup plugins
            if cleaner_obj.plugin_manager:
                for plugin in cleaner_obj.plugin_manager.get_loaded_plugins():
                    try:
                        cleaned = plugin.customize_cleanup(cleaner_obj)
                        if cleaned:
                            print(f"  ✅ Plugin '{plugin.name}' cleaned {len(cleaned)} additional files")
                    except Exception as e:
                        print(f"  ⚠️  Plugin cleanup error: {e}")
        
        else:
            return jsonify({'error': f'Unknown cleanup type: {cleanup_type}'}), 400
        
        freed_mb = space_freed / (1024**2)
        
        # Record in database
        cleanup_id = str(uuid.uuid4())
        db.record_cleanup({
            'cleanup_id': cleanup_id,
            'scan_id': None,
            'cleanup_type': cleanup_type,
            'files_deleted': files_deleted,
            'space_freed_bytes': space_freed,
            'duration_seconds': None,
            'success': True
        })
        
        return jsonify({
            'status': 'success',
            'cleanup_type': cleanup_type,
            'space_freed_mb': freed_mb,
            'space_freed_bytes': space_freed,
            'files_deleted': files_deleted,
            'cleanup_id': cleanup_id,
            'timestamp': datetime.now().isoformat(),
            'plugins_used': len(cleaner_obj.plugin_manager.get_loaded_plugins()) if cleaner_obj.plugin_manager else 0
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
        db = get_db()
        days = request.args.get('days', 90, type=int)
        
        # Try to get cached trends first
        cached = db.get_cached_trends(max_age_hours=24)
        if cached:
            return jsonify({
                'days_analyzed': days,
                'daily_growth_mb': cached['daily_growth_mb'],
                'weekly_growth_mb': cached['weekly_growth_mb'],
                'monthly_growth_mb': cached['monthly_growth_mb'],
                'trend_direction': 'stable',
                'average_utilization': cached['average_utilization'],
                'prediction_next_30_days_mb': cached['prediction_next_30_days_mb'],
                'data_points': 0  # From cache
            })
        
        # Calculate fresh trends
        trends = db.calculate_trends(days=days)
        
        # Cache results
        db.cache_trends(trends)
        
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

@app.route('/api/v1/ai/cleanup-plan', methods=['POST'])
@require_auth
def ai_cleanup_plan():
    """Generate AI-powered cleanup plan from scan results"""
    try:
        data = request.json or {}
        scan_id = data.get('scan_id')
        
        ai_engine = get_ai_engine()
        cleaner_obj = get_cleaner()
        
        # Get scan results
        if not cleaner_obj.scan_results:
            return jsonify({'error': 'No scan results available'}), 404
        
        # Generate cleanup plan
        plan = ai_engine.generate_cleanup_plan(cleaner_obj)
        
        # Save recommendations to database
        db = get_db()
        for file_entry in plan.get('files_to_delete', [])[:50]:
            rec_data = {
                'recommendation_id': str(uuid.uuid4()),
                'scan_id': scan_id,
                'filepath': file_entry['filepath'],
                'size_bytes': int(file_entry['size_mb'] * 1024 * 1024),
                'action': 'delete',
                'confidence': 0.85,  # From cleanup plan logic
                'reason': file_entry['reason'],
                'risk_level': 'safe'
            }
            db.save_recommendation(rec_data)
        
        return jsonify({
            'success': True,
            'plan': plan,
            'total_recommendations_saved': len(plan.get('files_to_delete', [])) + len(plan.get('files_to_review', []))
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/ai/file-analysis/<filepath>', methods=['GET'])
@require_auth
def ai_file_analysis(filepath):
    """Analyze a specific file's deletion safety"""
    try:
        filepath = os.path.expanduser(filepath)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        ai_engine = get_ai_engine()
        
        # Get file stats
        stat_info = os.stat(filepath)
        file_info = {
            'path': filepath,
            'size': stat_info.st_size
        }
        
        analysis = ai_engine.analyze_file_for_safety(filepath, file_info)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/ai/preferences', methods=['GET', 'POST'])
@require_auth
def ai_preferences():
    """Get or set AI preferences"""
    try:
        db = get_db()
        
        if request.method == 'POST':
            preferences = request.json or {}
            
            # Set user preferences
            db.save_preference('ai_strict_mode', preferences.get('strict_mode', False))
            db.save_preference('ai_aggressive_mode', preferences.get('aggressive_mode', False))
            
            # Adjust AI engine weights
            ai_engine = get_ai_engine()
            ai_engine.adjust_weights(preferences)
            
            return jsonify({
                'success': True,
                'message': 'AI preferences updated'
            })
        
        else:
            # Get current preferences
            strict_mode = db.get_preference('ai_strict_mode', False)
            aggressive_mode = db.get_preference('ai_aggressive_mode', False)
            
            return jsonify({
                'success': True,
                'preferences': {
                    'strict_mode': strict_mode,
                    'aggressive_mode': aggressive_mode
                }
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/ai/learn', methods=['POST'])
@require_auth
def ai_learn():
    """Provide feedback on AI recommendation (user decision)"""
    try:
        data = request.json or {}
        filepath = data.get('filepath')
        decision = data.get('decision')  # delete, keep, review
        success = data.get('success', True)
        
        if not filepath or not decision:
            return jsonify({'error': 'filepath and decision required'}), 400
        
        ai_engine = get_ai_engine()
        
        # Learn from decision
        ai_engine.learn_from_decision(filepath, decision, success)
        
        return jsonify({
            'success': True,
            'message': f'Thank you! Your feedback helps improve recommendations.'
        })
    
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

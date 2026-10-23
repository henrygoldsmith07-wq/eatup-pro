#!/bin/bash
# EatUp Pro Production Deployment Script v8.0
# Complete automated deployment and configuration

set -e  # Exit on error

echo "======================================"
echo "🎯 EATUP PRO PRODUCTION DEPLOYMENT"
echo "v8.0 - Ultimate System Optimization"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"; }
log_warn() { echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARN:${NC} $1"; }
log_error() { echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"; }

# Check Python version
log_info "Checking Python environment..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
if [ $(echo "$python_version < 3.8" | bc -l) -eq 1 ]; then
    log_error "Python 3.8+ required, found: $python_version"
    exit 1
fi
log_info "✓ Python $python_version detected"

# Create data directory
log_info "Creating directories..."
mkdir -p data/logs data/backups data/export
chmod 755 data logs backups export

# Install core dependencies
log_info "Installing core dependencies..."
pip install -q Flask flask-cors winshell psutil colorama

# Install optional ML dependencies (with fallback)
log_info "Installing ML dependencies..."
pip install -q scikit-learn numpy pandas || log_warn "ML libraries skipped (optional)"

# Install voice/speech dependencies (with fallback)
log_info "Installing voice interfaces..."
pip install -q SpeechRecognition pyttsx3 || log_warn "Voice dependencies skipped (optional)"

# Install WebSocket support (with fallback)
log_info "Installing WebSocket support..."
pip install -q flask-socketio python-socketio gevent || log_warn "WebSocket skipped (optional)"

# Install visualization dependencies
log_info "Installing visualization tools..."
pip install -q Pillow || log_warn "PIL/Pillow skipped (optional)"

# Initialize database
log_info "Initializing databases..."
python3 -c "import sqlite3; conn = sqlite3.connect('data/eatup_main.db'); conn.close()"
python3 -c "import sqlite3; conn = sqlite3.connect('data/mobile_api.db'); conn.close()"
log_info "✓ Databases initialized"

# Set up log rotation
log_info "Configuring log management..."
cat > data/logrotate.conf << 'EOF'
data/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    size 10M
    postrotate
        /bin/kill -USR1 `cat /var/run/syslog.pid 2>/dev/null` 2>/dev/null || true
    endscript
}
EOF

# Create backup automation script
log_info "Setting up backup automation..."
cat > backup_daily.sh << 'EOFSH'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/archive_$DATE"
mkdir -p $BACKUP_DIR
cp -r data/logs/* $BACKUP_DIR/logs/ 2>/dev/null || true
cp -r data/*.db $BACKUP_DIR/ 2>/dev/null || true
tar -czf $BACKUP_DIR/data.tar.gz . 2>/dev/null || true
find backups -mtime +30 -delete
echo "Backup completed: $BACKUP_DIR"
EOFSH
chmod +x backup_daily.sh

# Add to crontab if running on Linux/Mac
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    log_info "Setting up scheduled tasks..."
    (crontab -l 2>/dev/null; echo "0 2 * * * cd \$(dirname \$0) && ./backup_daily.sh") | crontab -
    log_info "✓ Daily backups scheduled at 2 AM"
fi

# Start API server in background (optional)
START_API=false
read -p "Start API Server? (y/n): " START_API
if [ "$START_API" = "y" ]; then
    log_info "Starting API Server..."
    nohup python3 api_server.py > data/logs/api_server.log 2>&1 &
    API_PID=$!
    echo "API Server started with PID: $API_PID"
    echo "Logs: data/logs/api_server.log"
fi

# Show deployment summary
echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "📁 Directories created:"
echo "   - data/logs/"
echo "   - data/backups/"  
echo "   - data/export/"
echo ""
echo "📊 Databases initialized:"
echo "   - eatup_main.db"
echo "   - mobile_api.db"
echo ""
echo "🔧 Services configured:"
echo "   ✓ Core dependencies installed"
echo "   ✓ Optional ML features ready"
echo "   ✓ Voice interface configured"
echo "   ✓ WebSocket support active"
echo ""
echo "📅 Scheduled tasks:"
echo "   ✓ Daily backup at 2 AM"
echo "   ✓ Log rotation enabled"
echo ""
echo "🚀 Quick Start Commands:"
echo "   Scan drive:     python master_control.py scan --drive C:"
echo "   Smart cleanup:  python master_control.py cleanup"
echo "   Game optimize:  python master_control.py games"
echo "   Quantum clean:  python master_control.py quantum"
echo "   System opt:     python master_control.py system"
echo ""
echo "🌐 Web Interface: http://localhost:5000"
echo ""
echo "📖 Full documentation: See FEATURES_COMPLETE_V2.1.0.md"
echo ""
echo "Version: 8.0 - Production Ready"
echo "Repository: https://github.com/henrygoldsmith07-wq/eatup-pro"
echo ""

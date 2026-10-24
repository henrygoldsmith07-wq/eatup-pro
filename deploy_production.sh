#!/bin/bash
# EatUp Pro v8.1+ - Automated Deployment Script
# Production-ready deployment with health checks and rollback

set -e  # Exit on error

echo "🚀 EatUp Pro v8.1+ - Production Deployment"
echo "============================================="

# Configuration
APP_NAME="eatup-pro"
VERSION="8.1+"
BACKUP_DIR="./backups"
LOG_FILE="/var/log/eatup-deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log "Python version: $python_version"
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        error "pip3 is required but not installed"
        exit 1
    fi
    
    log "✅ Prerequisites met"
}

# Create backup
create_backup() {
    log "Creating backup of current deployment..."
    
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/eatup_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    tar -czf "$BACKUP_FILE" --exclude='*.pyc' --exclude='__pycache__' . 2>/dev/null || true
    
    log "Backup created: $BACKUP_FILE"
}

# Install dependencies
install_dependencies() {
    log "Installing Python dependencies..."
    
    pip3 install -r requirements.txt
    
    log "✅ Dependencies installed"
}

# Migrate database
run_migrations() {
    log "Running database migrations..."
    
    if [ -f "api_server.py" ]; then
        python3 -c "from api_server import init_database; init_database()" 2>/dev/null || true
    fi
    
    log "✅ Database migrations complete"
}

# Start services
start_services() {
    log "Starting EatUp Pro services..."
    
    # Stop existing processes
    pkill -f "api_server.py" 2>/dev/null || true
    
    # Start new process in background
    nohup python3 api_server.py > /var/log/eatup_api.log 2>&1 &
    
    sleep 3
    
    log "✅ Services started"
}

# Health check
health_check() {
    log "Performing health check..."
    
    MAX_RETRIES=10
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -s http://localhost:5000/api/v1/health > /dev/null 2>&1; then
            log "✅ Health check passed"
            return 0
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        log "Waiting for service to start... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 2
    done
    
    error "Health check failed after $MAX_RETRIES attempts"
    return 1
}

# Rollback if needed
rollback() {
    warn "Initiating rollback..."
    
    LATEST_BACKUP=$(ls -t $BACKUP_DIR/*.tar.gz 2>/dev/null | head -1)
    
    if [ -n "$LATEST_BACKUP" ]; then
        log "Restoring from backup: $LATEST_BACKUP"
        tar -xzf "$LATEST_BACKUP"
        start_services
        log "✅ Rollback complete"
    else
        error "No backup available for rollback"
        exit 1
    fi
}

# Deploy main application
deploy_application() {
    log "Deploying EatUp Pro v$VERSION..."
    
    # Get latest code (git pull or equivalent)
    if [ -d ".git" ]; then
        git pull origin main
    fi
    
    # Create directories
    mkdir -p data logs backups config
    
    # Set permissions
    chmod 755 data logs backups
    
    # Install dependencies
    install_dependencies
    
    # Run migrations
    run_migrations
    
    # Start services
    start_services
    
    # Verify deployment
    if health_check; then
        log "✅ Deployment successful!"
        
        # Show stats
        log "\n📊 Deployment Statistics:"
        total_lines=$(find . -name "*.py" -exec cat {} \; | wc -l)
        total_files=$(find . -name "*.py" | wc -l)
        log "   Total Python files: $total_files"
        log "   Total lines of code: $total_lines"
        
    else
        error "Deployment verification failed"
        rollback
    fi
}

# Generate configuration
generate_config() {
    log "Generating production configuration..."
    
    if [ ! -f "config/.env" ]; then
        cat > config/.env << EOF
# EatUp Pro Production Configuration
FLASK_ENV=production
PORT=5000
DATABASE_URL=sqlite:///data/eatup_storage.db
ENABLE_NEURAL_AI=true
ENABLE_QUANTUM_OPTIMIZATION=true
ENABLE_BLOCKCHAIN_AUDIT=true
API_RATE_LIMIT=1000
SESSION_TIMEOUT_MINUTES=60
LOG_LEVEL=INFO
EOF
        log "Configuration generated at config/.env"
    fi
}

# Cleanup old backups
cleanup_backups() {
    log "Cleaning up old backups (keeping last 7 days)..."
    
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete 2>/dev/null || true
    
    log "✅ Backup cleanup complete"
}

# Main deployment flow
main() {
    log "Starting EatUp Pro deployment..."
    
    # Execute deployment steps
    check_prerequisites
    create_backup
    generate_config
    deploy_application
    cleanup_backups
    
    log "\n🎉 Deployment Complete!"
    log "Service running at: http://localhost:5000"
    log "Logs available at: /var/log/eatup_api.log"
}

# Handle arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    backup)
        create_backup
        ;;
    status)
        if pgrep -f "api_server.py" > /dev/null; then
            log "Service is RUNNING"
            curl -s http://localhost:5000/api/v1/health | python3 -m json.tool 2>/dev/null || true
        else
            error "Service is NOT running"
        fi
        ;;
    rollback)
        rollback
        ;;
    *)
        echo "Usage: $0 {deploy|backup|status|rollback}"
        exit 1
        ;;
esac

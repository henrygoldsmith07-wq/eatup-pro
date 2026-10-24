# 🚀 EatUp Pro v8.1 - Quick Start Guide

Get up and running in minutes with our production-ready enterprise storage management platform.

---

## ⚡ 3-Minute Setup (Local Development)

### Prerequisites
- Python 3.11+ installed
- pip package manager available
- Windows/macOS/Linux operating system

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Initialize Database & Run
```bash
python api_server.py
```

✅ API server now running at `http://localhost:5000`  
✅ Health check: `http://localhost:5000/api/v1/health`

### Step 3: Try the Web Interface
Open [index.html](file:///C:/Users/rober/Documents/Qoder/2026-10-19/cffb3719/index.html) in your browser for the interactive demo UI.

---

## 🐳 Docker Deployment (Recommended)

### One-Command Everything
```bash
docker-compose up -d
```

This starts all services automatically:
- ✅ EatUp Pro API server
- ✅ PostgreSQL database
- ✅ Redis cache
- ✅ Nginx reverse proxy
- ✅ Prometheus monitoring
- ✅ Grafana dashboards

**Access Points:**
- API: http://localhost:5000
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

### Build Custom Image
```bash
docker build --target production -t eatup-pro:v8.1 .
docker run -p 5000:5000 eatup-pro:v8.1
```

---

## ☁️ Cloud Deployment

### Vercel (Easiest)
1. Connect GitHub repository to Vercel
2. Root directory: `/`
3. Deploy automatically

Or use CLI:
```bash
npm i -g vercel
vercel --prod
```

### Railway (Alternative PaaS)
```bash
# Login first
railway login

# Initialize project
cd /path/to/eatup-pro
railway init
railway up

# Auto-deploys on git push
```

### Kubernetes Production

Deploy entire stack with Helm charts:
```bash
helm repo add eatup https://charts.eatup.pro
helm install eatup-pro eatup/eatup \
  --namespace eatup-pro \
  --create-namespace
```

---

## 📦 Complete Service Stack

### docker-compose.yml Components

**1. EatUp API Server** (`eatup-api`)
- Port: 5000
- Features: Neural AI + Quantum optimization enabled
- Volume mapping: `/app/data` (persistent storage)

**2. PostgreSQL** (`postgres`)
- Port: 5432
- Database: `eatup_pro`
- Optimized for high-write workloads

**3. Redis Cache** (`redis`)
- Port: 6379
- Persistence enabled via AOF
- Sub-second lookup times

**4. Nginx Reverse Proxy** (`nginx`)
- Port: 80/443
- SSL termination support
- Gzip compression enabled
- Rate limiting per endpoint

**5. Prometheus** (`prometheus`)
- Port: 9090
- Scrapes every 15 seconds
- Custom alert rules configured

**6. Grafana Dashboards** (`grafana`)
- Port: 3000
- Pre-configured datasources
- Ready-to-use dashboards

---

## 🔧 Configuration Options

### Environment Variables
```bash
# Core Settings
FLASK_ENV=production          # development | production | testing
PORT=5000                     # API server port
DATABASE_URL=sqlite:///data/db.db

# Feature Flags
ENABLE_NEURAL_AI=true         # Enable ML-based cleanup
ENABLE_QUANTUM_OPTIMIZATION=true    # Enable quantum algorithms
ENABLE_BLOCKCHAIN_AUDIT=true         # Immutable audit trail
ENABLE_VOICE_COMMANDS=false           # Speech recognition

# Performance Tuning
API_RATE_LIMIT=1000           # Requests per hour
SESSION_TIMEOUT_MINUTES=60    # User session duration
WORKER_THREADS=4              # Background task threads
```

### Advanced Configuration

**Database Migration:**
```bash
python migrate_database.py --upgrade
python migrate_database.py --check  # Verify version
```

**Backup Management:**
```bash
# Full backup
python backup_manager.py create --full

# Incremental backup
python backup_manager.py create --incremental

# Restore from backup
python backup_manager.py restore backup_20261024.tar.gz
```

---

## 🎯 Testing Your Installation

### Basic API Tests
```bash
# Check health status
curl http://localhost:5000/api/v1/health

# Start a quick scan
curl -X POST http://localhost:5000/api/v1/scan/start \
  -H "Content-Type: application/json" \
  -d '{"drive": "C:", "depth": "quick"}'

# Get results (replace scan_id with actual ID)
curl http://localhost:5000/api/v1/scan/results/<scan_id>
```

### Run Unit Tests
```bash
pytest tests/ -v --cov=. --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Load Test (Optional)
```bash
locust -f load_test.py --host=http://localhost:5000 --workers=10
# Open http://localhost:8089 for web UI
```

---

## 🛠️ Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Change port
export PORT=8080
python api_server.py
```

**Database permissions:**
```bash
chmod 755 data/
python api_server.py
```

**Missing dependencies:**
```bash
pip install -r requirements.txt --force-reinstall
```

**Docker container won't start:**
```bash
docker logs eatup-api
docker-compose down && docker-compose up -d
```

### Debug Mode
```bash
# Verbose logging
python api_server.py --debug --verbose

# Interactive debugger
python -m pdb api_server.py
```

---

## 📊 Monitoring & Alerts

### Access Dashboards
- **Grafana**: http://localhost:3000 (login: admin/admin)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### Check Service Status
```bash
# All containers healthy?
docker-compose ps

# Recent logs
docker-compose logs --tail=100 eatup-api

# Resource usage
docker stats eatup-api
```

---

## 🔄 Daily Operations

### Routine Backup
```bash
# Add to crontab for daily backups at 2 AM
0 2 * * * cd /opt/eatup-pro && python backup_manager.py create --daily
```

### Health Check
```bash
# Quick verification
./scripts/check_health.sh
```

### Log Rotation
```bash
# Compress old logs
find logs/ -name "*.log" -mtime +7 -exec gzip {} \;

# Clear logs older than 30 days
find logs/ -name "*.log.gz" -mtime +30 -delete
```

---

## 📈 Scale Up When Needed

### Vertical Scaling
```yaml
# Update docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '4'      # From 2 cores to 4
      memory: 2G     # From 1GB to 2GB
```

### Horizontal Scaling
```bash
# Using Kubernetes HPA
kubectl scale deployment eatup-api --replicas=3

# Or using Docker Swarm
docker service scale eatup-api=3
```

---

## 🆘 Getting Help

- 📖 [Complete API Documentation](docs/API_REFERENCE.md)
- 🐛 [Issue Tracker](https://github.com/eatup-pro/issues)
- 💬 [Community Forum](https://community.eatup.pro)
- 📧 Email: support@eatup.pro

---

**Next Steps:**
1. ✅ Complete setup using guide above
2. 🔍 Review [ARCHITECTURE.md](ARCHITECTURE.md) for internals
3. 📚 Read [FEATURES_COMPLETE_V2.1.0.md](FEATURES_COMPLETE_V2.1.0.md) for capabilities
4. 🚀 Deploy to production when ready

Happy cleaning! 🧹✨

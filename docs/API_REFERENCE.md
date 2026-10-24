# EatUp Pro API Reference v8.0

Complete REST API documentation for EatUp Pro Enterprise Storage Management Platform.

## Base URL
```
Production: https://your-domain.vercel.app
Local Development: http://localhost:5000
```

## Authentication
Most endpoints require authentication via Bearer token (optional for demo mode):

```javascript
headers: {
  'Authorization': 'Bearer YOUR_API_KEY',
  'Content-Type': 'application/json'
}
```

---

## Health & Status Endpoints

### Check API Health
```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "8.0.0",
  "uptime": 3600,
  "modules": {
    "neural_cleaner": true,
    "quantum_optimizer": true,
    "blockchain_ledger": true,
    "edge_orchestrator": true
  }
}
```

---

## Scan Operations

### Start Disk Scan
```http
POST /api/v1/scan/start
```

**Body:**
```json
{
  "drive": "C:",
  "include_categories": ["temp", "duplicates", "large_files"],
  "scan_depth": "full"
}
```

**Response:**
```json
{
  "success": true,
  "scan_id": "scan_1234567890",
  "message": "Scan started",
  "estimated_time_seconds": 45
}
```

### Get Scan Results
```http
GET /api/v1/scan/results/{scan_id}
```

**Response:**
```json
{
  "scan_id": "scan_1234567890",
  "status": "completed",
  "timestamp": "2026-10-24T10:30:00Z",
  "total_space": 1073741824000,
  "used_space": 858993459200,
  "free_space": 214748364800,
  "categories": {
    "Applications": 400000000000,
    "Documents": 150000000000,
    "Temp Files": 50000000000,
    "Duplicates": 75000000000
  },
  "recommendations": [
    {
      "type": "temp_cleanup",
      "potential_savings": 50000000000,
      "safety_score": 0.95
    }
  ]
}
```

### Cancel Active Scan
```http
POST /api/v1/scan/cancel/{scan_id}
```

---

## Cleanup Operations

### Execute Smart Cleanup
```http
POST /api/v1/cleanup/run
```

**Body:**
```json
{
  "scan_id": "scan_1234567890",
  "cleanup_types": ["temp", "duplicates", "game_cache"],
  "delete_permanently": false,
  "auto_approve_safe": true
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "cleanup_job_987654",
  "files_processed": 1247,
  "space_reclaimed_bytes": 125000000000,
  "recycle_bin_location": "C:\\$RECYCLE.BIN\\cleanup_987654",
  "status": "completed"
}
```

### Preview Cleanup Without Executing
```http
POST /api/v1/cleanup/preview
```

**Body:** Same as `/cleanup/run` but returns planned actions without executing

---

## Game Optimization

### Scan Game Caches
```http
POST /api/v1/games/scan
```

**Body:**
```json
{
  "platforms": ["steam", "epic_games", "battle_net"],
  "clean_aggressive": false
}
```

**Response:**
```json
{
  "steam": {
    "cache_size": 5242880000,
    "files_count": 1247,
    "path": "%LOCALAPPDATA%\\Steam\\appcache"
  },
  "epic_games": {
    "cache_size": 2147483648,
    "files_count": 543,
    "path": "%LOCALAPPDATA%\\Epic\\GameCache"
  }
}
```

### Clean Game Cache
```http
POST /api/v1/games/clean
```

---

## Neural AI Cleaner

### Get AI-Powered Recommendations
```http
GET /api/v1/ai/recommendations?scan_id={scan_id}
```

**Response:**
```json
{
  "recommendations": [
    {
      "file_path": "C:\\Windows\\Logs\\debug.log",
      "size_bytes": 104857600,
      "safety_score": 0.97,
      "reasoning": "Old debug log file > 30 days",
      "priority": "high",
      "confidence": 0.94
    }
  ],
  "model_version": "rf_v2.1_xgboost_v1.7",
  "features_analyzed": 23
}
```

### Train Neural Model
```http
POST /api/v1/ai/train
```

**Body:**
```json
{
  "user_feedback_data": [
    {
      "filepath": "/path/to/file",
      "action_taken": "kept",
      "reason": "important_project_file"
    }
  ],
  "retrain_from_scratch": false
}
```

---

## Quantum Optimization

### Run Quantum-Inspired Analysis
```http
POST /api/v1/quantum/optimize
```

**Body:**
```json
{
  "algorithm": "genetic_selection",
  "population_size": 100,
  "generations": 50,
  "entanglement_threshold": 0.75
}
```

**Response:**
```json
{
  "optimization_id": "quantum_opt_123456",
  "convergence_achieved": true,
  "optimal_solution": {
    "files_to_remove": ["file1", "file2"],
    "total_savings": 125000000000,
    "risk_assessment": "low"
  },
  "quantum_metrics": {
    "superposition_states_explored": 1024,
    "entanglement_pairs_found": 47,
    "tunneling_events": 12
  }
}
```

---

## Blockchain Audit Trail

### Query Audit History
```http
GET /api/v1/blockchain/audit?limit=50
```

**Response:**
```json
{
  "entries": [
    {
      "hash": "0x4a3b...8f2c",
      "parent_hash": "0x9e1d...4a7b",
      "merkle_root": "0xc2f5...",
      "transaction_type": "file_deletion",
      "timestamp": "2026-10-24T10:30:00Z",
      "file_path": "C:\\Temp\\old_file.tmp",
      "size": 1048576,
      "proof_of_work": 472839
    }
  ],
  "current_chain_length": 1247,
  "last_block_hash": "0x4a3b...8f2c"
}
```

### Mint Achievement NFT
```http
POST /api/v1/blockchain/nft/mint
```

**Body:**
```json
{
  "achievement_type": "storage_master",
  "metadata": {
    "space_saved_gb": 150,
    "files_cleaned": 2500,
    "streak_days": 30
  }
}
```

---

## Edge IoT Orchestration

### Discover Devices
```http
POST /api/v1/edge/discover
```

**Body:**
```json
{
  "network_range": "192.168.1.0/24",
  "protocols": ["ssh", "http", "mqtt"]
}
```

**Response:**
```json
{
  "devices": [
    {
      "id": "device_001",
      "ip": "192.168.1.101",
      "type": "nas_storage",
      "hostname": "nas-home",
      "available": true,
      "protocol": "ssh"
    }
  ]
}
```

### Execute Distributed Cleanup
```http
POST /api/v1/edge/orchestrate
```

**Body:**
```json
{
  "task": {
    "type": "disk_cleanup",
    "strategy": "parallel_execution",
    "target_devices": ["device_001", "device_002"],
    "cleanup_config": {
      "max_space_to_free_gb": 10
    }
  }
}
```

---

## Predictive Analytics

### Get Storage Forecast
```http
GET /api/v1/analytics/forecast
```

**Response:**
```json
{
  "current_usage_percent": 72.5,
  "prediction": {
    "days_until_full": 145,
    "confidence_interval": {
      "lower": 120,
      "upper": 170
    }
  },
  "trend": "increasing",
  "monthly_growth_rate_gb": 125.5,
  "recommendation": {
    "action": "aggressive_cleanup",
    "urgency": "medium"
  }
}
```

---

## Scheduled Tasks

### Create New Schedule
```http
POST /api/v1/schedule/create
```

**Body:**
```json
{
  "name": "Weekly Deep Clean",
  "cron_expression": "0 2 * * 0",
  "task_type": "smart_cleanup",
  "enabled": true,
  "config": {
    "max_cleanup_size_gb": 50
  }
}
```

**Response:**
```json
{
  "schedule_id": "sched_weekly_001",
  "next_run": "2026-10-29T02:00:00Z",
  "status": "active"
}
```

### List All Schedules
```http
GET /api/v1/schedule/list
```

---

## User Management

### Get User Stats
```http
GET /api/v1/user/stats
```

**Response:**
```json
{
  "user_id": "user_123",
  "achievements": [
    {
      "id": "first_cleanup",
      "name": "First Step",
      "unlocked_at": "2026-10-01T10:00:00Z",
      "xp_awarded": 100
    }
  ],
  "level": 12,
  "total_xp": 4500,
  "lifetime_stats": {
    "total_files_cleaned": 15247,
    "total_space_saved_gb": 523.7,
    "streak_days": 45
  }
}
```

---

## Real-Time WebSocket Events

Connect to WebSocket endpoint for live updates:

```javascript
const ws = new WebSocket('wss://your-domain.vercel.app/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'scan_progress') {
    console.log(`Progress: ${data.progress}% (${data.files_scanned}/${data.total_files})`);
  } else if (data.type === 'completion') {
    console.log('Task completed!', data.result);
  }
};
```

### Available Event Types:
- `scan_progress` - Real-time scan updates
- `cleanup_progress` - Cleanup job status
- `achievement_unlocked` - New badge earned
- `system_alert` - Critical notifications
- `forecast_update` - Storage predictions

---

## Error Responses

All errors follow consistent format:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "Drive parameter must be C: or D:",
    "details": {
      "field": "drive",
      "value": "X:"
    }
  }
}
```

**Error Codes:**
- `AUTH_REQUIRED` - Authentication needed
- `INVALID_INPUT` - Malformed request parameters
- `OPERATION_IN_PROGRESS` - Another task is running
- `INSUFFICIENT_PERMISSIONS` - Access denied
- `RESOURCE_NOT_FOUND` - Resource doesn't exist
- `RATE_LIMIT_EXCEEDED` - Too many requests

---

## Rate Limiting

- Free tier: 100 requests/hour
- Pro tier: 1000 requests/hour
- Enterprise: Unlimited

Headers included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1635123456
```

---

## SDK Examples

### JavaScript/TypeScript
```javascript
import { EatUpClient } from '@eatup/sdk';

const client = new EatUpClient({ apiKey: 'your_api_key' });

// Scan drive
const scan = await client.scans.start({ drive: 'C:' });
const results = await client.scans.get(scan.id);

// Cleanup
const cleanup = await client.cleanup.run({
  scanId: scan.id,
  types: ['temp', 'duplicates']
});

console.log(`Reclaimed ${cleanup.spaceReclaimed / 1024 / 1024 / 1024} GB`);
```

### Python
```python
from eatup import EatUpClient

client = EatUpClient(api_key='your_api_key')

# Quick scan
result = client.scan_drive('C:')
print(f"Found {result.total_used / 1024**2:.2f} MB used")

# Smart cleanup
cleanup = client.smart_cleanup()
print(f"Saved {cleanup.reclaimed_mb} MB")
```

### cURL
```bash
# Start scan
curl -X POST https://api.eatup.pro/api/v1/scan/start \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{"drive": "C:"}'

# Check health
curl https://api.eatup.pro/api/v1/health
```

---

## Webhook Support

Configure webhooks for server-side integration:

```http
POST /api/v1/webhooks
```

**Body:**
```json
{
  "url": "https://your-app.com/webhook",
  "events": ["scan.completed", "cleanup.finished", "achievement.unlocked"],
  "secret": "whsec_your_secret_key"
}
```

**Webhook Payload:**
```json
{
  "event": "scan.completed",
  "timestamp": "2026-10-24T10:30:00Z",
  "data": {
    "scan_id": "scan_123",
    "results": {...}
  }
}
```

---

## Version History

- **v8.0** - Current (Quantum optimization, blockchain ledger)
- **v7.5** - Added neural network AI
- **v7.0** - Mobile backend API
- **v6.0** - Gamification system
- **v5.0** - Edge IoT orchestration
- **v2.1** - AR visualization export

Support policy: Latest 2 versions maintained

---

Need help? Contact: support@eatup.pro
GitHub: github.com/your-org/eatup-pro

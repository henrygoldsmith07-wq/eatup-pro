# EatUp Pro - Vercel Deployment Guide 🚀

Complete guide for deploying EatUp Pro to Vercel.

## Prerequisites

✅ GitHub account (already created)  
✅ Vercel account (free tier recommended)  
✅ Git repository initialized  

## Quick Deploy Steps

### 1. Install Vercel CLI (Optional but Recommended)

```bash
npm install -g vercel
```

### 2. Login to Vercel

```bash
vercel login
```

Follow the prompts to authenticate with GitHub.

### 3. Deploy from Command Line

```bash
# Go to project directory
cd C:\Users\rober\Documents\Qoder\2026-10-19\cffb3719

# Deploy directly
vercel --prod

# Or deploy to preview first
vercel
```

### 4. Deploy via Vercel Dashboard (Alternative Method)

1. Go to https://vercel.com/new
2. Import your GitHub repository: `henrygoldsmith07-wq/eatup-pro`
3. Click "Deploy"
4. Configure environment variables if needed

## Configuration

### Environment Variables

Create these in Vercel Dashboard → Settings → Environment Variables:

```bash
API_KEY=your-secret-api-key-here  # Optional for authentication
DEBUG=false                       # Set to false for production
PORT=8080                         # Default port
```

### Project Settings

**Framework Preset**: Other  
**Build Command**: `echo "No build step required"`  
**Output Directory**: `.` (current directory)  
**Install Command**: (none needed - Python packages installed at runtime)

## Deployment Options

### Option 1: Static Site Only (Recommended for Landing Pages)

If you only want to host the static HTML/CSS/JS:

```bash
vercel --static
```

This deploys just the web interface without backend functionality.

### Option 2: Full Application with Backend

For the complete app with API server:

Vercel Functions will run the Python backend. You'll need to convert Flask API endpoints to Vercel Functions format.

See **Advanced Setup** below for details.

## Advanced Setup: Python Backend on Vercel

### Convert Flask Routes to Vercel Functions

Create `api/v1/[endpoint].py` for each route:

**Example: api/v1/[health].py**
```python
import json
from datetime import datetime

def handler(request):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'status': 'healthy',
            'version': '2.0.0',
            'timestamp': datetime.now().isoformat()
        })
    }
```

**Example: api/v1/[scan]/[start].py**
```python
import json
from cleaner import EatUpCleaner
import threading

def handler(request):
    def run_scan():
        cleaner = EatUpCleaner()
        result = cleaner.scan_drive('C:')
    
    thread = threading.Thread(target=run_scan, daemon=True)
    thread.start()
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'status': 'starting',
            'message': 'Scan started'
        })
    }
```

### Update Requirements

Add to `requirements.txt`:
```
flask>=2.0.0
psutil>=5.9.0
winshell>=7.0
schedule>=1.0.0
```

Note: Some Windows-specific packages may not work in serverless environments. Consider using AWS Lambda with Windows support or Docker containers for full functionality.

## Custom Domain

To add your own domain:

1. Go to Vercel Dashboard → Your Project → Domains
2. Add custom domain (e.g., `eatup.yourdomain.com`)
3. Follow DNS configuration instructions
4. Wait for SSL certificate provisioning (~24 hours)

## Continuous Deployment

Vercel automatically deploys on every git push to main branch! 

Your repository: https://github.com/henrygoldsmith07-wq/eatup-pro

Changes made to main branch will trigger automatic deployments.

## Environment-Specific Configs

### Development (.env.local)
```
PORT=8080
DEBUG=true
API_KEY=dev-key
```

### Production (.env.production)
```
PORT=8080
DEBUG=false
API_KEY=production-key
```

## Monitoring

After deployment, monitor your application:

1. **Vercel Dashboard**: https://vercel.com/dashboard
   - View deployment logs
   - Check function execution times
   - Monitor errors and performance

2. **Analytics**: Enable Vercel Analytics in project settings

## Troubleshooting

### Issue: Python Package Not Found

**Solution**: Ensure `requirements.txt` is in root and list all dependencies.

### Issue: Build Timeout

**Solution**: Increase build timeout in `vercel.json`:
```json
{
  "build": {
    "env": {
      "BUILD_TIMEOUT_SECONDS": 300
    }
  }
}
```

### Issue: Database/File Access Issues

**Solution**: Use Vercel's blob storage or external database instead of local filesystem.

## Cost

**Free Tier includes**:
- ✅ 100GB bandwidth/month
- ✅ 100GB storage
- ✅ 1,000 build minutes/month
- ✅ Community support

Perfect for EatUp Pro! 🎉

## Next Steps After Deployment

1. Share your live URL with users
2. Set up custom domain (optional)
3. Configure analytics
4. Monitor usage metrics
5. Plan next features based on user feedback

---

**Deployment URL Example**: 
https://eatup-pro.vercel.app

Ready to launch! 🚀

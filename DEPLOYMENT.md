# Deployment Guide

## Vercel Deployment

### Configuration Fixed

The Vercel deployment error regarding `routes` vs `rewrites` has been fixed:
- Created `vercel.json` using `rewrites` instead of `routes`
- Set up proper API routing structure in `/api/index.py`
- Configured static frontend serving

### Important Limitations

**⚠️ CRITICAL: System Dependencies Not Supported on Vercel**

This application requires system-level dependencies that are **NOT available** on Vercel's serverless platform:

1. **Tesseract OCR** - Required for processing scanned PDFs
2. **Poppler Utils** - Required for `pdf2image` library

**Result**: The application will deploy to Vercel but the `/convert` endpoint will **FAIL** when processing PDFs because these dependencies are missing.

### Recommended Deployment Platforms

For full functionality, deploy to platforms that support system dependencies:

#### 1. **Railway** (Recommended)
- Supports Docker containers
- Can install system packages
- Easy deployment from GitHub

```bash
# Use the existing Dockerfile
railway up
```

#### 2. **Render**
- Native Docker support
- Free tier available
- Build from Dockerfile

#### 3. **Fly.io**
- Full Docker support
- Global edge network
- `fly launch` for quick deployment

#### 4. **Google Cloud Run**
- Container-based deployment
- Serverless but with full system access
- Pay per use

```bash
gcloud run deploy nashville-converter \
  --source . \
  --platform managed \
  --allow-unauthenticated
```

#### 5. **AWS App Runner**
- Container deployment
- Auto-scaling
- Direct GitHub integration

### Alternative: Vercel + External Processing Service

If you must use Vercel, consider:
1. Deploy frontend to Vercel
2. Deploy backend (with dependencies) to Railway/Render
3. Update frontend `apiUrl` to point to external backend
4. Configure CORS on backend to allow Vercel domain

### Files Created for Vercel

- `vercel.json` - Configuration using `rewrites` (not `routes`)
- `api/index.py` - Serverless function handler
- `api/requirements.txt` - Python dependencies
- `.vercelignore` - Exclude unnecessary files

### Testing Locally

Before deploying, test with Docker to ensure all dependencies work:

```bash
docker-compose up -d
curl -X POST http://localhost:8000/convert \
  -F "file=@test.pdf" \
  -F "key=G" \
  -F "mode=major" \
  --output result.pdf
```

### Deployment Commands

#### Vercel (limited functionality)
```bash
vercel --prod
```

#### Railway (recommended)
```bash
railway login
railway init
railway up
```

#### Render
Connect your GitHub repository in the Render dashboard and select "Docker" as build type.

### Environment Variables

No environment variables required for MVP version. Future features may require:
- `MAX_FILE_SIZE` - Maximum PDF upload size
- `TEMP_FILE_CLEANUP_MINUTES` - Cleanup delay
- `CORS_ORIGINS` - Allowed frontend domains

### Monitoring

After deployment, test the health endpoint:
```bash
curl https://your-domain.com/api/
```

Should return:
```json
{
  "status": "healthy",
  "capabilities": {
    "text_pdf_support": true,
    "ocr_support": true,
    "supported_keys": [...],
    "supported_modes": ["major", "minor"]
  }
}
```

If `ocr_support` is `false`, Tesseract is not installed.

---

**Summary**: The configuration error is fixed, but Vercel lacks required system dependencies. Use Docker-based platforms (Railway, Render, Fly.io) for full functionality.

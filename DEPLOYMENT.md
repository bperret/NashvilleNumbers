# Deployment Guide

This application is configured for **single-platform deployment on Vercel** with full-stack support (frontend + backend API).

## Overview

- **Frontend**: Static HTML/CSS/JS served from `/frontend`
- **Backend**: Python FastAPI serverless functions in `/api`
- **Platform**: Vercel (handles both frontend and backend)
- **PDF Support**: Text-based PDFs only (no OCR for scanned images)

---

## Quick Deploy to Vercel

### Prerequisites

1. A [Vercel account](https://vercel.com/signup) (free tier works)
2. Git repository hosted on GitHub, GitLab, or Bitbucket

### Deployment Steps

1. **Connect your repository to Vercel:**
   - Go to https://vercel.com/new
   - Import your Git repository
   - Vercel will auto-detect the configuration from `vercel.json`

2. **Deploy:**
   - Click "Deploy"
   - Vercel will build and deploy both frontend and backend
   - You'll get a URL like `https://your-app.vercel.app`

3. **Test:**
   - Visit your Vercel URL
   - Upload a text-based PDF chord chart
   - Convert and download the Nashville Numbers version

That's it! Your app is live.

---

## Manual Deployment with Vercel CLI

If you prefer using the command line:

### Install Vercel CLI

```bash
npm install -g vercel
```

### Login to Vercel

```bash
vercel login
```

### Deploy

```bash
# From project root
vercel --prod
```

The CLI will:
1. Build the Python serverless functions
2. Deploy the static frontend
3. Configure routes automatically
4. Provide you with a production URL

---

## How It Works

### Architecture

```
┌─────────────────────────────────────┐
│         Vercel Platform              │
│                                      │
│  ┌────────────┐    ┌─────────────┐  │
│  │  Frontend  │    │   Backend   │  │
│  │  (Static)  │───▶│ (Serverless)│  │
│  │            │    │   Python    │  │
│  └────────────┘    └─────────────┘  │
│                                      │
│  Routes:                             │
│  /           → frontend/index.html   │
│  /api/*      → api/index.py          │
└─────────────────────────────────────┘
```

### What Happens on Vercel

1. **Build Phase:**
   - Vercel detects `api/index.py` and builds Python serverless function
   - Static files from `/frontend` are prepared for CDN serving
   - Dependencies from `requirements.txt` are installed

2. **Runtime:**
   - Frontend requests go to static files (instant CDN delivery)
   - API requests to `/api/*` invoke the Python serverless function
   - Each API call runs in an isolated serverless container
   - Results are streamed back to the client

3. **Scaling:**
   - Automatic scaling based on traffic
   - No server management required
   - Pay only for actual usage

---

## Configuration Files

### `vercel.json`

Configures routing and builds:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    },
    {
      "src": "frontend/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "/frontend/$1"
    }
  ]
}
```

### `requirements.txt`

Python dependencies installed by Vercel:

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pdfplumber==0.10.3
reportlab==4.0.9
PyPDF2==3.0.1
Pillow==10.2.0
# ... other dependencies
```

---

## Limitations

### Text-Based PDFs Only

**OCR is disabled** because Vercel's serverless environment doesn't support system dependencies like Tesseract OCR.

✅ **Supported:** PDFs with selectable text (most chord charts)
❌ **Not Supported:** Scanned images or photos of chord charts

If you upload a scanned PDF, you'll get an error message asking for a text-based version.

### Alternative for Scanned PDFs

If you need OCR support:

1. **Use a separate OCR service** (e.g., Google Cloud Vision API, AWS Textract)
2. **Deploy backend to Docker platform** (Railway, Render, Fly.io) with system dependencies
3. **Pre-process PDFs** using online OCR tools before uploading

---

## Environment Variables

### Optional Configuration

You can set these in the Vercel dashboard under "Settings" → "Environment Variables":

- `MAX_FILE_SIZE`: Maximum PDF size in bytes (default: 10485760 = 10MB)
- `TEMP_DIR`: Temporary file storage path (default: `/tmp/nashville_converter`)

### CORS Settings

By default, CORS is open (`allow_origins=["*"]`). For production, you may want to restrict this.

Edit `backend/api/main.py` line 38:

```python
allow_origins=["https://your-app.vercel.app"],
```

Then redeploy:

```bash
git commit -am "Restrict CORS"
git push
# Vercel auto-deploys on push
```

---

## Monitoring & Logs

### Vercel Dashboard

Access logs and metrics at https://vercel.com/dashboard:

1. **Deployments:** See build logs and deployment history
2. **Functions:** Monitor serverless function invocations
3. **Analytics:** View traffic and performance metrics

### Command Line Logs

```bash
# Stream logs in real-time
vercel logs --follow

# View specific deployment logs
vercel logs [deployment-url]
```

---

## Troubleshooting

### Build Failures

**Problem:** Vercel build fails with dependency errors

**Solution:**
- Check `requirements.txt` for incompatible versions
- Ensure no system dependencies (like tesseract-ocr) are required
- Review build logs in Vercel dashboard

### API Timeout

**Problem:** "Function execution timed out"

**Solution:**
- Vercel has a 10-second timeout for Hobby tier (60s for Pro)
- Large PDFs may exceed this limit
- Consider upgrading to Pro tier or splitting large PDFs

### CORS Errors

**Problem:** Browser blocks API requests with CORS error

**Solution:**
- Ensure `allow_origins` in `backend/api/main.py` includes your domain
- Check that Vercel URL matches the CORS configuration
- Clear browser cache and try again

### "Scanned PDF" Error

**Problem:** "This PDF appears to be a scanned image"

**Solution:**
- This is expected behavior (OCR is disabled)
- Use a text-based PDF with selectable text
- Or use an online OCR tool to convert the scanned PDF first

---

## Local Development

### Run Locally

```bash
# Start backend
uvicorn backend.api.main:app --reload --port 8000

# In another terminal, serve frontend
cd frontend
python -m http.server 3000
```

Visit http://localhost:3000

### Test API Locally

```bash
# Health check
curl http://localhost:8000/

# Test conversion
curl -X POST http://localhost:8000/convert \
  -F "file=@test.pdf" \
  -F "key=G" \
  -F "mode=major" \
  --output result.pdf
```

---

## Cost Estimate

### Vercel Pricing (as of 2024)

**Hobby (Free) Tier:**
- Unlimited websites
- 100 GB-hours of serverless function execution
- 100 GB bandwidth
- Perfect for personal projects and demos

**Pro Tier ($20/month):**
- 1,000 GB-hours of serverless function execution
- 1 TB bandwidth
- 60-second function timeout (vs 10s for Hobby)
- Better for production apps with traffic

**Typical Usage:**
- Converting a 5-page PDF: ~2-3 seconds execution time
- ~1,200-1,800 conversions per month on free tier
- Bandwidth: ~50KB per PDF, supports ~2M conversions/month

---

## Security Best Practices

### Production Checklist

- [ ] Update CORS settings to whitelist only your domain
- [ ] Enable Vercel's built-in DDoS protection
- [ ] Set up rate limiting (consider adding middleware)
- [ ] Monitor function invocations for abuse
- [ ] Keep dependencies updated (automated with Dependabot)
- [ ] Use environment variables for sensitive config

### Rate Limiting Example

Add to `backend/api/main.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/convert")
@limiter.limit("10/minute")
async def convert_pdf(...):
    # ... existing code
```

---

## Updates & Maintenance

### Automatic Deployments

Vercel automatically deploys when you push to your Git repository:

```bash
git add .
git commit -m "Update feature"
git push origin main
# Vercel automatically deploys
```

### Manual Deployments

```bash
vercel --prod
```

### Rollback

```bash
# List deployments
vercel ls

# Rollback to specific deployment
vercel rollback [deployment-url]
```

---

## Need Help?

- **Vercel Docs:** https://vercel.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Project Issues:** [Your GitHub Issues Page]

---

Happy deploying! 🚀

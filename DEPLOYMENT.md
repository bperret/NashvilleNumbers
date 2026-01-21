# Deployment Guide

This application requires a **hybrid deployment** because the backend needs system dependencies (Tesseract OCR, poppler-utils) that aren't available on Vercel.

## Recommended Deployment Strategy

### Frontend → Vercel (Static Site)
### Backend → Railway/Render/Fly.io (Docker Support)

---

## Option 1: Railway (Recommended)

Railway supports Docker and all system dependencies out of the box.

### Backend Deployment (Railway)

1. **Create a Railway account** at https://railway.app
2. **Deploy from GitHub:**
   ```bash
   # Railway will auto-detect the Dockerfile
   # Click "New Project" → "Deploy from GitHub"
   # Select your repository
   ```
3. **Set the root directory** to `/` (Railway will use the Dockerfile)
4. **Note your Railway API URL** (e.g., `https://your-app.up.railway.app`)

### Frontend Deployment (Vercel)

1. **Deploy to Vercel:**
   ```bash
   # From your local machine
   vercel --prod
   ```

2. **Update the frontend to use your Railway backend:**

   Edit `frontend/index.html` line 422 and replace with your Railway URL:
   ```javascript
   const apiUrl = 'https://your-app.up.railway.app/convert';
   ```

3. **Enable CORS on Railway backend:**

   Update `backend/api/main.py` line 38:
   ```python
   allow_origins=["https://your-vercel-domain.vercel.app"],
   ```

4. **Redeploy both services**

---

## Option 2: Render

Similar to Railway, Render supports Docker deployments.

### Backend Deployment (Render)

1. **Create a Render account** at https://render.com
2. **New Web Service:**
   - Connect your GitHub repo
   - Select "Docker" as the environment
   - Set the root directory to `/`
   - Render will auto-detect the Dockerfile
3. **Note your Render API URL** (e.g., `https://your-app.onrender.com`)

### Frontend Deployment (Vercel)

Same steps as Option 1, but use your Render URL instead.

---

## Option 3: Fly.io

Best for global edge deployment.

### Backend Deployment (Fly.io)

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login and launch:**
   ```bash
   fly auth login
   fly launch
   ```

3. **Deploy:**
   ```bash
   fly deploy
   ```

4. **Get your app URL:**
   ```bash
   fly status
   ```

### Frontend Deployment (Vercel)

Same steps as Option 1, but use your Fly.io URL.

---

## Option 4: All-in-One on Railway/Render

Deploy both frontend and backend together on Railway or Render using Docker Compose or nginx.

### Railway

1. Add a `railway.toml`:
   ```toml
   [build]
   builder = "dockerfile"
   dockerfilePath = "Dockerfile"

   [deploy]
   startCommand = "docker-compose up"
   ```

2. Deploy from GitHub on Railway

### Render

1. Use the existing `docker-compose.yml`
2. Deploy as a "Background Worker" on Render
3. Expose port 3000 for the frontend

---

## Environment Variables

### Backend (Railway/Render/Fly)

No environment variables needed for MVP. For production:
- `ALLOWED_ORIGINS` - Comma-separated list of frontend URLs
- `MAX_FILE_SIZE` - Maximum PDF size in bytes (default: 10MB)
- `TEMP_DIR` - Temporary file storage path (default: /tmp/nashville_converter)

### Frontend (Vercel)

No build-time environment variables needed. The API URL is hardcoded in `index.html`.

For production, consider using environment variables:
```javascript
const apiUrl = process.env.API_URL || 'http://localhost:8000/convert';
```

---

## Why Not Vercel for Backend?

Vercel's Python runtime has limitations:
1. **No system dependencies** - Can't install Tesseract OCR or poppler-utils
2. **50MB deployment limit** - Dependencies exceed this
3. **Serverless architecture** - Not ideal for file processing with temporary storage
4. **10-second timeout** - OCR processing can take longer

Railway, Render, and Fly.io support full Docker containers with persistent processes.

---

## Configuration Validation

Before deploying, validate your Vercel configuration to ensure there are no conflicts:

```bash
# Run the validation script
python3 validate_vercel_config.py
```

### Common Configuration Conflicts

**Vercel Configuration Conflict**: The legacy `routes` property cannot be used alongside modern routing properties:
- `rewrites`
- `redirects`
- `headers`
- `cleanUrls`
- `trailingSlash`

If you need both routing and headers/redirects, use `rewrites` instead of `routes`.

**Example - Correct Configuration:**
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" }
      ]
    }
  ]
}
```

**Example - Incorrect Configuration:**
```json
{
  "routes": [
    { "src": "/(.*)", "dest": "/index.html" }
  ],
  "headers": [...]  // ❌ CONFLICT - Cannot use both!
}
```

---

## Testing Deployment

### Test Backend API

```bash
# Health check
curl https://your-backend-url.com/

# Test conversion
curl -X POST https://your-backend-url.com/convert \
  -F "file=@test.pdf" \
  -F "key=G" \
  -F "mode=major" \
  --output result.pdf
```

### Test Frontend

1. Open your Vercel URL in a browser
2. Upload a PDF
3. Select key and mode
4. Click "Convert"
5. Verify the converted PDF downloads

---

## Monitoring

### Railway
- Built-in logs and metrics dashboard
- View at https://railway.app/project/your-project

### Render
- Logs available in the Render dashboard
- Metrics and health checks included

### Fly.io
- Use `fly logs` to view logs
- Metrics at https://fly.io/dashboard

---

## Costs

### Railway
- Free tier: 500 hours/month ($5 worth)
- Hobby plan: $5/month for more resources

### Render
- Free tier: Available with limitations
- Starter plan: $7/month

### Fly.io
- Free tier: 3 shared VMs
- Pay-as-you-go after that

### Vercel (Frontend)
- Free tier: Unlimited for personal projects
- Pro: $20/month for commercial use

---

## Troubleshooting

### CORS Errors
Update `backend/api/main.py` line 38 with your Vercel domain:
```python
allow_origins=["https://your-app.vercel.app"],
```

### Backend Not Responding
Check logs on your deployment platform:
```bash
# Railway: View in dashboard
# Render: View in dashboard
# Fly.io: fly logs
```

### File Upload Fails
Ensure the backend URL in `frontend/index.html` is correct (line 422-424).

---

## Security Notes

1. **CORS**: In production, restrict `allow_origins` to your frontend domain only
2. **File Upload**: 10MB limit is enforced server-side
3. **Rate Limiting**: Consider adding rate limiting for production (e.g., using FastAPI rate limiting middleware)
4. **HTTPS**: All deployment platforms provide free SSL certificates

---

## Next Steps

1. Choose a deployment platform (Railway recommended)
2. Deploy backend to Railway/Render/Fly
3. Update frontend with backend API URL
4. Deploy frontend to Vercel
5. Test end-to-end conversion
6. Update CORS settings for security

Happy deploying! 🚀

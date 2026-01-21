# Quick Deploy Guide (5 Minutes)

Deploy your Nashville Numbers Converter to production in 5 simple steps.

## What You'll Need
- GitHub account (free)
- Railway account (free tier available) - https://railway.app
- Vercel account (free tier available) - https://vercel.com

---

## Step 1: Deploy Backend to Railway (2 minutes)

1. Go to https://railway.app and sign in with GitHub
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `NashvilleNumbers` repository
5. Railway will auto-detect the `Dockerfile` and start building
6. Wait for deployment to complete (~1-2 minutes)
7. Click **"Generate Domain"** to get your public URL
8. **Copy your Railway URL** (e.g., `https://nashvillenumbers-production.up.railway.app`)

✅ Backend is now live!

---

## Step 2: Configure Frontend for Production (1 minute)

1. Open `frontend/config.js` in your editor
2. Uncomment the last line and add your Railway URL:
   ```javascript
   window.BACKEND_URL = 'https://your-railway-url.up.railway.app';
   ```
3. Save the file
4. Commit and push:
   ```bash
   git add frontend/config.js
   git commit -m "Configure backend URL for production"
   git push
   ```

---

## Step 3: Deploy Frontend to Vercel (1 minute)

### Option A: Using Vercel CLI
```bash
# Install Vercel CLI (first time only)
npm install -g vercel

# Deploy
vercel --prod
```

### Option B: Using Vercel Dashboard
1. Go to https://vercel.com/new
2. Import your `NashvilleNumbers` GitHub repository
3. Vercel will auto-detect the configuration
4. Click **"Deploy"**
5. Wait for deployment (~30 seconds)

✅ Frontend is now live!

**Copy your Vercel URL** (e.g., `https://nashville-numbers.vercel.app`)

---

## Step 4: Update CORS Settings (1 minute)

Your backend needs to accept requests from your Vercel frontend.

1. Open `backend/api/main.py`
2. Find line 38:
   ```python
   allow_origins=["*"],  # In production, restrict to frontend domain
   ```
3. Replace with your Vercel URL:
   ```python
   allow_origins=["https://nashville-numbers.vercel.app"],
   ```
4. Commit and push:
   ```bash
   git add backend/api/main.py
   git commit -m "Update CORS for production"
   git push
   ```
5. Railway will auto-deploy the update (~1 minute)

---

## Step 5: Test Your Deployment (30 seconds)

1. Open your Vercel URL in a browser
2. Upload a sample PDF chord chart
3. Select a key (e.g., "G Major")
4. Click **"Convert to Nashville Numbers"**
5. Verify the converted PDF downloads

🎉 **You're live!**

---

## Troubleshooting

### ❌ "Failed to fetch" error
- **Check**: Is `frontend/config.js` set correctly?
- **Check**: Is your Railway backend running? Visit the Railway URL directly
- **Fix**: Update the `BACKEND_URL` in `config.js` and redeploy Vercel

### ❌ CORS error in browser console
- **Check**: Did you update `backend/api/main.py` line 38?
- **Check**: Does `allow_origins` match your Vercel URL exactly (including https://)?
- **Fix**: Update CORS settings and wait for Railway to redeploy

### ❌ Backend not responding
- **Check**: Railway deployment logs at https://railway.app
- **Check**: Is Tesseract installed? (Railway handles this automatically via Dockerfile)
- **Fix**: Try redeploying on Railway by clicking "Redeploy"

### ❌ "No chords detected"
- This is a PDF content issue, not a deployment issue
- Try a different PDF with clear chord symbols (C, Dm, G7, etc.)

---

## Cost Breakdown

### Railway (Backend)
- **Free Tier**: $5 worth of usage per month (enough for hobby use)
- **Hobby Plan**: $5/month for more resources
- **Typical usage**: ~$1-2/month for light traffic

### Vercel (Frontend)
- **Free Tier**: Unlimited for personal projects
- **Pro**: $20/month (only needed for commercial use)

**Total for hobby use**: Free to $5/month 🎉

---

## What's Next?

### Custom Domain (Optional)
Both Railway and Vercel support custom domains:
- Railway: Settings → Domains → Add Custom Domain
- Vercel: Project Settings → Domains → Add Domain

### Monitoring
- **Railway**: Built-in logs and metrics at https://railway.app
- **Vercel**: Analytics available in project dashboard

### Updates
Any commits to your main branch will auto-deploy:
- Railway: Auto-deploys backend
- Vercel: Auto-deploys frontend

---

## Support

- **Deployment Issues**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **App Issues**: See [README.md](README.md)
- **Railway Docs**: https://docs.railway.app
- **Vercel Docs**: https://vercel.com/docs

Happy deploying! 🚀

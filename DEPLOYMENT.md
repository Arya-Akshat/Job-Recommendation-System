# Deployment Guide

This guide will walk you through deploying the Job Recommendation System with:
- **Backend** on Render (Python/FastAPI)
- **Frontend** on Vercel (React/Vite)

---

## Part 1: Deploy Backend on Render

### Prerequisites
- GitHub repository pushed with latest code
- Render account (sign up at https://render.com)
- Gemini API key (from https://makersuite.google.com/app/apikey)

### Steps

#### 1.1. Prepare Backend for Render
The backend is already configured with `render.yaml`. Ensure these files exist:
- ✅ `backend/render.yaml` (created)
- ✅ `backend/requirements.txt` (exists)
- ✅ `backend/app.py` (updated with CORS)

#### 1.2. Create New Web Service on Render

1. **Go to Render Dashboard**
   - Visit https://dashboard.render.com/
   - Click **"New +"** → **"Web Service"**

2. **Connect GitHub Repository**
   - Select **"Build and deploy from a Git repository"**
   - Click **"Connect account"** if not already connected
   - Find and select your `Job-Recommendation-System` repository
   - Click **"Connect"**

3. **Configure Web Service**
   - **Name**: `job-recommendation-backend` (or your choice)
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt && python -m spacy download en_core_web_sm
     ```
   - **Start Command**: 
     ```bash
     uvicorn app:app --host 0.0.0.0 --port $PORT
     ```

4. **Set Environment Variables**
   Click **"Advanced"** → **"Add Environment Variable"**:
   
   | Key | Value |
   |-----|-------|
   | `GEMINI_API_KEY` | Your Gemini API key from Google |
   | `PYTHON_VERSION` | `3.11.0` |
   | `FRONTEND_URL` | (Leave empty for now, update after Vercel deployment) |

5. **Choose Instance Type**
   - For testing: **Free tier** (spins down after inactivity)
   - For production: **Starter ($7/month)** or higher
   - Click **"Create Web Service"**

6. **Wait for Deployment** ⏳
   - Render will build and deploy your backend
   - Monitor logs in the dashboard
   - Wait for: **"Your service is live 🎉"**
   - Note your backend URL: `https://job-recommendation-backend-XXXX.onrender.com`

#### 1.3. Test Backend API

Once deployed, test your backend:
```bash
curl https://your-backend-url.onrender.com/
```

You should see the API documentation or a response.

---

## Part 2: Deploy Frontend on Vercel

### Prerequisites
- Backend deployed and URL noted
- Vercel account (sign up at https://vercel.com)
- GitHub repository access

### Steps

#### 2.1. Prepare Frontend for Vercel
Files are already configured:
- ✅ `frontend/vercel.json` (created)
- ✅ `frontend/.env.example` (created)
- ✅ Frontend uses `VITE_API_BASE` env variable

#### 2.2. Create New Project on Vercel

1. **Go to Vercel Dashboard**
   - Visit https://vercel.com/dashboard
   - Click **"Add New..."** → **"Project"**

2. **Import Git Repository**
   - Click **"Import Git Repository"**
   - Select **"GitHub"** and authorize if needed
   - Find and select `Job-Recommendation-System`
   - Click **"Import"**

3. **Configure Project**
   - **Framework Preset**: `Vite` (should auto-detect)
   - **Root Directory**: Click **"Edit"** → Select `frontend`
   - **Build Command**: `npm run build` (or leave default)
   - **Output Directory**: `dist` (should auto-detect)
   - **Install Command**: `npm install` (or leave default)

4. **Set Environment Variables**
   Click **"Environment Variables"** section:
   
   | Key | Value |
   |-----|-------|
   | `VITE_API_BASE` | Your Render backend URL (e.g., `https://job-recommendation-backend-xxxx.onrender.com`) |

   ⚠️ **Important**: Remove trailing slash from URL

5. **Deploy**
   - Click **"Deploy"**
   - Wait for build to complete (~2-3 minutes)
   - Note your frontend URL: `https://your-app-name.vercel.app`

#### 2.3. Update Backend CORS (Important!)

Now that you have the Vercel URL, update the backend:

1. **Go back to Render Dashboard**
   - Open your `job-recommendation-backend` service
   - Go to **"Environment"** tab
   - Add/Update environment variable:
     - Key: `FRONTEND_URL`
     - Value: `https://your-app-name.vercel.app`
   - Click **"Save Changes"**

2. **Trigger Redeploy**
   - Go to **"Manual Deploy"** → **"Deploy latest commit"**
   - Wait for redeploy to complete

---

## Part 3: Verify Deployment

### 3.1. Test Backend
```bash
# Health check
curl https://your-backend-url.onrender.com/

# Test endpoint (should return job recommendations)
curl -X POST https://your-backend-url.onrender.com/recommend_jobs \
  -H "Content-Type: application/json" \
  -d '{"user_skills": ["Python", "FastAPI"], "user_experience": 2}'
```

### 3.2. Test Frontend
1. Open your Vercel URL in browser: `https://your-app-name.vercel.app`
2. Upload a resume PDF
3. Check if recommendations load
4. Click "Apply Now" buttons to verify job links work

### 3.3. Check Browser Console
- Open Developer Tools (F12)
- Check Console for any errors
- Check Network tab to see API requests

---

## Part 4: Common Issues & Troubleshooting

### Backend Issues

**❌ Build fails with "No module named 'X'"**
- Add missing package to `backend/requirements.txt`
- Commit and push changes
- Render will auto-redeploy

**❌ "GEMINI_API_KEY not set" error**
- Go to Render → Environment → Add `GEMINI_API_KEY`
- Save and redeploy

**❌ Backend is slow/times out**
- Free tier spins down after inactivity (15 mins)
- First request after idle takes ~30-60 seconds
- Upgrade to Starter plan for always-on service

**❌ CORS errors in browser**
- Verify `FRONTEND_URL` is set correctly in Render
- Check backend logs for CORS-related messages
- Redeploy backend after changing env vars

### Frontend Issues

**❌ "Failed to fetch" or "Network error"**
- Verify `VITE_API_BASE` is set correctly in Vercel
- Check if backend URL is accessible
- Open backend URL directly in browser to test

**❌ Environment variables not working**
- Vercel requires `VITE_` prefix for public variables
- Redeploy after adding/changing env vars
- Check build logs in Vercel dashboard

**❌ 404 on page refresh**
- Vercel should auto-configure SPA routing
- Verify `vercel.json` exists in frontend folder

**❌ Jobs not loading**
- Check browser console for errors
- Verify backend `/recommend_jobs` endpoint works
- Check Network tab for failed requests

---

## Part 5: Continuous Deployment

### Automatic Deployments

Both Render and Vercel support automatic deployments:

**Render (Backend)**:
- Pushes to `main` branch automatically trigger deployment
- Monitor in Render Dashboard → Events

**Vercel (Frontend)**:
- Pushes to `main` branch automatically deploy to production
- Pull requests create preview deployments
- Monitor in Vercel Dashboard → Deployments

### Manual Deployments

**Render**: 
- Dashboard → Manual Deploy → "Deploy latest commit"

**Vercel**: 
- Dashboard → Deployments → "Redeploy"

---

## Part 6: Custom Domains (Optional)

### Backend (Render)
1. Settings → Custom Domains
2. Add your domain (e.g., `api.yourdomain.com`)
3. Update DNS records as instructed
4. Update `VITE_API_BASE` in Vercel

### Frontend (Vercel)
1. Settings → Domains
2. Add your domain (e.g., `yourdomain.com`)
3. Update DNS records as instructed
4. Update `FRONTEND_URL` in Render

---

## Part 7: Monitoring & Logs

### Render Logs
- Dashboard → Logs tab
- Real-time logs of backend activity
- Filter by severity (Info, Warning, Error)

### Vercel Logs
- Dashboard → Deployments → Select deployment → "View Function Logs"
- Build logs available for each deployment

### Usage Monitoring
- Render: Dashboard shows CPU, memory, bandwidth usage
- Vercel: Analytics tab shows page views, performance

---

## Summary Checklist

### Backend (Render)
- [ ] Repository pushed to GitHub
- [ ] Created Render web service
- [ ] Set `GEMINI_API_KEY` environment variable
- [ ] Set `PYTHON_VERSION` to 3.11.0
- [ ] Deployment successful
- [ ] Backend URL noted and tested

### Frontend (Vercel)
- [ ] Created Vercel project
- [ ] Set `VITE_API_BASE` to backend URL
- [ ] Deployment successful
- [ ] Frontend URL noted

### Final Configuration
- [ ] Updated `FRONTEND_URL` in Render with Vercel URL
- [ ] Redeployed backend
- [ ] Tested full application flow
- [ ] Verified CORS working
- [ ] Upload resume works
- [ ] Job recommendations load
- [ ] Apply Now buttons work

---

## URLs to Save

After deployment, save these URLs:

```
Backend API: https://_____________________.onrender.com
Frontend App: https://_____________________.vercel.app
```

---

## Cost Estimate

### Free Tier (Testing)
- **Render Free**: Backend (spins down after 15 min inactivity)
- **Vercel Free**: Frontend (unlimited deployments)
- **Total**: $0/month

### Production (Recommended)
- **Render Starter**: $7/month (always-on, 512MB RAM)
- **Vercel Free**: $0/month (sufficient for most projects)
- **Total**: $7/month

### Scaling Up
- **Render Standard**: $25/month (2GB RAM)
- **Vercel Pro**: $20/month (more bandwidth, analytics)

---

## Next Steps After Deployment

1. **Monitor Performance**: Check response times and errors
2. **Set Up Alerts**: Configure email notifications for downtime
3. **Add Analytics**: Integrate Google Analytics or Mixpanel
4. **Improve SEO**: Add meta tags, sitemap
5. **Add Authentication**: If you want user accounts
6. **Database**: Consider adding PostgreSQL for storing recommendations
7. **CI/CD**: Set up automated testing before deployment

---

Need help? Check:
- Render Docs: https://render.com/docs
- Vercel Docs: https://vercel.com/docs
- Backend logs in Render dashboard
- Frontend logs in Vercel dashboard

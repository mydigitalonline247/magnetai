# MagnetAI Deployment Guide - Vercel

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Account**: Your code should be in a GitHub repository
3. **Google OAuth Setup**: Already configured
4. **Supabase Project**: Already configured

## Step 1: Prepare Your Repository

Make sure your repository contains:
- ✅ `main.py` - Your FastAPI application
- ✅ `api/index.py` - Vercel serverless function entry point
- ✅ `vercel.json` - Vercel configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `.gitignore` - Excludes sensitive files

## Step 2: Deploy to Vercel

### Option A: Deploy via Vercel Dashboard

1. **Connect Repository**:
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository
   - Select the repository containing your MagnetAI code

2. **Configure Project**:
   - Framework Preset: `Other`
   - Root Directory: `./` (leave as default)
   - Build Command: Leave empty (Vercel will auto-detect)
   - Output Directory: Leave empty

3. **Add Environment Variables**:
   - Click "Environment Variables" in the project settings
   - Add the following variables:

```
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
SUPABASE_URL=https://stihymxjkdblsoxnbiph.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
SUPABASE_ANON_KEY=your_supabase_anon_key
```

4. **Deploy**:
   - Click "Deploy"
   - Wait for the build to complete

### Option B: Deploy via Vercel CLI

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy**:
   ```bash
   vercel
   ```

4. **Add Environment Variables**:
   ```bash
   vercel env add GOOGLE_CLIENT_ID
   vercel env add GOOGLE_CLIENT_SECRET
   vercel env add SUPABASE_URL
   vercel env add SUPABASE_SERVICE_ROLE_KEY
   vercel env add SUPABASE_ANON_KEY
   ```

## Step 3: Update Google OAuth Redirect URI

After deployment, you'll get a URL like: `https://your-app.vercel.app`

1. **Go to Google Cloud Console**:
   - Visit [console.cloud.google.com](https://console.cloud.google.com)
   - Select your project
   - Go to "APIs & Services" > "Credentials"

2. **Update OAuth 2.0 Client**:
   - Click on your OAuth 2.0 client
   - Add the new redirect URI: `https://your-app.vercel.app/auth/google/callback`
   - Save the changes

## Step 4: Test Your Deployment

1. **Test Basic Endpoints**:
   - Visit `https://your-app.vercel.app/` - Should show "Hello, World!"
   - Visit `https://your-app.vercel.app/docs` - FastAPI documentation

2. **Test Database Connection**:
   - Visit `https://your-app.vercel.app/test-supabase` - Should show Supabase connection status

3. **Test OAuth Flow**:
   - Visit `https://your-app.vercel.app/auth/google` - Should redirect to Google OAuth

## Step 5: Custom Domain (Optional)

1. **Add Custom Domain**:
   - In Vercel dashboard, go to your project
   - Click "Settings" > "Domains"
   - Add your custom domain

2. **Update Google OAuth**:
   - Add the custom domain redirect URI to Google OAuth settings

## Troubleshooting

### Common Issues:

1. **Environment Variables Not Set**:
   - Check Vercel dashboard > Settings > Environment Variables
   - Ensure all variables are added correctly

2. **OAuth Redirect URI Mismatch**:
   - Verify the redirect URI in Google Cloud Console matches your Vercel URL
   - Include the full path: `https://your-app.vercel.app/auth/google/callback`

3. **Supabase Connection Issues**:
   - Check if Supabase project is active
   - Verify service role key is correct
   - Ensure RLS policies are properly configured

4. **Build Failures**:
   - Check Vercel build logs for Python dependency issues
   - Ensure `requirements.txt` is up to date

### Debug Endpoints:

- `/debug/env` - Check environment variables
- `/test-supabase` - Test database connection
- `/docs` - API documentation

## Production Considerations

1. **Security**:
   - Use environment variables for all secrets
   - Enable HTTPS (automatic with Vercel)
   - Use Supabase RLS policies

2. **Performance**:
   - Vercel serverless functions have cold starts
   - Consider using Supabase for all data (no local SQLite in production)

3. **Monitoring**:
   - Use Vercel analytics
   - Monitor Supabase usage
   - Set up error tracking

## Next Steps

After successful deployment:
1. Test all OAuth flows
2. Monitor application performance
3. Set up custom domain if needed
4. Configure monitoring and alerts 
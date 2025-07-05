# Google OAuth Setup for MagnetAI

## Prerequisites
- Google Cloud Console account
- FastAPI application running

## Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google+ API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - For local development: `http://localhost:8000/auth/google/callback`
     - For production: `https://your-domain.vercel.app/auth/google/callback`
5. Copy your Client ID and Client Secret

## Step 2: Set Environment Variables

### For Local Development
Create a `.env` file in your project root:
```
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

### For Vercel Deployment
1. Go to your Vercel project dashboard
2. Navigate to "Settings" > "Environment Variables"
3. Add the following variables:
   - `GOOGLE_CLIENT_ID`: your-google-client-id
   - `GOOGLE_CLIENT_SECRET`: your-google-client-secret
   - `GOOGLE_REDIRECT_URI`: https://your-domain.vercel.app/auth/google/callback

## Step 3: Test the Integration

1. Start your FastAPI server: `uvicorn main:app --reload`
2. Visit `http://localhost:8000/login`
3. Click "Sign in with Google"
4. Complete the OAuth flow
5. You should receive an access token

## API Endpoints

- `GET /login` - Login page
- `GET /auth/google` - Initiate Google OAuth
- `GET /auth/google/callback` - OAuth callback handler
- `GET /auth/me` - Get current user info (requires Bearer token)
- `GET /protected` - Example protected route
- `GET /auth/logout` - Logout endpoint

## Testing with Postman

1. First, get an access token by visiting `/login` in your browser
2. Copy the token from the success page
3. In Postman, add the Authorization header:
   - Type: Bearer Token
   - Token: your-access-token
4. Test protected endpoints like `/auth/me` and `/protected`

## Security Notes

- This implementation uses simple tokens for demonstration
- In production, use JWT tokens with proper expiration
- Store user data in a database instead of in-memory storage
- Add proper error handling and validation
- Implement refresh tokens for better security 
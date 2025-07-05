# main.py
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from pydantic import BaseModel
import httpx
import os
from typing import Optional
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

# Supabase Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_DATABASE_URL = os.environ.get("SUPABASE_DATABASE_URL", "")

# Validate required environment variables
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env file")

# Initialize Supabase client
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="MagnetAI APP", description="Your automated lifestyle to a stress-free transaction")

# Security
security = HTTPBearer()

# Pydantic models
class UserInfo(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None
    sub: str  # Google user ID

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_info: UserInfo

# In-memory storage (replace with database in production)
users_db = {}

@app.get("/")
def read_root():
    return {"message": "Hello, World!", "status": "running"}

@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables"""
    return {
        "client_id_set": bool(os.environ.get("GOOGLE_CLIENT_ID")),
        "client_secret_set": bool(os.environ.get("GOOGLE_CLIENT_SECRET")),
        "supabase_url_set": bool(os.environ.get("SUPABASE_DATABASE_URL")),
        "redirect_uri": os.environ.get("GOOGLE_REDIRECT_URI", "not set"),
        "client_id_length": len(os.environ.get("GOOGLE_CLIENT_ID", "")),
        "client_secret_length": len(os.environ.get("GOOGLE_CLIENT_SECRET", ""))
    }

@app.get("/login")
async def login_page():
    """Serve the login page for local testing"""
    if os.path.exists("login.html"):
        return FileResponse("login.html")
    else:
        # Fallback for production (no HTML file)
        return HTMLResponse(content="""
        <html>
            <body>
                <h1>MagnetAI OAuth</h1>
                <p>This is a backend-only API. For OAuth testing, use:</p>
                <ul>
                    <li><a href="/auth/google">Direct OAuth Link</a></li>
                    <li><a href="/docs">API Documentation</a></li>
                </ul>
                <p>Or make a GET request to <code>/auth/google</code></p>
            </body>
        </html>
        """)

@app.get("/auth/init")
async def init_oauth():
    """Initialize OAuth flow - redirects to Google"""
    return RedirectResponse(url="/auth/google")

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "query": q}

# Google OAuth endpoints
@app.get("/auth/google")
async def google_login():
    """Redirect to Google OAuth"""
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid email profile&"
        f"access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)

@app.get("/auth/google/callback")
async def google_callback(code: str):
    """Handle Google OAuth callback"""
    try:
        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": GOOGLE_REDIRECT_URI,
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()
            
            # Get user info
            user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            user_response = await client.get(user_info_url, headers=headers)
            user_response.raise_for_status()
            user_info = user_response.json()
            
            # Store user info in Supabase database
            user_data = {
                "google_id": user_info["id"],
                "email": user_info["email"],
                "name": user_info["name"],
                "picture": user_info.get("picture", ""),
                "last_login": "now()"
            }
            
            try:
                if supabase:
                    # Check if user exists
                    existing_user = supabase.table("users").select("*").eq("google_id", user_info["id"]).execute()
                    
                    if existing_user.data:
                        # Update existing user
                        supabase.table("users").update(user_data).eq("google_id", user_info["id"]).execute()
                    else:
                        # Insert new user
                        supabase.table("users").insert(user_data).execute()
                else:
                    # Fallback to in-memory storage
                    users_db[user_info["id"]] = user_info
            except Exception as db_error:
                print(f"Database error: {db_error}")
                # Fallback to in-memory storage
                users_db[user_info["id"]] = user_info
            
            # Create a simple token (in production, use JWT)
            access_token = f"user_{user_info['id']}"
            
            # Return success page with token
            return HTMLResponse(content=f"""
            <html>
                <body>
                    <h1>Login Successful!</h1>
                    <p>Welcome, {user_info['name']}!</p>
                    <p>Your access token: {access_token}</p>
                    <p>Use this token in the Authorization header: Bearer {access_token}</p>
                    <script>
                        // Store token in localStorage
                        localStorage.setItem('access_token', '{access_token}');
                        localStorage.setItem('user_info', '{json.dumps(user_info)}');
                    </script>
                </body>
            </html>
            """)
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@app.get("/auth/me", response_model=UserInfo)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user information"""
    token = credentials.credentials
    
    # Simple token validation (in production, use JWT)
    if not token.startswith("user_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = token.replace("user_", "")
    
    # Try to get user from Supabase first
    user_info = None
    if supabase:
        try:
            result = supabase.table("users").select("*").eq("google_id", user_id).execute()
            if result.data:
                user_info = result.data[0]
        except Exception as db_error:
            print(f"Database error: {db_error}")
    
    # Fallback to in-memory storage
    if not user_info:
        user_info = users_db.get(user_id)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return UserInfo(
        email=user_info["email"],
        name=user_info["name"],
        picture=user_info.get("picture"),
        sub=user_info["google_id"] if "google_id" in user_info else user_info["id"]
    )

@app.get("/auth/logout")
async def logout():
    """Logout endpoint"""
    return {"message": "Logged out successfully"}

# Protected endpoint example
@app.get("/protected")
async def protected_route(current_user: UserInfo = Depends(get_current_user)):
    """Example of a protected route"""
    return {
        "message": f"Hello {current_user.name}! This is a protected route.",
        "user_email": current_user.email
    }

# For Vercel deployment
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
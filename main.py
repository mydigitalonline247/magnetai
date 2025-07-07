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
from supabase import create_client
from supabase.client import Client
import sqlite3
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

# Dynamic redirect URI for production
def get_redirect_uri():
    """Get the appropriate redirect URI based on environment"""
    if os.environ.get("VERCEL_URL"):
        # Production on Vercel
        return f"https://{os.environ.get('VERCEL_URL')}/auth/google/callback"
    elif os.environ.get("PRODUCTION_URL"):
        # Use specific production URL if set
        return f"{os.environ.get('PRODUCTION_URL')}/auth/google/callback"
    elif os.environ.get("NODE_ENV") == "production" or os.environ.get("VERCEL_ENV") == "production":
        # Fallback for production environment
        return "https://magnetai.vercel.app/auth/google/callback"
    else:
        # Local development
        return os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

GOOGLE_REDIRECT_URI = get_redirect_uri()

# Supabase Configuration.
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
# Use service role key for local development to bypass RLS, fallback to anon key
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_DATABASE_URL = os.environ.get("SUPABASE_DATABASE_URL", "")

# Local SQLite database for testing (only in development)
LOCAL_DB_PATH = "local_users.db" if not os.environ.get("VERCEL_URL") else None

def init_local_db():
    """Initialize local SQLite database"""
    if not LOCAL_DB_PATH:
        return  # Skip in production
    
    conn = sqlite3.connect(LOCAL_DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_id TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            picture TEXT,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_local_db_connection():
    """Get SQLite database connection"""
    if not LOCAL_DB_PATH:
        return None  # No local DB in production
    return sqlite3.connect(LOCAL_DB_PATH)

# Initialize local database (only in development)
if LOCAL_DB_PATH:
    init_local_db()

# Validate required environment variables
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env file")

# Initialize Supabase client (will be created when needed)
supabase: Optional[Client] = None

def get_supabase_client():
    """Get or create Supabase client"""
    global supabase
    if supabase is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            logger.info(f"Creating Supabase client with URL: {SUPABASE_URL}")
            logger.info(f"Using key type: {'Service Role' if SUPABASE_KEY == os.environ.get('SUPABASE_SERVICE_ROLE_KEY') else 'Anon'}")
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Supabase client created successfully")
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {e}")
            return None
    return supabase

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
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    anon_key = os.environ.get("SUPABASE_ANON_KEY")
    return {
        "client_id_set": bool(os.environ.get("GOOGLE_CLIENT_ID")),
        "client_secret_set": bool(os.environ.get("GOOGLE_CLIENT_SECRET")),
        "supabase_url_set": bool(os.environ.get("SUPABASE_DATABASE_URL")),
        "supabase_url": os.environ.get("SUPABASE_URL", "not set"),
        "supabase_anon_key": anon_key[:10] + "..." if anon_key else "not set",
        "supabase_service_role_key": service_role_key[:10] + "..." if service_role_key else "not set",
        "supabase_key_being_used": SUPABASE_KEY[:10] + "..." if SUPABASE_KEY else "not set",
        "redirect_uri": os.environ.get("GOOGLE_REDIRECT_URI", "not set"),
        "client_id_length": len(os.environ.get("GOOGLE_CLIENT_ID", "")),
        "client_secret_length": len(os.environ.get("GOOGLE_CLIENT_SECRET", "")),
        "supabase_client_initialized": get_supabase_client() is not None
    }

@app.get("/debug/supabase")
async def debug_supabase():
    """Debug endpoint to test database connection"""
    result = {
        "supabase": {"available": False, "user_count": 0, "error": None},
        "local_db": {"available": False, "user_count": 0, "error": None},
        "database_type": "Unknown"
    }
    
    # Test Supabase connection
    try:
        supabase_client = get_supabase_client()
        if supabase_client:
            # Try to query the users table
            supabase_result = supabase_client.table("users").select("*").execute()
            result["supabase"] = {
                "available": True,
                "user_count": supabase_result.count,
                "error": None
            }
            result["database_type"] = "Supabase"
        else:
            result["supabase"]["error"] = "Supabase client not initialized"
    except Exception as e:
        result["supabase"]["error"] = str(e)
    
    # Test local SQLite database
    try:
        conn = get_local_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Count users in local database
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            conn.close()
            
            result["local_db"] = {
                "available": True,
                "user_count": user_count,
                "error": None
            }
            
            # If Supabase is not available, use local as primary
            if not result["supabase"]["available"]:
                result["database_type"] = "SQLite"
        else:
            result["local_db"] = {
                "available": False,
                "user_count": 0,
                "error": "Local database not available in production"
            }
            
    except Exception as e:
        result["local_db"]["error"] = str(e)
    
    return result

@app.get("/test-supabase")
async def test_supabase():
    """Alias for debug/supabase endpoint"""
    return await debug_supabase()

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
def read_item(item_id: int, q: Optional[str] = None):
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
                # Try Supabase first (for production)
                supabase_client = get_supabase_client()
                if supabase_client:
                    logger.info("Attempting to store user in Supabase...")
                    # Check if user exists
                    existing_user = supabase_client.table("users").select("*").eq("google_id", user_info["id"]).execute()
                    
                    if existing_user.data:
                        # Update existing user
                        supabase_client.table("users").update(user_data).eq("google_id", user_info["id"]).execute()
                        logger.info(f"User updated in Supabase: {user_info['email']}")
                    else:
                        # Insert new user
                        supabase_client.table("users").insert(user_data).execute()
                        logger.info(f"User stored in Supabase: {user_info['email']}")
                else:
                    raise Exception("Supabase client not available")
                    
            except Exception as supabase_error:
                logger.error(f"Supabase error: {supabase_error}")
                logger.info("Falling back to local SQLite database...")
                
                # Fallback to local SQLite database
                try:
                    conn = get_local_db_connection()
                    if conn is not None:
                        cursor = conn.cursor()
                        
                        # Check if user exists
                        cursor.execute("SELECT * FROM users WHERE google_id = ?", (user_info["id"],))
                        existing_user = cursor.fetchone()
                        
                        if existing_user:
                            # Update existing user
                            cursor.execute("""
                                UPDATE users 
                                SET email = ?, name = ?, picture = ?, last_login = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                                WHERE google_id = ?
                            """, (user_info["email"], user_info["name"], user_info.get("picture", ""), user_info["id"]))
                        else:
                            # Insert new user
                            cursor.execute("""
                                INSERT INTO users (google_id, email, name, picture, last_login, created_at, updated_at)
                                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            """, (user_info["id"], user_info["email"], user_info["name"], user_info.get("picture", "")))
                        
                        conn.commit()
                        conn.close()
                        logger.info(f"User stored in local database: {user_info['email']}")
                    else:
                        raise Exception("Local database not available")
                    
                except Exception as local_db_error:
                    logger.error(f"Local database error: {local_db_error}")
                    # Final fallback to in-memory storage
                    users_db[user_info["id"]] = user_info
                    logger.info(f"User stored in memory: {user_info['email']}")
            
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
    
    # Try to get user from local database first
    user_info = None
    try:
        conn = get_local_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE google_id = ?", (user_id,))
            result = cursor.fetchone()
            
            if result:
                # Convert SQLite row to dict
                columns = [description[0] for description in cursor.description]
                user_info = dict(zip(columns, result))
            
            conn.close()
    except Exception as db_error:
        logger.error(f"Local database error: {db_error}")
    
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
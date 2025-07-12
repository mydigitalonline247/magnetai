import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime, timedelta
from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials as firebase_credentials
import os
from app.utils import base_response
import base64
import json

# Initialize Firebase Admin SDK if not already initialized
if not firebase_admin._apps:
    try:
        cred_path = os.environ.get("FIREBASE_CREDENTIALS")
        cred_b64 = os.environ.get("FIREBASE_CREDENTIALS_BASE64")
        if cred_b64:
            cred_json = base64.b64decode(cred_b64).decode("utf-8")
            cred_dict = json.loads(cred_json)
            cred = firebase_credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        elif cred_path:
            cred = firebase_credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # Initialize without credentials (for development/testing)
            print("Warning: No Firebase credentials found. Firebase features may not work.")
            firebase_admin.initialize_app()
    except Exception as e:
        print(f"Warning: Failed to initialize Firebase: {e}")
        # Continue without Firebase initialization

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return base_response(
                success=False,
                message="Invalid authentication credentials",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        return base_response(success=True, message="Token is valid", data=payload)
    except ExpiredSignatureError:
        return base_response(
            success=False,
            message="Token has expired",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    except InvalidTokenError:
        return base_response(
            success=False,
            message="Invalid authentication credentials",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


async def verify_google_token(id_token_str: str):
    try:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        # Check if Firebase is properly initialized
        if not firebase_admin._apps:
            return base_response(
                success=False,
                message="Firebase not properly initialized. Check environment variables.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        print(f"Starting Firebase token verification for token: {id_token_str[:50]}...")
        
        # Add more detailed logging
        print(f"Firebase apps available: {list(firebase_admin._apps.keys())}")
        
        # Basic token format validation
        if not id_token_str or len(id_token_str) < 100:
            return base_response(
                success=False,
                message="Invalid token format - token too short",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if token has the expected format (3 parts separated by dots)
        token_parts = id_token_str.split('.')
        if len(token_parts) != 3:
            return base_response(
                success=False,
                message="Invalid token format - not a valid JWT",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        print(f"Token format validation passed, proceeding with Firebase verification...")
        
        # Use ThreadPoolExecutor to run Firebase verification in a separate thread
        # with a timeout to prevent hanging
        loop = asyncio.get_event_loop()
        print(f"Starting async Firebase verification...")
        
        with ThreadPoolExecutor() as executor:
            print(f"Created ThreadPoolExecutor, starting verification...")
            decoded_token = await asyncio.wait_for(
                loop.run_in_executor(executor, firebase_auth.verify_id_token, id_token_str),
                timeout=15.0  # 15 second timeout
            )
            print(f"Firebase token verification successful")
            return base_response(success=True, message="Firebase ID token is valid", data=decoded_token)
            
    except asyncio.TimeoutError:
        print(f"Firebase token verification timed out after 15 seconds")
        return base_response(
            success=False,
            message="Firebase token verification timed out",
            status_code=status.HTTP_408_REQUEST_TIMEOUT
        )
    except Exception as e:
        print(f"Firebase token verification error: {str(e)}")
        return base_response(
            success=False,
            message=f"Invalid Firebase ID token: {str(e)}",
            status_code=status.HTTP_401_UNAUTHORIZED
        ) 
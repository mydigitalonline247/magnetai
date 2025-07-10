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

# Initialize Firebase Admin SDK if not already initialized
if not firebase_admin._apps:
    cred_path = os.environ.get("FIREBASE_CREDENTIALS")
    if cred_path:
        cred = firebase_credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: timedelta = None):
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


def verify_google_token(id_token_str: str):
    try:
        decoded_token = firebase_auth.verify_id_token(id_token_str)
        return base_response(success=True, message="Firebase ID token is valid", data=decoded_token)
    except Exception as e:
        return base_response(
            success=False,
            message=f"Invalid Firebase ID token: {str(e)}",
            status_code=status.HTTP_401_UNAUTHORIZED
        ) 
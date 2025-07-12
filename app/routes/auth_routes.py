from fastapi import APIRouter, status, Depends
from app.models import FirebaseTokenRequest, LoginResponse, UserResponse
from app.auth import create_access_token, verify_token, verify_google_token
from datetime import timedelta
from app.config import JWT_EXPIRATION_HOURS
from app.utils import base_response

router = APIRouter()

@router.post("/auth/firebase")
async def firebase_auth(token_request: FirebaseTokenRequest):
    """
    Authenticate a user using a Firebase ID token (from any provider: Google, Email, etc.).
    Expects a Firebase ID token from the frontend (obtained via Firebase Auth).
    """
    print(f"Received token request: {token_request}")
    idinfo_response = await verify_google_token(token_request.id_token)
    if not idinfo_response.status_code == 200:
        return idinfo_response
    
    # Get the response data from the JSONResponse
    response_data = idinfo_response.body
    if isinstance(response_data, bytes):
        response_data = response_data.decode('utf-8')
    if isinstance(response_data, str):
        import json
        response_data = json.loads(response_data)
    
    # Extract the actual data from the BaseResponse structure
    idinfo = response_data.get("data", {})
    
    user_data = {
        "id": idinfo.get("uid", ""),
        "email": idinfo.get("email", ""),
        "name": idinfo.get("name", ""),
        "picture": idinfo.get("picture", ""),
        "verified_email": idinfo.get("email_verified", False)
    }
    access_token_expires = timedelta(hours=JWT_EXPIRATION_HOURS)
    access_token = create_access_token(
        data={"sub": user_data["id"], "email": user_data["email"]},
        expires_delta=access_token_expires
    )
    login_response = LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user_data)
    )
    return base_response(
        success=True,
        message="Login was successful",
        data=login_response.dict(),
        status_code=status.HTTP_200_OK
    )

@router.get("/auth/me")
async def get_current_user(token_response = Depends(verify_token)):
    if not token_response.status_code == 200:
        return token_response
    
    # Get the response data from the JSONResponse
    response_data = token_response.body
    if isinstance(response_data, bytes):
        response_data = response_data.decode('utf-8')
    if isinstance(response_data, str):
        import json
        response_data = json.loads(response_data)
    
    # Extract the actual data from the BaseResponse structure
    token_data = response_data.get("data", {})
    
    user_response = UserResponse(
        id=token_data.get("sub", ""),
        email=token_data.get("email", ""),
        name="", # You'd get this from your database
        picture="", # You'd get this from your database
        verified_email=True
    )
    return base_response(
        success=True,
        message="User profile retrieved successfully",
        data=user_response.dict(),
        status_code=status.HTTP_200_OK
    ) 
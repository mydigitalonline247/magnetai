from fastapi import APIRouter, HTTPException, status, Depends
from app.models import GoogleTokenRequest, LoginResponse, UserResponse, BaseResponse
from app.auth import create_access_token, verify_token, verify_google_token
from datetime import timedelta
from app.config import JWT_EXPIRATION_HOURS

router = APIRouter()

@router.post("/auth/firebase")
async def firebase_auth(token_request: GoogleTokenRequest):
    """
    Authenticate a user using a Firebase ID token (from any provider: Google, Email, etc.).
    Expects a Firebase ID token from the frontend (obtained via Firebase Auth).
    """
    try:
        idinfo = verify_google_token(token_request.id_token)
        user_data = {
            "id": idinfo["uid"],
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
        return BaseResponse(
            success=True,
            message="Login was successful",
            data=login_response.dict()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase ID token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

@router.get("/auth/me")
async def get_current_user(token_data: dict = Depends(verify_token)):
    user_response = UserResponse(
        id=token_data["sub"],
        email=token_data["email"],
        name="", # You'd get this from your database
        picture="", # You'd get this from your database
        verified_email=True
    )
    return BaseResponse(
        success=True,
        message="User profile retrieved successfully",
        data=user_response.dict()
    ) 
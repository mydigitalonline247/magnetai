from fastapi import APIRouter, HTTPException, status, Depends
from app.models import GoogleTokenRequest, LoginResponse, UserResponse
from app.auth import create_access_token, verify_token, verify_google_token
from datetime import timedelta
from app.config import JWT_EXPIRATION_HOURS

router = APIRouter()

@router.post("/auth/google", response_model=LoginResponse)
async def google_auth(token_request: GoogleTokenRequest):
    try:
        idinfo = verify_google_token(token_request.id_token)
        user_data = {
            "id": idinfo["sub"],
            "email": idinfo["email"],
            "name": idinfo["name"],
            "picture": idinfo["picture"],
            "verified_email": idinfo.get("email_verified", False)
        }
        access_token_expires = timedelta(hours=JWT_EXPIRATION_HOURS)
        access_token = create_access_token(
            data={"sub": user_data["id"], "email": user_data["email"]},
            expires_delta=access_token_expires
        )
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(**user_data)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

@router.get("/auth/me", response_model=UserResponse)
async def get_current_user(token_data: dict = Depends(verify_token)):
    return UserResponse(
        id=token_data["sub"],
        email=token_data["email"],
        name="", # You'd get this from your database
        picture="", # You'd get this from your database
        verified_email=True
    ) 
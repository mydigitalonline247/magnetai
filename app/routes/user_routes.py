from fastapi import APIRouter, Depends
from app.auth import verify_token
from app.models import BaseResponse

router = APIRouter()

@router.get("/protected", response_model=BaseResponse)
async def protected_route(token_data: dict = Depends(verify_token)):
    return BaseResponse(
        success=True,
        message="Protected route accessed successfully",
        data={"message": f"Hello {token_data['email']}, this is a protected route!"}
    )

@router.get("/", response_model=BaseResponse)
async def root():
    return BaseResponse(
        success=True,
        message="API is running successfully",
        data={"message": "Google OAuth API is running"}
    ) 
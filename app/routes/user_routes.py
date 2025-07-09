from fastapi import APIRouter, Depends
from app.auth import verify_token

router = APIRouter()

@router.get("/protected")
async def protected_route(token_data: dict = Depends(verify_token)):
    return {"message": f"Hello {token_data['email']}, this is a protected route!"}

@router.get("/")
async def root():
    return {"message": "Google OAuth API is running"} 
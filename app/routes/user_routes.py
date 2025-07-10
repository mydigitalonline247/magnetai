from fastapi import APIRouter, Depends, status
from app.auth import verify_token
from app.utils import base_response

router = APIRouter()

@router.get("/protected")
async def protected_route(token_response = Depends(verify_token)):
    if not token_response.status_code == 200:
        return token_response
    token_data = token_response.body if hasattr(token_response, 'body') else token_response.json()
    return base_response(
        success=True,
        message="Protected route accessed successfully",
        data={"message": f"Hello {token_data['email']}, this is a protected route!"},
        status_code=status.HTTP_200_OK
    )

@router.get("/")
async def root():
    return base_response(
        success=True,
        message="MagnetAI is running successfully",
        data={"message": "MagnetAI is running"},
        status_code=status.HTTP_200_OK
    ) 
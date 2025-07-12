from fastapi import APIRouter, Depends, status
from app.auth import verify_token
from app.utils import base_response

router = APIRouter()

@router.get("/protected")
async def protected_route(token_response = Depends(verify_token)):
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
    
    return base_response(
        success=True,
        message="Protected route accessed successfully",
        data={"message": f"Hello {token_data.get('email', 'user')}, this is a protected route!"},
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
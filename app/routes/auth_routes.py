from fastapi import APIRouter, status, Depends, Request
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
    print(f"Starting Firebase verification...")
    
    try:
        idinfo_response = await verify_google_token(token_request.id_token)
        print(f"Firebase verification completed with status: {idinfo_response.status_code}")
        
        if not idinfo_response.status_code == 200:
            print(f"Firebase verification failed: {idinfo_response.body}")
            return idinfo_response
    except Exception as e:
        print(f"Error during Firebase verification: {e}")
        return base_response(
            success=False,
            message=f"Error during Firebase verification: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.post("/auth/firebase-raw")
async def firebase_auth_raw(request: Request):
    """
    Raw version of Firebase auth that manually handles request body
    """
    print("firebase_auth_raw endpoint reached")
    
    try:
        # Manually read and parse the request body
        body = await request.body()
        print(f"Request body read, length: {len(body)}")
        
        body_str = body.decode('utf-8')
        print(f"Request body decoded: {body_str[:100]}...")
        
        import json
        data = json.loads(body_str)
        print(f"JSON parsed: {data}")
        
        id_token = data.get("id_token")
        if not id_token:
            return base_response(
                success=False,
                message="Missing id_token in request body",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        print(f"Starting Firebase verification for token: {id_token[:50]}...")
        idinfo_response = await verify_google_token(id_token)
        
        if not idinfo_response.status_code == 200:
            return idinfo_response
            
        # Continue with the rest of the logic...
        response_data = idinfo_response.body
        if isinstance(response_data, bytes):
            response_data = response_data.decode('utf-8')
        if isinstance(response_data, str):
            response_data = json.loads(response_data)
        
        idinfo = response_data.get("data", {})
        
        user_data = {
            "id": idinfo.get("uid", ""),
            "email": idinfo.get("email", ""),
            "name": idinfo.get("name", ""),
            "picture": idinfo.get("picture", ""),
            "verified_email": idinfo.get("email_verified", False)
        }
        
        from datetime import timedelta
        from app.config import JWT_EXPIRATION_HOURS
        from app.auth import create_access_token
        
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
        
    except Exception as e:
        print(f"Error in firebase_auth_raw: {e}")
        import traceback
        traceback.print_exc()
        return base_response(
            success=False,
            message=f"Error processing request: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
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

@router.post("/auth/test")
async def test_auth_endpoint():
    """
    Test endpoint that doesn't require Firebase - just to verify the API is working
    """
    print("test endpoint reached")
    return base_response(
        success=True,
        message="Auth endpoint is working (no Firebase required)",
        data={"test": "This endpoint works without Firebase"},
        status_code=status.HTTP_200_OK
    )

@router.post("/auth/test-token")
async def test_token_format(token_request: FirebaseTokenRequest):
    """
    Test endpoint to validate token format without Firebase verification
    """
    print(f"test-token endpoint reached with token: {token_request.id_token[:50]}...")
    token = token_request.id_token
    
    # Basic validation
    if not token or len(token) < 100:
        return base_response(
            success=False,
            message="Token too short",
            data={"token_length": len(token) if token else 0},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Check JWT format
    token_parts = token.split('.')
    if len(token_parts) != 3:
        return base_response(
            success=False,
            message="Invalid JWT format",
            data={"parts_count": len(token_parts)},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Try to decode the header (first part) to see if it's valid
    try:
        import base64
        import json
        
        # Decode the header
        header_part = token_parts[0]
        # Add padding if needed
        header_part += '=' * (4 - len(header_part) % 4)
        header_json = base64.urlsafe_b64decode(header_part)
        header = json.loads(header_json)
        
        return base_response(
            success=True,
            message="Token format is valid",
            data={
                "token_length": len(token),
                "header": header,
                "parts_count": len(token_parts)
            },
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return base_response(
            success=False,
            message="Token header could not be decoded",
            data={"error": str(e)},
            status_code=status.HTTP_400_BAD_REQUEST
        ) 
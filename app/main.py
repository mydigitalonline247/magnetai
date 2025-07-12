from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.routes import auth_routes, user_routes
from app.models import BaseResponse
from app.utils import base_response
from datetime import datetime
import json
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MagnetAI")

@app.on_event("startup")
async def startup_event():
    logger.info("MagnetAI API starting up...")
    
    # Check Firebase configuration
    try:
        import firebase_admin
        if firebase_admin._apps:
            logger.info("Firebase Admin SDK is initialized")
        else:
            logger.warning("Firebase Admin SDK is not initialized - will initialize on first use")
            
        # Check environment variables
        import os
        firebase_creds = os.environ.get("FIREBASE_CREDENTIALS_BASE64")
        if firebase_creds:
            logger.info("Firebase credentials found in environment")
        else:
            logger.warning("No Firebase credentials found - Firebase auth will not work")
            
    except Exception as e:
        logger.error(f"Error checking Firebase configuration: {e}")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        # Log request details
        logger.info(f"Request: {request.method} {request.url}")
        
        # Try to log body for POST requests (with timeout)
        if request.method == "POST":
            try:
                import asyncio
                body = await asyncio.wait_for(request.body(), timeout=5.0)
                logger.info(f"Request body length: {len(body)} bytes")
                logger.info(f"Request body (bytes): {body[:200]}...")  # Log first 200 chars
                if body:
                    try:
                        body_str = body.decode('utf-8')
                        logger.info(f"Request body (decoded): {body_str[:200]}...")
                        # Check if the JSON is complete
                        if body_str.strip().endswith('}'):
                            logger.info("Request body appears to be complete JSON")
                        else:
                            logger.warning("Request body appears to be incomplete JSON")
                    except UnicodeDecodeError:
                        logger.info("Request body could not be decoded as UTF-8")
            except asyncio.TimeoutError:
                logger.warning("Request body read timed out")
            except Exception as e:
                logger.error(f"Error reading request body: {e}")
        
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Middleware error: {e}")
        # Return a basic error response if middleware fails
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error in middleware"}
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=BaseResponse(
            success=False,
            message=exc.detail,
            data=None
        ).dict()
    )

@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=BaseResponse(
            success=False,
            message=exc.detail,
            data=None
        ).dict()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Convert errors to a serializable format
    serializable_errors = []
    for error in exc.errors():
        serializable_error = {
            "type": error["type"],
            "loc": error["loc"],
            "msg": error["msg"],
            "input": str(error.get("input", ""))  # Convert any bytes to string
        }
        serializable_errors.append(serializable_error)
    
    return JSONResponse(
        status_code=422,
        content=BaseResponse(
            success=False,
            message="Validation error",
            data={"errors": serializable_errors}
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    print("Unhandled exception:", exc)
    traceback.print_exc()  # This will print the full traceback to your console
    
    # Handle JSON serialization errors specifically
    if isinstance(exc, TypeError) and "not JSON serializable" in str(exc):
        return JSONResponse(
            status_code=500,
            content=BaseResponse(
                success=False,
                message="Internal server error: JSON serialization failed",
                data={"error": "Request body could not be processed"}
            ).dict()
        )
    
    return JSONResponse(
        status_code=500,
        content=BaseResponse(
            success=False,
            message="Internal server error",
            data=None
        ).dict()
    )

app.include_router(auth_routes.router)
app.include_router(user_routes.router)

# Add a simple health check endpoint
@app.get("/health")
async def health_check():
    return base_response(
        success=True,
        message="API is working",
        data={"message": "Hello from MagnetAI API!"},
        status_code=200
    )

@app.get("/test")
async def test_endpoint():
    return base_response(
        success=True,
        message="API is working",
        data={"message": "Hello from MagnetAI API!"},
        status_code=200
    )

@app.get("/ping")
async def ping_endpoint():
    return base_response(
        success=True,
        message="API is working",
        data={"message": "Hello from MagnetAI API!"},
        status_code=200
    )

@app.post("/simple-test")
async def simple_test(request: Request):
    """
    Simple test endpoint that doesn't use any models - just to test if POST requests work
    """
    try:
        body = await request.body()
        body_str = body.decode('utf-8') if body else ""
        return base_response(
            success=True,
            message="Simple test endpoint reached",
            data={"received_body": body_str[:100]},
            status_code=200
        )
    except Exception as e:
        return base_response(
            success=False,
            message=f"Error in simple test: {str(e)}",
            data={"error": str(e)},
            status_code=500
        )

@app.get("/firebase-status")
async def firebase_status():
    """Check Firebase initialization status"""
    try:
        import firebase_admin
        import os
        
        status = {
            "firebase_initialized": bool(firebase_admin._apps),
            "has_credentials": bool(os.environ.get("FIREBASE_CREDENTIALS_BASE64")),
            "app_count": len(firebase_admin._apps) if firebase_admin._apps else 0
        }
        
        return base_response(
            success=True,
            message="Firebase status retrieved",
            data=status,
            status_code=200
        )
    except Exception as e:
        return base_response(
            success=False,
            message=f"Error checking Firebase status: {str(e)}",
            data={"error": str(e)},
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 
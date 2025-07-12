from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.routes import auth_routes, user_routes
from app.models import BaseResponse
from datetime import datetime
import json
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MagnetAI")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log request details
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    # Try to log body for POST requests
    if request.method == "POST":
        try:
            body = await request.body()
            logger.info(f"Request body (bytes): {body}")
            if body:
                try:
                    body_str = body.decode('utf-8')
                    logger.info(f"Request body (decoded): {body_str}")
                except UnicodeDecodeError:
                    logger.info("Request body could not be decoded as UTF-8")
        except Exception as e:
            logger.error(f"Error reading request body: {e}")
    
    response = await call_next(request)
    return response

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 
from app.models import BaseResponse
from fastapi.responses import JSONResponse


def base_response(success: bool, message: str, data=None, status_code: int = 200):
    response = BaseResponse(success=success, message=message, data=data)
    return JSONResponse(status_code=status_code, content=response.dict()) 
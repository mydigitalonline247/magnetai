from pydantic import BaseModel
from typing import Optional

class GoogleTokenRequest(BaseModel):
    id_token: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: str
    verified_email: bool

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse 
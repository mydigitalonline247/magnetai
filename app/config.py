import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "your-google-client-id")
JWT_SECRET = os.environ.get("JWT_SECRET", "your-jwt-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 
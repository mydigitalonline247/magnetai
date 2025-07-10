import os
from dotenv import load_dotenv

load_dotenv()

# Removed GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
JWT_SECRET = os.environ.get("JWT_SECRET", "your-jwt-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 
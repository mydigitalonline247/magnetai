from fastapi import FastAPI
from app.routes import auth_routes, user_routes

app = FastAPI(title="Google OAuth API")

app.include_router(auth_routes.router)
app.include_router(user_routes.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 
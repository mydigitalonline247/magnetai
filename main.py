# main.py
from fastapi import FastAPI

app = FastAPI(title="MagnetAI API", description="A FastAPI application for MagnetAI")

@app.get("/")
def read_root():
    return {"message": "Hello, World!", "status": "running"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "query": q}

# For Vercel deployment
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router as api_router

app = FastAPI(title="AI Resume Builder")

# CORS Setup (Zaroori hai taaki Mobile App connect ho sake)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Sabko allow karega (Laptop, Phone, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router Connect kar rahe hain
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"status": "online", "message": "AI Resume Builder Backend is Running!"}

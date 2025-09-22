from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the routers
from .routes import polls, ws, health

app = FastAPI(
    title="PPE Polling System API",
    description="API for the Public Verification of Private Effort polling system.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the PPE Polling System API!"}

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "ok"}

# Include routers
app.include_router(polls.router)
app.include_router(health.router, prefix="/api")
app.include_router(ws.router)
app.include_router(ws.router)

from fastapi import FastAPI

from app.api.v1.git import router as git_router

app = FastAPI(
    title="AI Safe Deployment API",
    version="0.1.0"
)

# Register API Routers
app.include_router(git_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "AI Safe Deployment API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, analyze, history

app = FastAPI(title="SEO Entity Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(analyze.router, tags=["analyze"])
app.include_router(history.router, tags=["history"])

@app.get("/health")
async def health():
    return {"status": "ok"}

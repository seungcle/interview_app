from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from interview_app.backend.agents_router import router as agents_router
from interview_app.backend.interview_router import router

app = FastAPI(title="AI 면접 코치 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(agents_router)

from fastapi import FastAPI

from interview_app.backend.interview_router import router

app = FastAPI(title="AI 면접 코치 API", version="0.1.0")

app.include_router(router)

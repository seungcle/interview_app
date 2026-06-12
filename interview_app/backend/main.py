import openai
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from interview_app.backend.agents_router import router as agents_router
from interview_app.backend.interview_router import router
from interview_app.backend.resume_router import router as resume_router

app = FastAPI(title="AI 면접 코치 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(openai.RateLimitError)
async def rate_limit_handler(request: Request, exc: openai.RateLimitError) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요."})


@app.exception_handler(openai.APIError)
async def openai_api_error_handler(request: Request, exc: openai.APIError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": f"AI 서비스 오류: {exc.message}"})


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


app.include_router(router)
app.include_router(agents_router)
app.include_router(resume_router)

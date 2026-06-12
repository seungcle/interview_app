import os
from collections.abc import AsyncIterator

import openai
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from interview_app.backend.sessions import (
    add_message,
    clear_session,
    create_session,
    get_history,
    get_session_role,
    set_session_role,
)
from interview_app.core.roles import ROLES

load_dotenv()

router = APIRouter(prefix="/interview", tags=["interview"])


# ── Pydantic 모델 ───────────────────────────────────────────────────────────────

class InterviewStreamRequest(BaseModel):
    question: str = Field(..., min_length=1, description="면접관이 제시한 질문", examples=["자기소개를 해 주세요."])
    answer: str = Field(..., min_length=1, description="지원자가 입력한 답변", examples=["안녕하세요, 저는 파이썬을 공부하고 있습니다."])
    role: str = Field(default="general", description="면접관 유형 (general · technical · hr)", examples=["technical"])
    session_id: str | None = Field(default=None, description="UUID 기반 면접 세션 ID")
    model: str = Field(default="gpt-4o-mini", description="사용할 OpenAI 모델명")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="생성 온도")


class SessionCreateRequest(BaseModel):
    role: str = Field(default="general", description="초기 면접관 유형")


class SessionCreateResponse(BaseModel):
    session_id: str
    role: str


class HistoryResponse(BaseModel):
    session_id: str
    messages: list[dict[str, str]]
    role: str
    message_count: int


class RoleUpdateRequest(BaseModel):
    role: str = Field(..., description="변경할 면접관 유형 (general · technical · hr)")


class RoleUpdateResponse(BaseModel):
    session_id: str
    role: str
    message: str


class FeedbackRequest(BaseModel):
    score: int = Field(..., ge=0, le=1, description="0: 별로, 1: 좋아요")
    session_id: str | None = Field(default=None)
    message: str | None = Field(default=None)


class FeedbackResponse(BaseModel):
    received: bool


_feedback_log: list[dict] = []


# ── OpenAI 클라이언트 ────────────────────────────────────────────────────────────

def get_interview_openai_client() -> AsyncOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")
    return AsyncOpenAI(api_key=api_key)


# ── SSE generator ───────────────────────────────────────────────────────────────

async def interview_event_generator(
    request: InterviewStreamRequest,
) -> AsyncIterator[str]:
    """면접 코치 피드백을 SSE data 이벤트로 스트리밍합니다."""
    client = get_interview_openai_client()
    role = ROLES.get(request.role, ROLES["general"])

    messages: list[dict[str, str]] = [{"role": "system", "content": role.system_prompt}]

    if request.session_id:
        try:
            messages.extend(get_history(request.session_id))
        except KeyError:
            pass

    user_content = (
        f"[면접 질문]\n{request.question}\n\n"
        f"[지원자 답변]\n{request.answer}\n\n"
        "위 답변을 면접관 역할에 맞게 평가하고 개선 피드백을 제공해 주세요."
    )
    messages.append({"role": "user", "content": user_content})

    stream = await client.chat.completions.create(
        model=request.model,
        temperature=request.temperature,
        stream=True,
        messages=messages,
    )

    full_response = ""
    try:
        async for chunk in stream:
            delta = chunk.choices[0].delta
            token = delta.content or ""
            if not token:
                continue
            full_response += token
            yield f"data: {token}\n\n"
    except openai.RateLimitError:
        yield "data: ⚠️ 요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.\n\n"
    except openai.APIError as e:
        yield f"data: ⚠️ AI 서비스 오류가 발생했습니다: {e.message}\n\n"

    if request.session_id and full_response:
        try:
            add_message(request.session_id, "user", user_content)
            add_message(request.session_id, "assistant", full_response)
        except KeyError:
            pass

    yield "data: [DONE]\n\n"


# ── 엔드포인트 ──────────────────────────────────────────────────────────────────

@router.post("/stream")
async def interview_stream(request: InterviewStreamRequest) -> StreamingResponse:
    return StreamingResponse(
        interview_event_generator(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/session/create", response_model=SessionCreateResponse)
async def create_interview_session(body: SessionCreateRequest) -> SessionCreateResponse:
    session_id = create_session(body.role)
    return SessionCreateResponse(session_id=session_id, role=body.role)


@router.get("/session/{session_id}/history", response_model=HistoryResponse)
async def get_interview_history(session_id: str) -> HistoryResponse:
    try:
        messages = get_history(session_id)
        role = get_session_role(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")
    return HistoryResponse(
        session_id=session_id,
        messages=messages,
        role=role,
        message_count=len(messages),
    )


@router.patch("/session/{session_id}/role", response_model=RoleUpdateResponse)
async def update_interview_role(session_id: str, body: RoleUpdateRequest) -> RoleUpdateResponse:
    if body.role not in ROLES:
        raise HTTPException(status_code=400, detail=f"허용되지 않은 면접관 유형입니다. 허용값: {set(ROLES)}")
    try:
        set_session_role(session_id, body.role)
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")
    return RoleUpdateResponse(session_id=session_id, role=body.role, message=f"면접관 유형이 {body.role}로 변경되었습니다.")


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(body: FeedbackRequest) -> FeedbackResponse:
    _feedback_log.append({
        "score": body.score,
        "session_id": body.session_id,
        "message": body.message,
    })
    return FeedbackResponse(received=True)

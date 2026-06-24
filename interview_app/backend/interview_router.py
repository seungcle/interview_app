from __future__ import annotations

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
    create_session,
    get_history,
    get_session_role,
    get_token_log,
    log_tokens,
    set_session_role,
)
from interview_app.core.roles import ROLES

load_dotenv()

router = APIRouter(prefix="/interview", tags=["interview"])


class InterviewStreamRequest(BaseModel):
    question: str = Field(default="")
    answer: str = Field(default="")
    role: str = Field(default="general")
    session_id: str | None = Field(default=None)
    model: str = Field(default="gpt-4o-mini")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class SessionCreateRequest(BaseModel):
    role: str = Field(default="general")


class SessionCreateResponse(BaseModel):
    session_id: str
    role: str


class HistoryResponse(BaseModel):
    session_id: str
    messages: list[dict[str, str]]
    role: str
    message_count: int


class RoleUpdateRequest(BaseModel):
    role: str = Field(...)


class RoleUpdateResponse(BaseModel):
    session_id: str
    role: str
    message: str


class FeedbackRequest(BaseModel):
    score: int = Field(..., ge=0, le=1)
    session_id: str | None = Field(default=None)
    message: str | None = Field(default=None)


class FeedbackResponse(BaseModel):
    received: bool


class TokenStatsResponse(BaseModel):
    session_id: str
    token_log: list[dict]
    total_prompt: int
    total_completion: int
    total_tokens: int


def get_interview_openai_client() -> AsyncOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")
    return AsyncOpenAI(api_key=api_key)


async def interview_event_generator(request: InterviewStreamRequest) -> AsyncIterator[str]:
    client = get_interview_openai_client()
    role = ROLES.get(request.role, ROLES["general"])

    messages: list[dict[str, str]] = [{"role": "system", "content": role.system_prompt}]

    if request.session_id:
        try:
            messages.extend(get_history(request.session_id))
        except KeyError:
            pass

    if request.answer:
        user_content = (
            f"[면접 질문]\n{request.question}\n\n"
            f"[지원자 답변]\n{request.answer}\n\n"
            "위 답변을 면접관 역할에 맞게 평가하고 개선 피드백을 제공해 주세요."
        )
    else:
        user_content = "면접을 시작해주세요. 적합한 면접 질문 1개를 한국어로 해주세요."
    messages.append({"role": "user", "content": user_content})

    stream = await client.chat.completions.create(
        model=request.model,
        temperature=request.temperature,
        stream=True,
        messages=messages,
        stream_options={"include_usage": True},
    )

    full_response = ""
    usage_data = None
    try:
        async for chunk in stream:
            if chunk.usage:
                usage_data = chunk.usage
            if not chunk.choices:
                continue
            token = chunk.choices[0].delta.content or ""
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

    if request.session_id and usage_data:
        try:
            log_tokens(request.session_id, usage_data.prompt_tokens, usage_data.completion_tokens)
        except KeyError:
            pass

    yield "data: [DONE]\n\n"


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


@router.get("/session/{session_id}/stats", response_model=TokenStatsResponse)
async def get_token_stats(session_id: str) -> TokenStatsResponse:
    log = get_token_log(session_id)
    return TokenStatsResponse(
        session_id=session_id,
        token_log=log,
        total_prompt=sum(e["prompt"] for e in log),
        total_completion=sum(e["completion"] for e in log),
        total_tokens=sum(e["total"] for e in log),
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(body: FeedbackRequest) -> FeedbackResponse:
    return FeedbackResponse(received=True)

import os
from collections.abc import AsyncIterator

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

load_dotenv()

# TODO 1: UUID 세션 관리
# from interview_app.backend.sessions import create_session, add_message, get_history
# → day2-self2에서 연결. session_id 를 InterviewStreamRequest 에서 받아 get_history() 로 이전 이력을 꺼낸다.

# TODO 2: 예외 핸들러
# from interview_app.backend.errors import register_exception_handlers
# → backend/main.py 에서 register_exception_handlers(app) 로 등록한다.
# → RateLimitError → 429, APIError → 502 로 변환.

# TODO 3: 토큰 사용량 추적
# from interview_app.backend.usage import record_usage
# → stream 경로에서 usage 기록 시점이 제한될 수 있으므로 일반 /interview 엔드포인트에서 먼저 연결.

# TODO 4: 8주차 역할 프리셋 재사용
# from interview_app.core.roles import ROLES
# → 본 파일의 ROLE_PROMPTS 와 roles.py의 ROLES를 비교해 import 중심으로 재사용. 재작성 금지.

router = APIRouter(prefix="/interview", tags=["interview"])

# roles.py의 ROLES(personality/technical/executive/structured)와 병행 사용.
# general·hr 키는 이 파일에서만 정의하고, 나머지는 추후 roles.py로 교체 예정.
ROLE_PROMPTS: dict[str, str] = {
    "general": "당신은 일반 면접관입니다. 지원자의 답변을 종합적으로 평가하고 개선점을 한국어로 피드백하세요.",
    "technical": "당신은 기술 면접관입니다. 지원자의 기술 역량과 문제 해결 방식을 집중 평가하고 한국어로 피드백하세요.",
    "hr": "당신은 인사 면접관입니다. 지원자의 인성, 협업 능력, 조직 적합성을 평가하고 한국어로 피드백하세요.",
}


class InterviewStreamRequest(BaseModel):
    """면접 코치 `/interview/stream` 엔드포인트가 받는 요청 모델입니다."""

    question: str = Field(
        ...,
        min_length=1,
        description="면접관이 제시한 질문입니다.",
        examples=["자기소개를 해 주세요."],
    )
    answer: str = Field(
        ...,
        min_length=1,
        description="지원자가 입력한 답변입니다.",
        examples=["안녕하세요, 저는 파이썬을 공부하고 있습니다."],
    )
    role: str = Field(
        default="general",
        description="면접관 유형입니다. general · technical · hr 중 하나를 사용합니다.",
        examples=["technical"],
    )
    session_id: str | None = Field(
        default=None,
        description="UUID 기반 면접 세션 ID입니다. self2에서 연결합니다.",
    )
    model: str = Field(default="gpt-4o-mini", description="사용할 OpenAI 모델명입니다.")


def get_interview_openai_client() -> AsyncOpenAI:
    """환경 변수에서 OPENAI_API_KEY를 읽어 AsyncOpenAI 클라이언트를 만듭니다."""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not configured",
        )

    return AsyncOpenAI(api_key=api_key)


async def interview_event_generator(
    request: InterviewStreamRequest,
) -> AsyncIterator[str]:
    """면접 코치 피드백을 SSE data 이벤트로 스트리밍합니다."""
    client = get_interview_openai_client()

    system_prompt = ROLE_PROMPTS.get(request.role, ROLE_PROMPTS["general"])
    user_message = f"질문: {request.question}\n\n지원자 답변: {request.answer}"

    stream = await client.chat.completions.create(
        model=request.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield f"data: {delta.content}\n\n"

    yield "data: [DONE]\n\n"


@router.post("/stream")
async def interview_stream(request: InterviewStreamRequest) -> StreamingResponse:
    """면접관 유형에 맞는 피드백을 SSE 형식으로 스트리밍합니다."""
    return StreamingResponse(
        interview_event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

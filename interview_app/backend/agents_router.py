"""
Day 3 self2 책임 메모
---------------------
- 이 파일이 담당하는 것:
  → 8주차 에이전트를 감싸고 SSE로 내보내는 백엔드 라우터

- 이 파일이 담당하지 않는 것:
  → 화면 표시, 사용자 입력 처리, AI 키 관리

- Day 3 self1의 api_client.py와의 관계:
  → 프론트 api_client.py가 이 파일의 엔드포인트를 호출한다

- 8주차 파일 재사용 원칙:
  → roles.py, tools.py, agents.py는 재작성하지 않고 import만 한다.
"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator

import openai
from agents import AgentUpdatedStreamEvent, RawResponsesStreamEvent, RunItemStreamEvent, Runner
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from interview_app.core.agents import interview_agent, triage_agent

router = APIRouter(prefix="/agents", tags=["agents"])


class InterviewAgentRequest(BaseModel):
    message: str = Field(..., min_length=1, description="면접 질문 텍스트")
    mode: str = Field(default="single", description="single(일반) 또는 multi(멀티에이전트)")


async def run_interview_agent_stream(message: str, mode: str) -> AsyncIterator[str]:
    """면접 질문을 에이전트 스트림으로 실행하고 SSE 이벤트를 yield합니다."""
    agent = triage_agent if mode == "multi" else interview_agent

    try:
        stream_result = Runner.run_streamed(agent, input=message)

        async for event in stream_result.stream_events():
            if isinstance(event, RawResponsesStreamEvent):
                data = event.data
                if getattr(data, "type", None) == "response.output_text.delta":
                    delta = getattr(data, "delta", "")
                    if delta:
                        payload = {"type": "token", "delta": delta}
                        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

            elif isinstance(event, RunItemStreamEvent):
                payload = {"type": "status", "label": "run_item"}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

            elif isinstance(event, AgentUpdatedStreamEvent):
                agent_name = getattr(event.new_agent, "name", "unknown") if hasattr(event, "new_agent") else "unknown"
                payload = {"type": "status", "label": "handoff_detected", "agent": agent_name}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    except openai.RateLimitError:
        payload = {"type": "token", "delta": "⚠️ 요청이 너무 많습니다. 잠시 후 다시 시도해 주세요."}
        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    except openai.APIError as e:
        payload = {"type": "token", "delta": f"⚠️ AI 서비스 오류가 발생했습니다: {e.message}"}
        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    yield "data: [DONE]\n\n"


@router.post("/stream")
async def stream_interview_agent_endpoint(request: InterviewAgentRequest) -> StreamingResponse:
    """면접 에이전트의 스트리밍 응답을 SSE로 전달합니다."""
    return StreamingResponse(
        run_interview_agent_stream(request.message, request.mode),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

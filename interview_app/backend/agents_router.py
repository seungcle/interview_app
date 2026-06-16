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
    message: str = Field(..., min_length=1)
    mode: str = Field(default="single")


async def run_interview_agent_stream(message: str, mode: str) -> AsyncIterator[str]:
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
    return StreamingResponse(
        run_interview_agent_stream(request.message, request.mode),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

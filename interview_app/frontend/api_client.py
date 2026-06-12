from __future__ import annotations

import json
import os
from collections.abc import Iterator
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


def get_backend_url() -> str:
    """면접 코치 FastAPI 백엔드 주소를 환경변수 또는 기본값으로 가져옵니다."""
    return os.getenv("BACKEND_URL", "http://localhost:8000")


def create_interview_session(role: str = "general") -> dict[str, Any]:
    """면접 세션을 생성하고 session_id를 반환합니다."""
    with httpx.Client(base_url=get_backend_url(), timeout=10.0) as client:
        response = client.post("/interview/session/create", json={"role": role})
        response.raise_for_status()
        return response.json()


def post_interview_message(
    question: str,
    answer: str,
    role: str = "general",
    session_id: str | None = None,
    model: str = "gpt-4o-mini",
) -> dict[str, Any]:
    """백엔드에 면접 피드백 요청을 보내고 전체 응답을 반환합니다 (스트리밍 없음)."""
    payload = {
        "question": question,
        "answer": answer,
        "role": role,
        "session_id": session_id,
        "model": model,
    }
    full_text = ""
    for token in stream_interview_message(**payload):
        full_text += token
    return {"content": full_text}


def stream_interview_message(
    question: str,
    answer: str,
    role: str = "general",
    session_id: str | None = None,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
) -> Iterator[str]:
    """면접 코치 백엔드의 SSE 응답을 토큰 단위로 전달합니다."""
    payload = {
        "question": question,
        "answer": answer,
        "role": role,
        "session_id": session_id,
        "model": model,
        "temperature": temperature,
    }
    url = f"{get_backend_url()}/interview/stream"

    with httpx.stream("POST", url, json=payload, timeout=30.0) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line or not line.startswith("data:"):
                continue
            token = line[5:]
            if token.startswith(" "):
                token = token[1:]
            if token == "[DONE]":
                break
            yield token


def check_backend_health() -> bool:
    """백엔드 서버가 응답하는지 확인합니다."""
    try:
        with httpx.Client(timeout=3.0) as client:
            r = client.get(f"{get_backend_url()}/health")
            return r.status_code == 200
    except Exception:
        return False


def stream_agent_message(message: str, mode: str = "single") -> Iterator[str]:
    """에이전트 스트림 응답을 토큰 단위로 전달합니다."""
    payload = {"message": message, "mode": mode}
    url = f"{get_backend_url()}/agents/stream"
    with httpx.stream("POST", url, json=payload, timeout=60.0) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line or not line.startswith("data:"):
                continue
            raw = line[5:]
            if raw.startswith(" "):
                raw = raw[1:]
            if raw == "[DONE]":
                break
            try:
                data = json.loads(raw)
                if data.get("type") == "token":
                    yield data.get("delta", "")
            except json.JSONDecodeError:
                yield raw


def get_session_stats(session_id: str) -> dict:
    """세션의 토큰 사용량 통계를 백엔드에서 가져옵니다."""
    with httpx.Client(base_url=get_backend_url(), timeout=5.0) as client:
        response = client.get(f"/interview/session/{session_id}/stats")
        response.raise_for_status()
        return response.json()


def send_feedback(score: int, session_id: str | None = None, message: str | None = None) -> bool:
    """면접 응답 피드백(thumbs)을 백엔드에 전송합니다."""
    payload = {"score": score, "session_id": session_id, "message": message}
    with httpx.Client(base_url=get_backend_url(), timeout=5.0) as client:
        response = client.post("/interview/feedback", json=payload)
        response.raise_for_status()
        return response.json().get("received", False)


def generate_resume_questions(
    resume_text: str,
    question_count: int = 5,
    model: str = "gpt-4o-mini",
    system_prompt: str = "당신은 AI 면접 코치입니다.",
) -> dict[str, Any]:
    """백엔드를 통해 이력서 기반 면접 질문을 생성합니다."""
    payload = {
        "resume_text": resume_text,
        "question_count": question_count,
        "model": model,
        "system_prompt": system_prompt,
    }
    with httpx.Client(base_url=get_backend_url(), timeout=30.0) as client:
        response = client.post("/resume/questions", json=payload)
        response.raise_for_status()
        return response.json()


def render_agent_answer(placeholder: Any, message: str, mode: str = "single") -> str:
    """에이전트 스트림 토큰을 누적해 placeholder에 실시간으로 표시합니다."""
    full_text = ""
    for token in stream_agent_message(message, mode):
        full_text += token
        placeholder.markdown(full_text)
    return full_text


def render_streaming_answer(
    placeholder: Any,
    question: str,
    answer: str,
    role: str = "general",
    session_id: str | None = None,
    temperature: float = 0.7,
) -> str:
    """스트리밍 토큰을 누적해 면접 코치 답변을 화면에 실시간으로 표시합니다.

    Args:
        placeholder: st.empty()로 만든 Streamlit placeholder 객체
        question: 면접 질문 문자열
        answer: 지원자 답변 문자열
        role: 면접관 유형
        session_id: 면접 세션 ID (없으면 None)

    Returns:
        누적된 전체 답변 문자열
    """
    full_text = ""
    for token in stream_interview_message(question, answer, role, session_id, temperature=temperature):
        full_text += token
        placeholder.markdown(full_text)
    return full_text

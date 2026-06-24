from __future__ import annotations

import json
import os
from collections.abc import Iterator
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


def get_backend_url() -> str:
    return os.getenv("BACKEND_URL", "http://localhost:8000")


def create_interview_session(role: str = "general") -> dict[str, Any]:
    with httpx.Client(base_url=get_backend_url(), timeout=10.0) as client:
        response = client.post("/interview/session/create", json={"role": role})
        response.raise_for_status()
        return response.json()


def stream_interview_message(
    question: str,
    answer: str,
    role: str = "general",
    session_id: str | None = None,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
) -> Iterator[str]:
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
    try:
        with httpx.Client(timeout=3.0) as client:
            r = client.get(f"{get_backend_url()}/health")
            return r.status_code == 200
    except Exception:
        return False


def stream_agent_message(messages: list[dict], mode: str = "single") -> Iterator[str]:
    payload = {"messages": messages, "mode": mode}
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
    with httpx.Client(base_url=get_backend_url(), timeout=5.0) as client:
        response = client.get(f"/interview/session/{session_id}/stats")
        response.raise_for_status()
        return response.json()


def send_feedback(score: int, session_id: str | None = None, message: str | None = None) -> bool:
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


def render_agent_answer(placeholder: Any, messages: list[dict], mode: str = "single") -> str:
    full_text = ""
    for token in stream_agent_message(messages, mode):
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
    full_text = ""
    for token in stream_interview_message(question, answer, role, session_id, temperature=temperature):
        full_text += token
        placeholder.markdown(full_text)
    return full_text

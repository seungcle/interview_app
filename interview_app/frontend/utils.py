from __future__ import annotations

from typing import Any

import httpx
import streamlit as st

from interview_app.frontend.api_client import get_backend_url


def render_waiting_state(message: str):
    return st.status(message, expanded=True)


def format_error_message(error: Exception) -> dict[str, str]:
    if isinstance(error, (ConnectionError, httpx.ConnectError)):
        return {"level": "error", "message": f"백엔드 서버에 연결할 수 없습니다. uvicorn이 실행 중인지 확인하세요. ({get_backend_url()})"}
    if isinstance(error, httpx.TimeoutException):
        return {"level": "warning", "message": "요청 시간이 초과되었습니다. 잠시 후 다시 시도하세요."}
    if isinstance(error, httpx.HTTPStatusError):
        return {"level": "error", "message": f"서버 오류 {error.response.status_code}: 잠시 후 다시 시도하세요."}
    return {"level": "error", "message": "알 수 없는 오류가 발생했습니다."}


def show_api_error(error: Exception) -> None:
    result = format_error_message(error)
    if result["level"] == "warning":
        st.warning(result["message"])
    else:
        st.error(result["message"])


def render_feedback_widget(message_id: str, conversation_id: str, index: int) -> None:
    feedback_value = st.feedback("thumbs", key=f"fb_{message_id}_{index}")
    if feedback_value is not None:
        rating = "up" if feedback_value == 1 else "down"
        payload = {"conversation_id": conversation_id, "message_id": message_id, "rating": rating}
        safe_post_feedback(payload)


def safe_post_feedback(payload: dict[str, Any]) -> dict[str, Any] | None:
    try:
        response = httpx.post(f"{get_backend_url()}/feedback", json=payload, timeout=5.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        show_api_error(e)
        return None


def filter_conversations(
    messages: list[dict[str, str]],
    keyword: str,
    roles: list[str],
) -> list[dict[str, str]]:
    normalized_keyword = keyword.strip().lower()
    filtered: list[dict[str, str]] = []
    for message in messages:
        keyword_matches = not normalized_keyword or normalized_keyword in message.get("content", "").lower()
        role_matches = not roles or message.get("role") in roles
        if keyword_matches and role_matches:
            filtered.append(message)
    return filtered


def show_loading(message: str = "처리 중..."):
    return st.spinner(message)


def show_feedback_widget(key: str = "feedback") -> Any:
    return st.feedback("thumbs", key=key)


def search_messages(messages: list[dict], keyword: str) -> list[dict]:
    return filter_conversations(messages, keyword, [])

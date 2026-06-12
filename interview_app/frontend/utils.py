from __future__ import annotations

from typing import Any

import httpx
import streamlit as st

from interview_app.frontend.api_client import check_backend_health, get_backend_url


def format_error_message(error: Exception) -> str:
    """예외를 사용자에게 보여줄 한국어 메시지로 변환합니다."""
    if isinstance(error, httpx.ConnectError):
        return f"백엔드 서버에 연결할 수 없습니다. `uvicorn`이 실행 중인지 확인하세요. ({get_backend_url()})"
    if isinstance(error, httpx.HTTPStatusError):
        return f"서버 오류 {error.response.status_code}: {error.response.text[:100]}"
    if isinstance(error, httpx.TimeoutException):
        return "요청 시간이 초과되었습니다. 잠시 후 다시 시도하세요."
    return f"오류가 발생했습니다: {type(error).__name__}: {error}"


def show_backend_status() -> None:
    """사이드바에 백엔드 연결 상태를 표시합니다."""
    healthy = check_backend_health()
    if healthy:
        st.sidebar.success("백엔드 연결됨")
    else:
        st.sidebar.error("백엔드 연결 안 됨")


def show_loading(message: str = "처리 중..."):
    """st.spinner 래퍼 — with 블록 안에서 로딩 표시기를 보여 줍니다."""
    return st.spinner(message)


def show_feedback_widget(key: str = "feedback") -> Any:
    """thumbs 형태 피드백 위젯을 표시하고 결과를 반환합니다."""
    return st.feedback("thumbs", key=key)


def search_messages(messages: list[dict], keyword: str) -> list[dict]:
    """대화 이력에서 키워드가 포함된 메시지를 반환합니다."""
    if not keyword.strip():
        return messages
    kw = keyword.lower()
    return [m for m in messages if kw in m.get("content", "").lower()]

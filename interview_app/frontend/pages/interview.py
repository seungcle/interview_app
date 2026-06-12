from __future__ import annotations

import streamlit as st

from interview_app.frontend.api_client import (
    check_backend_health,
    create_interview_session,
    render_agent_answer,
    render_streaming_answer,
)

st.set_page_config(page_title="면접 연습", page_icon="🎤")
st.title("면접 연습")


def initialize_interview_state() -> None:
    if "interview_messages" not in st.session_state:
        st.session_state.interview_messages = [
            {"role": "assistant", "content": "안녕하세요! 면접 답변을 입력하면 피드백을 드립니다."}
        ]
    if "interview_session_id" not in st.session_state:
        st.session_state.interview_session_id = None
    if "interview_mode" not in st.session_state:
        st.session_state.interview_mode = "single"


initialize_interview_state()

# ── 사이드바 ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("면접 설정")

    labels = {"single": "일반", "multi": "멀티에이전트", "direct": "직접 OpenAI"}
    mode = st.radio("에이전트 모드", ["single", "multi", "direct"], format_func=lambda m: labels[m])
    st.session_state.interview_mode = mode

    if st.button("새 세션 시작"):
        try:
            settings = st.session_state.get("settings", {})
            result = create_interview_session(settings.get("role", "general"))
            st.session_state.interview_session_id = result["session_id"]
            st.session_state.interview_messages = [
                {"role": "assistant", "content": "새 면접 세션이 시작되었습니다. 면접 답변을 입력해 주세요."}
            ]
            st.success(f"세션 생성: {result['session_id'][:8]}...")
        except Exception as e:
            st.error(f"세션 생성 실패: {e}")

    st.divider()
    backend_ok = check_backend_health()
    st.caption(f"백엔드 상태: {'🟢 연결됨' if backend_ok else '🔴 연결 안 됨'}")
    if st.session_state.interview_session_id:
        st.caption(f"세션 ID: {st.session_state.interview_session_id[:8]}...")

# ── 채팅 화면 ────────────────────────────────────────────────────────────────────
for message in st.session_state.interview_messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("면접 답변을 입력해 주세요.")
if user_input:
    st.session_state.interview_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            if not check_backend_health():
                raise ConnectionError("백엔드 서버에 연결할 수 없습니다.")

            settings = st.session_state.get("settings", {})
            mode = st.session_state.interview_mode

            if mode in ("single", "multi"):
                response_text = render_agent_answer(placeholder, user_input, mode)
            else:
                prev_msgs = st.session_state.interview_messages
                question = next(
                    (m["content"] for m in reversed(prev_msgs[:-1]) if m["role"] == "assistant"),
                    "면접 질문",
                )
                response_text = render_streaming_answer(
                    placeholder,
                    question=question,
                    answer=user_input,
                    role=settings.get("role", "general"),
                    session_id=st.session_state.interview_session_id,
                    temperature=float(settings.get("temperature", 0.7)),
                )
        except Exception as e:
            response_text = f"⚠️ 오류가 발생했습니다: {e}"
            placeholder.markdown(response_text)

    st.session_state.interview_messages.append({"role": "assistant", "content": response_text})
    st.rerun()

from __future__ import annotations

import streamlit as st

from interview_app.frontend.api_client import (
    check_backend_health,
    create_interview_session,
    render_agent_answer,
    render_streaming_answer,
    send_feedback,
)
from interview_app.frontend.utils import format_error_message, show_api_error, show_feedback_widget

st.title("면접 연습")


def initialize_interview_state() -> None:
    if "interview_messages" not in st.session_state:
        st.session_state.interview_messages = []
    if "interview_session_id" not in st.session_state:
        st.session_state.interview_session_id = None
    if "interview_mode" not in st.session_state:
        st.session_state.interview_mode = "single"
    if "interview_started" not in st.session_state:
        st.session_state.interview_started = False


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
            st.session_state.interview_messages = []
            st.session_state.interview_started = False
            st.success(f"세션 생성: {result['session_id'][:8]}...")
            st.rerun()
        except Exception as e:
            st.error(f"세션 생성 실패: {e}")

    st.divider()
    backend_ok = check_backend_health()
    st.caption(f"백엔드 상태: {'🟢 연결됨' if backend_ok else '🔴 연결 안 됨'}")
    if st.session_state.interview_session_id:
        st.caption(f"세션 ID: {st.session_state.interview_session_id[:8]}...")

# ── 첫 질문 자동 생성 ────────────────────────────────────────────────────────────
if not st.session_state.interview_started:
    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            if not check_backend_health():
                raise ConnectionError("백엔드 서버에 연결할 수 없습니다.")
            settings = st.session_state.get("settings", {})
            mode = st.session_state.interview_mode
            if mode in ("single", "multi"):
                response_text = render_agent_answer(placeholder, [], mode)
            else:
                response_text = render_streaming_answer(
                    placeholder,
                    question="",
                    answer="",
                    role=settings.get("role", "general"),
                    session_id=st.session_state.interview_session_id,
                    temperature=float(settings.get("temperature", 0.7)),
                )
        except Exception as e:
            show_api_error(e)
            response_text = format_error_message(e)["message"]
            placeholder.empty()
    st.session_state.interview_messages.append({"role": "assistant", "content": response_text})
    st.session_state.interview_started = True
    st.rerun()

# ── 채팅 화면 ────────────────────────────────────────────────────────────────────
for message in st.session_state.interview_messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# ── 피드백 위젯 ──────────────────────────────────────────────────────────────────
msgs = st.session_state.interview_messages
last_asst = next((m for m in reversed(msgs) if m["role"] == "assistant"), None)
if last_asst and len(msgs) > 1:
    fb_sent_key = f"fb_sent_{len(msgs)}"
    if fb_sent_key not in st.session_state:
        st.caption("마지막 응답이 도움이 됐나요?")
        fb = show_feedback_widget(key=f"fb_{len(msgs)}")
        if fb is not None:
            try:
                send_feedback(fb, st.session_state.interview_session_id, last_asst["content"][:100])
            except Exception:
                pass
            st.session_state[fb_sent_key] = fb
            st.rerun()
    else:
        score = st.session_state[fb_sent_key]
        st.caption("👍 피드백 감사합니다!" if score == 1 else "👎 피드백 감사합니다!")

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
                start_trigger = [{"role": "user", "content": "면접을 시작해주세요."}]
                agent_messages = start_trigger + [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.interview_messages
                ]
                response_text = render_agent_answer(placeholder, agent_messages, mode)
            else:
                prev_msgs = st.session_state.interview_messages
                question = next(
                    (m["content"] for m in reversed(prev_msgs[:-1]) if m["role"] == "assistant"),
                    "",
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
            show_api_error(e)
            response_text = format_error_message(e)["message"]
            placeholder.empty()

    st.session_state.interview_messages.append({"role": "assistant", "content": response_text})
    st.rerun()

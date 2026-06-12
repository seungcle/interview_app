import json

import streamlit as st

from interview_app.core.roles import FRAME_HINTS, ROLES
from interview_app.frontend.api_client import check_backend_health, render_streaming_answer

st.set_page_config(
    page_title="AI 면접 코치",
    page_icon="🎤",
)


# ── 헬퍼 함수 ──────────────────────────────────────────────────────────────────

def get_interviewer_options() -> dict[str, str]:
    """면접관 유형의 키와 화면 표시 이름을 반환합니다."""
    return {key: role.display_name for key, role in ROLES.items()}


def get_system_prompt(role_key: str) -> str:
    """선택한 면접관 유형의 시스템 프롬프트를 반환합니다."""
    return ROLES[role_key].system_prompt




# ── session_state 초기화 ────────────────────────────────────────────────────────

def initialize_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "안녕하세요! AI 면접 코치입니다. 면접 답변을 입력해 주시면 후속 질문을 드리겠습니다.",
            }
        ]
    if "selected_role" not in st.session_state:
        st.session_state.selected_role = "personality"


initialize_state()


# ── 사이드바 ────────────────────────────────────────────────────────────────────

options = get_interviewer_options()

with st.sidebar:
    st.header("면접관 설정")

    selected_label = st.selectbox(
        "면접관 유형",
        options=list(options.values()),
        index=list(options.keys()).index(st.session_state.selected_role),
    )
    st.session_state.selected_role = [k for k, v in options.items() if v == selected_label][0]

    role_key = st.session_state.selected_role
    st.caption(f"프레임: **{FRAME_HINTS[role_key]}**")

    with st.expander("시스템 프롬프트 미리보기"):
        st.text(get_system_prompt(role_key).strip()[:120] + "...")

    st.divider()
    st.subheader("Day2 입력 준비 상태")

    messages = st.session_state.messages
    user_msgs = [m for m in messages if m["role"] == "user"]
    asst_msgs = [m for m in messages if m["role"] == "assistant"]

    st.write(f"선택된 면접관: **{options[role_key]}**")
    st.write(f"총 메시지 수: **{len(messages)}**")

    if user_msgs:
        st.write(f"마지막 답변: {user_msgs[-1]['content'][:40]}...")
    if len(asst_msgs) > 1:
        st.write(f"마지막 코치 응답: {asst_msgs[-1]['content'][:50]}...")

    interview_record = {
        "role": role_key,
        "message_count": len(messages),
        "ready_for_day2": len(messages) >= 2,
    }
    st.json(interview_record)

    st.divider()
    st.download_button(
        label="면접 기록 내려받기",
        data=json.dumps(messages, ensure_ascii=False, indent=2),
        file_name="interview_record.json",
        mime="application/json",
    )


# ── 메인 채팅 화면 ───────────────────────────────────────────────────────────────

st.title("AI 면접 코치")
st.caption(f"현재 면접관: **{options[st.session_state.selected_role]}** — 답변을 입력하면 후속 질문을 드립니다.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("면접 답변을 입력해 주세요.")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            prev_msgs = st.session_state.messages
            question = next(
                (m["content"] for m in reversed(prev_msgs[:-1]) if m["role"] == "assistant"),
                "면접 질문",
            )
            response_text = render_streaming_answer(
                placeholder,
                question=question,
                answer=user_input,
                role=st.session_state.selected_role,
            )
        except Exception as e:
            response_text = f"⚠️ 백엔드 연결 오류: {e}"
            placeholder.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.rerun()

from __future__ import annotations

import json

import streamlit as st

from interview_app.core.roles import FRAME_HINTS, ROLES
from interview_app.frontend.api_client import render_streaming_answer
from interview_app.frontend.utils import format_error_message, show_api_error

st.set_page_config(page_title="AI 면접 코치", page_icon="🎤")


def get_interviewer_options() -> dict[str, str]:
    return {key: role.display_name for key, role in ROLES.items()}


def get_system_prompt(role_key: str) -> str:
    return ROLES[role_key].system_prompt


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


def run_home() -> None:
    initialize_state()

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
        st.download_button(
            label="면접 기록 내려받기",
            data=json.dumps(st.session_state.messages, ensure_ascii=False, indent=2),
            file_name="interview_record.json",
            mime="application/json",
        )

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
                show_api_error(e)
                response_text = format_error_message(e)["message"]
                placeholder.empty()

        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.rerun()


pg = st.navigation(
    [
        st.Page(run_home, title="AI 면접 코치", icon="🎤", default=True),
        st.Page("pages/interview.py", title="면접 연습", icon="🎤"),
        st.Page("pages/resume.py", title="이력서 분석", icon="📄"),
        st.Page("pages/settings.py", title="설정", icon="⚙️"),
        st.Page("pages/report.py", title="리포트", icon="📊"),
    ]
)
pg.run()

from __future__ import annotations

import streamlit as st

from interview_app.core.roles import ROLES

st.set_page_config(page_title="설정", page_icon="⚙️")
st.title("면접 코치 설정")


def initialize_settings() -> None:
    if "settings" not in st.session_state:
        st.session_state.settings = {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "system_prompt": "당신은 AI 면접 코치입니다.",
            "role": "general",
        }


initialize_settings()

st.subheader("모델 설정")
model = st.selectbox(
    "OpenAI 모델",
    ["gpt-4o-mini", "gpt-4o"],
    index=0 if st.session_state.settings["model"] == "gpt-4o-mini" else 1,
)

temperature = st.slider("Temperature", 0.0, 1.0, float(st.session_state.settings["temperature"]), 0.1)

st.subheader("면접관 설정")
role_options = {key: role.display_name for key, role in ROLES.items()}
role_options["general"] = "일반 면접관"
role = st.selectbox(
    "기본 면접관 유형",
    list(role_options.keys()),
    format_func=lambda k: role_options[k],
    index=list(role_options.keys()).index(st.session_state.settings.get("role", "general")),
)

st.subheader("시스템 프롬프트")
system_prompt = st.text_area(
    "시스템 프롬프트",
    value=st.session_state.settings["system_prompt"],
    height=150,
)

if st.button("설정 저장", type="primary"):
    st.session_state.settings = {
        "model": model,
        "temperature": temperature,
        "system_prompt": system_prompt,
        "role": role,
    }
    st.success("설정이 저장되었습니다.")

with st.expander("현재 저장된 설정 확인"):
    st.json(st.session_state.settings)

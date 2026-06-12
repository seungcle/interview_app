import streamlit as st

from interview_app.core.roles import ROLES, FRAME_HINTS

st.set_page_config(
    page_title="AI 면접 코치",
    page_icon="🎤",
)

st.title("AI 면접 코치")
st.caption("면접 답변을 입력하면 면접관이 후속 질문을 드립니다.")


def initialize_messages() -> None:
    """면접 대화 기록이 없으면 초기 안내 메시지를 준비합니다."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "안녕하세요! AI 면접 코치입니다. 면접 답변을 입력해 주시면 후속 질문을 드리겠습니다.",
            }
        ]


initialize_messages()


def handle_user_input(user_text: str) -> None:
    """사용자 입력을 받아 메시지 목록에 저장합니다."""
    user_message = {"role": "user", "content": user_text}
    assistant_message = {
        "role": "assistant",
        "content": "면접 답변을 확인했습니다. (임시 응답)",
    }
    st.session_state.messages.append(user_message)
    st.session_state.messages.append(assistant_message)


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("면접 답변을 입력해 주세요.")
if user_input:
    handle_user_input(user_input)
    st.rerun()

with st.expander("면접 코치 설정 확인"):
    st.write("**역할 프리셋 목록**")
    for key, role in ROLES.items():
        st.write(f"- `{key}`: {role.display_name} (프레임: {FRAME_HINTS[key]})")
    st.write(f"**현재 메시지 수:** {len(st.session_state.messages)}")
    st.write("**시스템 프롬프트 미리보기 (첫 50자)**")
    for key, role in ROLES.items():
        st.write(f"- {role.display_name}: {role.system_prompt.strip()[:50]}...")

# ============================
# day1-self2 TODO
# ============================
# TODO 1: 면접관 유형 사이드바 위젯 추가 (압박/편안/기술/인성 선택)
# TODO 2: 선택한 면접관 유형을 st.session_state에 저장하기
# TODO 3: st.write_stream 출력 흐름 연결 (임시 generator 사용)
# TODO 4: 면접 기록 (면접관 유형 + 질문 + 답변 + 코치 응답) 구조 설계
# ============================

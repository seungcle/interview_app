from __future__ import annotations

import json
from datetime import datetime

import streamlit as st


def build_report(session_messages: list[dict], resume_questions: list[str], file_name: str, role: str) -> dict:
    """면접 세션 데이터를 리포트 딕셔너리로 정리합니다."""
    return {
        "generated_at": datetime.now().isoformat(),
        "role": role,
        "resume_file": file_name,
        "resume_questions": resume_questions,
        "resume_question_count": len(resume_questions),
        "interview_messages": session_messages,
        "interview_turn_count": sum(1 for m in session_messages if m["role"] == "user"),
    }


def render_report_page() -> None:
    """리포트 페이지를 화면에 표시하고 다운로드 버튼을 제공합니다."""
    st.title("면접 준비 리포트")
    st.caption("오늘의 면접 연습 결과를 정리합니다.")

    messages = st.session_state.get("interview_messages", [])
    resume_questions = st.session_state.get("resume_questions", [])
    file_name = st.session_state.get("resume_file_name", "없음")
    role = st.session_state.get("settings", {}).get("role", "general")

    report = build_report(messages, resume_questions, file_name, role)

    col1, col2, col3 = st.columns(3)
    col1.metric("면접 턴 수", report["interview_turn_count"])
    col2.metric("이력서 질문 수", report["resume_question_count"])
    col3.metric("분석 파일", file_name[:12] + "..." if len(file_name) > 12 else file_name)

    if resume_questions:
        st.subheader("이력서 기반 면접 질문")
        for i, q in enumerate(resume_questions, 1):
            st.write(f"**{i}.** {q}")

    if messages:
        st.subheader("면접 대화 이력")
        for msg in messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    st.divider()
    report_json = json.dumps(report, ensure_ascii=False, indent=2)
    st.download_button(
        label="리포트 JSON 내려받기",
        data=report_json,
        file_name=f"interview_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
    )
    st.download_button(
        label="대화 이력 내려받기",
        data=json.dumps(messages, ensure_ascii=False, indent=2),
        file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
    )


render_report_page()

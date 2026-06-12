from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from interview_app.frontend.api_client import get_session_stats

st.set_page_config(page_title="면접 리포트", page_icon="📊")


def build_report(session_messages: list[dict], resume_questions: list[str], file_name: str, role: str) -> dict:
    return {
        "generated_at": datetime.now().isoformat(),
        "role": role,
        "resume_file": file_name,
        "resume_questions": resume_questions,
        "resume_question_count": len(resume_questions),
        "interview_messages": session_messages,
        "interview_turn_count": sum(1 for m in session_messages if m["role"] == "user"),
    }


st.title("면접 준비 리포트")
st.caption("오늘의 면접 연습 결과를 정리합니다.")

messages = st.session_state.get("interview_messages", [])
resume_questions = st.session_state.get("resume_questions", [])
file_name = st.session_state.get("resume_file_name", "없음")
role = st.session_state.get("settings", {}).get("role", "general")
session_id = st.session_state.get("interview_session_id")

report = build_report(messages, resume_questions, file_name, role)

# ── 기본 메트릭 ───────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("면접 턴 수", report["interview_turn_count"])
col2.metric("이력서 질문 수", report["resume_question_count"])
col3.metric("분석 파일", file_name[:12] + "..." if len(file_name) > 12 else file_name)

# ── 토큰 사용량 대시보드 ──────────────────────────────────────────────────────────
st.subheader("토큰 사용량")

if session_id:
    try:
        stats = get_session_stats(session_id)
        token_log = stats.get("token_log", [])

        tcol1, tcol2, tcol3 = st.columns(3)
        tcol1.metric("총 토큰", stats["total_tokens"])
        tcol2.metric("입력 토큰", stats["total_prompt"])
        tcol3.metric("출력 토큰", stats["total_completion"])

        if token_log:
            st.caption("턴별 토큰 사용량")
            chart_data = {
                "입력": [e["prompt"] for e in token_log],
                "출력": [e["completion"] for e in token_log],
            }
            st.bar_chart(chart_data)
        else:
            st.info("direct 모드로 면접을 진행하면 턴별 토큰 사용량이 표시됩니다.")
    except Exception:
        st.info("세션 통계를 불러올 수 없습니다. 면접 연습 후 다시 확인하세요.")
else:
    st.info("면접 연습 페이지에서 '새 세션 시작'을 누른 뒤 direct 모드로 대화하면 토큰 현황을 볼 수 있습니다.")

st.divider()

# ── 이력서 질문 + 대화 이력 ────────────────────────────────────────────────────────
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

# ── 다운로드 ──────────────────────────────────────────────────────────────────────
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

from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from interview_app.frontend.api_client import get_session_stats
from interview_app.frontend.report import (
    build_interview_report,
    render_final_dashboard,
    render_report_download,
)

st.title("면접 준비 리포트")
st.caption("오늘의 면접 연습 결과를 정리합니다.")

messages = st.session_state.get("interview_messages", [])
resume_questions = st.session_state.get("resume_questions", [])
file_name = st.session_state.get("resume_file_name", "없음")
session_id = st.session_state.get("interview_session_id")

col1, col2, col3 = st.columns(3)
col1.metric("면접 턴 수", sum(1 for m in messages if m["role"] == "user"))
col2.metric("이력서 질문 수", len(resume_questions))
col3.metric("분석 파일", file_name[:12] + "..." if len(file_name) > 12 else file_name)

st.subheader("토큰 사용량")

usage_summary: dict = {
    "request_count": 0,
    "total_tokens": 0,
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "daily_limit_ratio": 0.0,
}
token_log: list = []

if session_id:
    try:
        stats = get_session_stats(session_id)
        token_log = stats.get("token_log", [])
        usage_summary.update({
            "request_count": len(token_log),
            "total_tokens": stats["total_tokens"],
            "prompt_tokens": stats["total_prompt"],
            "completion_tokens": stats["total_completion"],
        })
        render_final_dashboard(usage_summary)
        if token_log:
            st.caption("턴별 토큰 사용량")
            st.bar_chart({"입력": [e["prompt"] for e in token_log], "출력": [e["completion"] for e in token_log]})
        else:
            st.info("direct 모드로 면접을 진행하면 턴별 토큰 사용량이 표시됩니다.")
    except Exception:
        st.info("세션 통계를 불러올 수 없습니다. 면접 연습 후 다시 확인하세요.")
else:
    st.info("면접 연습 페이지에서 '새 세션 시작'을 누른 뒤 direct 모드로 대화하면 토큰 현황을 볼 수 있습니다.")

st.divider()

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

conversation = {
    "title": f"면접 세션 ({datetime.now().strftime('%Y-%m-%d')})",
    "messages": messages,
}
render_report_download(session_id or "unknown", conversation, usage_summary)

if messages:
    st.download_button(
        label="대화 이력 내려받기 (JSON)",
        data=json.dumps(messages, ensure_ascii=False, indent=2),
        file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
    )

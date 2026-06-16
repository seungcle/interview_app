from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st


def render_final_dashboard(usage_summary: dict[str, Any]) -> None:
    col1, col2 = st.columns(2)
    col1.metric("총 요청 수", f"{usage_summary.get('request_count', 0)}회")
    col2.metric("총 토큰", f"{usage_summary.get('total_tokens', 0):,}")

    prompt = usage_summary.get("prompt_tokens", 0)
    completion = usage_summary.get("completion_tokens", 0)
    if prompt or completion:
        st.bar_chart({"입력(prompt)": [prompt], "출력(completion)": [completion]})

    ratio = min(float(usage_summary.get("daily_limit_ratio", 0.0)), 1.0)
    st.progress(ratio)


def build_interview_report(
    conversation: dict[str, Any],
    usage_summary: dict[str, Any],
    feedback_summary: dict[str, int] | None = None,
) -> str:
    title = conversation.get("title", "면접 세션")
    messages = conversation.get("messages", [])
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"# 면접 리포트 - {title}",
        "",
        f"- 생성 시각: {generated_at}",
        f"- 총 턴 수: {sum(1 for m in messages if m.get('role') == 'user')}",
        "",
        "## 대화 이력",
        "",
        "| # | 역할 | 내용 |",
        "|---|------|------|",
    ]
    for i, msg in enumerate(messages, start=1):
        role = msg.get("role", "")
        content = msg.get("content", "").replace("\n", " ")[:80]
        lines.append(f"| {i} | {role} | {content} |")

    if feedback_summary:
        lines += [
            "",
            "## 피드백 요약",
            "",
            f"- 좋아요: {feedback_summary.get('up', 0)}회",
            f"- 싫어요: {feedback_summary.get('down', 0)}회",
        ]

    lines += [
        "",
        "## 사용량 요약",
        "",
        f"- 총 요청 수: {usage_summary.get('request_count', 0)}회",
        f"- 총 토큰: {usage_summary.get('total_tokens', 0):,}",
        f"- 입력 토큰: {usage_summary.get('prompt_tokens', 0):,}",
        f"- 출력 토큰: {usage_summary.get('completion_tokens', 0):,}",
    ]

    return "\n".join(lines)


def render_report_download(
    session_id: str,
    conversation: dict[str, Any] | None,
    usage_summary: dict[str, Any],
) -> None:
    if not conversation:
        st.info("리포트를 만들 세션을 먼저 선택하세요.")
        return
    messages = conversation.get("messages", [])
    if not messages:
        st.warning("선택한 세션에 메시지가 없습니다.")
        return
    report_md = build_interview_report(conversation, usage_summary)
    st.download_button(
        label="리포트 다운로드 (Markdown)",
        data=report_md,
        file_name=f"interview_{session_id}.md",
        mime="text/markdown",
    )

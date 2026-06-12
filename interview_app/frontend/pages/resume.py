"""
Day 4 self2 책임 메모
---------------------
- 이 파일이 담당하는 것:
  → 이력서 .txt 업로드, 텍스트 읽기, 맞춤 질문 생성 요청 준비,
    Function Calling 확인 데이터 표시, 질문 생성 대시보드.

- 이 파일이 담당하지 않는 것:
  → 면접 채팅 전체 화면 복사, API 키 입력, 8주차 agents 파일 수정.

- Day 5 self1로 넘길 값:
  → resume_file_name, resume_questions, resume_question_count, resume_step4b_done.
"""
from __future__ import annotations

import streamlit as st

from interview_app.frontend.api_client import generate_resume_questions as _generate_questions

st.set_page_config(page_title="이력서 분석", page_icon="📄")
st.title("이력서 분석")
st.caption("이력서를 업로드하면 맞춤 면접 질문을 생성합니다.")


# ── 헬퍼 함수 ──────────────────────────────────────────────────────────────────

def read_resume_text(uploaded_file) -> str:
    """업로드된 이력서 파일에서 면접 질문 생성용 텍스트를 준비합니다."""
    if uploaded_file is None:
        return ""
    text = uploaded_file.read().decode("utf-8")
    if not text or len(text.strip()) < 30:
        st.warning("이력서 내용이 너무 짧습니다. 더 자세한 내용을 포함한 파일을 업로드하세요.")
        return ""
    return text.strip()


def build_resume_question_request(resume_text: str, question_count: int) -> dict:
    """이력서 기반 면접 질문 생성 요청 값을 만듭니다."""
    settings = st.session_state.get("settings", {})
    return {
        "resume_text": resume_text,
        "question_count": question_count,
        "model": settings.get("model", "gpt-4o-mini"),
        "system_prompt": settings.get("system_prompt", "당신은 AI 면접 코치입니다."),
        "role": settings.get("role", "general"),
    }


def generate_questions_with_function_calling(request: dict) -> dict:
    """백엔드를 통해 이력서 기반 면접 질문을 생성합니다."""
    result = _generate_questions(
        resume_text=request["resume_text"],
        question_count=request["question_count"],
        model=request.get("model", "gpt-4o-mini"),
        system_prompt=request.get("system_prompt", "당신은 AI 면접 코치입니다."),
    )
    return {
        "questions": result["questions"],
        "tool_calls": [
            {
                "name": "generate_interview_questions",
                "arguments": {"section": "full_resume"},
                "result": {"keywords": result["keywords"]},
            }
        ],
    }


def render_function_call_result(result: dict) -> None:
    """질문 생성 결과와 도구 호출 확인 데이터를 분리해 표시합니다."""
    questions = result.get("questions", [])
    tool_calls = result.get("tool_calls", [])

    st.subheader("생성된 면접 질문")
    if questions:
        for i, q in enumerate(questions, 1):
            st.write(f"**{i}.** {q}")
    else:
        st.info("생성된 질문이 없습니다.")

    with st.expander("Function Calling 상세 확인"):
        if tool_calls:
            st.json(tool_calls)
        else:
            st.write("호출 없음")


def save_resume_question_state(file_name: str, questions: list[str]) -> None:
    """이력서 기반 질문 생성 결과를 세션 상태에 저장합니다."""
    st.session_state["resume_file_name"] = file_name
    st.session_state["resume_questions"] = questions
    st.session_state["resume_question_count"] = len(questions)
    # Day 5 report.py가 읽을 완료 플래그 — 질문이 1개 이상일 때만 True
    st.session_state["resume_step4b_done"] = len(questions) > 0


def render_resume_dashboard() -> None:
    """이력서 기반 질문 생성 결과를 대시보드로 표시합니다."""
    questions = st.session_state.get("resume_questions", [])
    question_count = st.session_state.get("resume_question_count", 0)
    file_name = st.session_state.get("resume_file_name", "없음")
    done = st.session_state.get("resume_step4b_done", False)

    col1, col2, col3 = st.columns(3)
    col1.metric("생성된 질문 수", question_count)
    col2.metric("분석 파일", file_name[:15] + "..." if len(file_name) > 15 else file_name)
    col3.metric("Step 4-B", "완료" if done else "미완료")

    if questions:
        # 질문 길이 분포 (30자 이하 / 31~60자 / 60자 초과)
        short = sum(1 for q in questions if len(q) <= 30)
        mid = sum(1 for q in questions if 31 <= len(q) <= 60)
        long = sum(1 for q in questions if len(q) > 60)
        st.bar_chart({"30자 이하": short, "31~60자": mid, "60자 초과": long})

    progress_value = min(question_count / 10, 1.0)
    st.progress(progress_value, text=f"목표 10문제 기준 {question_count}/10 완료")


# ── 화면 ────────────────────────────────────────────────────────────────────────

uploaded_file = st.file_uploader("이력서 텍스트 파일을 업로드하세요", type=["txt"])
resume_text = read_resume_text(uploaded_file)

if resume_text:
    with st.expander("이력서 미리보기", expanded=False):
        st.text_area("내용 (앞 500자)", value=resume_text[:500], height=150, disabled=True)

    question_count = st.number_input("생성할 질문 수", min_value=3, max_value=10, value=5, step=1)

    if st.button("이력서 기반 질문 생성", type="primary"):
        request = build_resume_question_request(resume_text, question_count)
        with st.spinner("질문 생성 중..."):
            try:
                result = generate_questions_with_function_calling(request)
            except Exception as e:
                st.error(f"질문 생성 실패: {e}")
                result = None

        if result:
            questions = result.get("questions", [])
            save_resume_question_state(uploaded_file.name, questions)
            render_function_call_result(result)
else:
    st.info("이력서 .txt 파일을 업로드하면 맞춤 면접 질문을 생성합니다.")

st.divider()
render_resume_dashboard()

# ============================
# Day 5 연결 메모
# ============================
# - frontend/utils.py: 반복 표시/오류 처리 함수 정리
# - report.py: resume_questions, resume_file_name 읽어 면접 준비 리포트 생성
# - README.md: 실행 순서(uvicorn 8000, streamlit 8501) 정리
# ============================

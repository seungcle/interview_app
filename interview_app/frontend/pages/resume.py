from __future__ import annotations

import streamlit as st

from interview_app.frontend.api_client import generate_resume_questions as _generate_questions

st.title("이력서 분석")
st.caption("이력서를 업로드하면 맞춤 면접 질문을 생성합니다.")


def read_resume_text(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    text = uploaded_file.read().decode("utf-8")
    if not text or len(text.strip()) < 30:
        st.warning("이력서 내용이 너무 짧습니다. 더 자세한 내용을 포함한 파일을 업로드하세요.")
        return ""
    return text.strip()


def build_resume_question_request(resume_text: str, question_count: int) -> dict:
    settings = st.session_state.get("settings", {})
    return {
        "resume_text": resume_text,
        "question_count": question_count,
        "model": settings.get("model", "gpt-4o-mini"),
        "system_prompt": settings.get("system_prompt", "당신은 AI 면접 코치입니다."),
    }


def generate_questions_with_function_calling(request: dict) -> dict:
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
    st.session_state["resume_file_name"] = file_name
    st.session_state["resume_questions"] = questions
    st.session_state["resume_question_count"] = len(questions)
    st.session_state["resume_step4b_done"] = len(questions) > 0


def render_resume_dashboard() -> None:
    questions = st.session_state.get("resume_questions", [])
    question_count = st.session_state.get("resume_question_count", 0)
    file_name = st.session_state.get("resume_file_name", "없음")
    done = st.session_state.get("resume_step4b_done", False)

    col1, col2, col3 = st.columns(3)
    col1.metric("생성된 질문 수", question_count)
    col2.metric("분석 파일", file_name[:15] + "..." if len(file_name) > 15 else file_name)
    col3.metric("Step 4-B", "완료" if done else "미완료")

    if questions:
        short = sum(1 for q in questions if len(q) <= 30)
        mid = sum(1 for q in questions if 31 <= len(q) <= 60)
        long = sum(1 for q in questions if len(q) > 60)
        st.bar_chart({"30자 이하": short, "31~60자": mid, "60자 초과": long})

    progress_value = min(question_count / 10, 1.0)
    st.progress(progress_value, text=f"목표 10문제 기준 {question_count}/10 완료")


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

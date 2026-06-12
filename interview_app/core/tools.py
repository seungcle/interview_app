from __future__ import annotations

from agents import function_tool

from interview_app.core.roles import FRAME_HINTS, ROLES


@function_tool
def get_interview_frame(role_key: str) -> str:
    """면접 유형의 권장 답변 프레임(STAR/PREP/CAR)을 반환합니다."""
    frame = FRAME_HINTS.get(role_key, "STAR")
    role_name = ROLES[role_key].display_name if role_key in ROLES else role_key
    return f"{role_name} 면접의 권장 프레임은 {frame}입니다."


@function_tool
def check_answer_structure(answer: str) -> str:
    """지원자 답변의 길이와 구조 충족 여부를 간단히 점검합니다."""
    word_count = len(answer.split())
    if word_count < 20:
        return "답변이 너무 짧습니다. 구체적인 상황·행동·결과를 포함해 보완해 주세요."
    if word_count > 300:
        return f"답변이 {word_count}단어로 깁니다. 핵심만 남기고 압축해 보세요."
    return f"답변 길이 {word_count}단어. 구조 점검을 진행합니다."

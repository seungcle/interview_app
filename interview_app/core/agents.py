from __future__ import annotations

from agents import Agent, handoff

from interview_app.core.roles import ROLES
from interview_app.core.tools import check_answer_structure, get_interview_frame

# ── 단일 면접 코치 (single 모드) ────────────────────────────────────────────────
interview_agent = Agent(
    name="AI 면접 코치",
    instructions=(
        "당신은 AI 면접 코치입니다. 지원자의 답변을 평가하고 개선 피드백을 한국어로 제공합니다. "
        "답변의 구조(STAR/PREP/CAR), 구체성, 설득력을 기준으로 평가하고 "
        "후속 질문 2개를 제시하세요."
    ),
    tools=[get_interview_frame, check_answer_structure],
)

# ── 전문 면접관 에이전트 (multi 모드용) ─────────────────────────────────────────
personality_agent = Agent(
    name="personality_interviewer",
    instructions=ROLES["personality"].system_prompt,
    tools=[get_interview_frame, check_answer_structure],
)

technical_agent = Agent(
    name="technical_interviewer",
    instructions=ROLES["technical"].system_prompt,
    tools=[get_interview_frame, check_answer_structure],
)

executive_agent = Agent(
    name="executive_interviewer",
    instructions=ROLES["executive"].system_prompt,
)

structured_agent = Agent(
    name="structured_interviewer",
    instructions=ROLES["structured"].system_prompt,
    tools=[check_answer_structure],
)

# ── 트리아지 에이전트 (multi 모드 진입점) ───────────────────────────────────────
triage_agent = Agent(
    name="면접 코디네이터",
    instructions=(
        "당신은 면접 요청을 분석해 적합한 면접관에게 연결하는 코디네이터입니다.\n"
        "- 기술·코드·구현 관련 → 기술 면접관\n"
        "- 협업·갈등·성장 관련 → 인성 면접관\n"
        "- 조직·직무·목표 관련 → 임원 면접관\n"
        "- STAR 구조 점검 필요 → 구조화 면접관\n"
        "반드시 적합한 면접관에게 handoff 하세요."
    ),
    handoffs=[
        handoff(technical_agent),
        handoff(personality_agent),
        handoff(executive_agent),
        handoff(structured_agent),
    ],
)

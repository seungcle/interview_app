from __future__ import annotations

import json
import os

from fastapi import APIRouter, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

router = APIRouter(prefix="/resume", tags=["resume"])

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_interview_questions",
            "strict": True,
            "description": "이력서를 분석해 맞춤 면접 질문을 생성합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "이력서에서 추출한 핵심 키워드",
                    },
                    "questions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "키워드 기반으로 생성된 면접 질문 목록. 키워드가 없으면 빈 배열.",
                    },
                },
                "required": ["keywords", "questions"],
                "additionalProperties": False,
            },
        },
    }
]


class ResumeQuestionRequest(BaseModel):
    resume_text: str = Field(..., min_length=30)
    question_count: int = Field(default=5, ge=3, le=10)
    model: str = Field(default="gpt-4o-mini")
    system_prompt: str = Field(default="당신은 AI 면접 코치입니다.")


class ResumeQuestionResponse(BaseModel):
    questions: list[str]
    keywords: list[str]


@router.post("/questions", response_model=ResumeQuestionResponse)
async def generate_resume_questions(body: ResumeQuestionRequest) -> ResumeQuestionResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    client = AsyncOpenAI(api_key=api_key)
    user_prompt = (
        f"다음 이력서를 분석해 면접 질문 {body.question_count}개를 생성하세요.\n\n"
        f"이력서:\n{body.resume_text[:3000]}"
    )

    response = await client.chat.completions.create(
        model=body.model,
        messages=[
            {"role": "system", "content": body.system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        tools=_TOOLS,
        tool_choice={"type": "function", "function": {"name": "generate_interview_questions"}},
    )

    args = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
    return ResumeQuestionResponse(
        questions=args.get("questions", []),
        keywords=args.get("keywords", []),
    )

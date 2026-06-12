# AI 면접 코치 웹앱

Streamlit 프론트엔드 + FastAPI 백엔드 구조의 AI 면접 연습 서비스입니다.

## 실행 방법

### 1. 환경 세팅
```bash
uv sync
```

### 2. API 키 설정
`.env.example`을 복사해 `.env`를 만들고 OpenAI API 키를 입력합니다.
```bash
cp .env.example .env
```
```
OPENAI_API_KEY=sk-...
```

### 3. 백엔드 실행 (FastAPI, 포트 8000)
```bash
uv run uvicorn interview_app.backend.main:app --reload --port 8000
```

### 4. 프론트엔드 실행 (Streamlit, 포트 8501)
```bash
uv run streamlit run interview_app/frontend/app.py --server.port 8501 --server.headless true
```

Swagger UI: http://localhost:8000/docs  
헬스체크: http://localhost:8000/health  
Streamlit 앱: http://localhost:8501

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| 면접 연습 | 답변 입력 시 AI 피드백·후속 질문 실시간 스트리밍 |
| 면접관 유형 | 인성·기술·임원·구조화·일반 5종 선택 |
| 에이전트 모드 | `single` 단일 코치 / `multi` 전문 면접관 handoff / `direct` 직접 OpenAI + 세션 이력 |
| 이력서 분석 | .txt 업로드 후 Function Calling으로 맞춤 질문 생성 |
| 리포트 | 면접 대화 이력 및 이력서 질문 JSON 다운로드 |

---

## 프로젝트 구조

```
interview_app/
├── backend/
│   ├── main.py               # FastAPI 진입점, CORS·예외 핸들러
│   ├── interview_router.py   # /interview/stream SSE 엔드포인트
│   ├── agents_router.py      # /agents/stream 에이전트 엔드포인트
│   ├── resume_router.py      # /resume/questions 질문 생성 엔드포인트
│   └── sessions.py           # UUID 세션 관리
├── core/
│   ├── roles.py              # 면접관 역할 프리셋
│   ├── tools.py              # Function tools
│   └── agents.py             # Agent·Handoff 정의
└── frontend/
    ├── app.py                # Streamlit 메인 진입점
    ├── api_client.py         # httpx SSE 통합 클라이언트
    ├── utils.py              # 로딩·에러·피드백·검색 유틸
    ├── report.py             # 리포트 생성·다운로드
    └── pages/
        ├── interview.py      # 면접 연습 페이지
        ├── resume.py         # 이력서 분석·질문 생성 페이지
        └── settings.py       # 모델·프롬프트 설정 페이지
```

---

## Q9-1 핵심 기능 확인표

| # | 기준 | 구현 위치 | 확인 |
|:-:|------|-----------|:----:|
| ① | Streamlit + FastAPI 동시 실행 | `frontend/app.py` + `backend/main.py` | ✅ |
| ② | SSE 기반 면접 대화 | `backend/interview_router.py` + `frontend/api_client.py` (`httpx.stream` + `placeholder.markdown()`) | ✅ |
| ③ | 멀티에이전트 / 이력서 기반 질문 | `backend/agents_router.py` (Agent·Handoff) + `frontend/pages/resume.py` (Function Calling) | ✅ |
| ④ | 멀티페이지 앱 구조 | `frontend/pages/` — interview.py·resume.py·settings.py | ✅ |
| ⑤ | UX 완성 기능 2개+ | `frontend/utils.py` — 로딩·에러·피드백(`st.feedback`)·검색 | ✅ |

---

## Day별 산출물 요약

| Day | self1 | self2 |
|:---:|-------|-------|
| 1 | `frontend/app.py` 채팅 UI 골격 | 면접관 유형 사이드바·`st.write_stream` |
| 2 | `backend/interview_router.py` SSE | `backend/sessions.py` 세션 API |
| 3 | `frontend/api_client.py` httpx 통합 | `backend/agents_router.py` 에이전트 마운트 |
| 4 | `frontend/pages/` 멀티페이지 구조 | `frontend/pages/resume.py` 이력서 질문 생성 |
| 5 | `frontend/utils.py` UX 유틸 | `frontend/report.py` 리포트 내보내기 |

---

## 보안 주의사항

- `.env` 파일은 Git에 포함되지 않습니다 (`.gitignore` 등록됨)
- API 키는 코드에 직접 쓰지 않고 `.env`에서만 관리합니다

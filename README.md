# AI 면접 코치 웹앱

8주차 CLI 면접 코치를 Streamlit 프론트엔드 + FastAPI 백엔드로 전환한 미니프로젝트입니다.

## 실행 방법

### 1. 환경 세팅
```bash
uv sync
```

### 2. API 키 설정
`.env` 파일에 OpenAI API 키를 입력합니다.
```
OPENAI_API_KEY=sk-...
```

### 3. 백엔드 실행 (FastAPI, 포트 8000)
```bash
uvicorn interview_app.backend.main:app --reload --port 8000
```

### 4. 프론트엔드 실행 (Streamlit, 포트 8501)
```bash
streamlit run interview_app/frontend/app.py --server.port 8501
```

Swagger UI: http://localhost:8000/docs  
Streamlit 앱: http://localhost:8501

---

## 프로젝트 구조

```
interview_app/
├── backend/
│   ├── main.py               # FastAPI 진입점, CORS 설정
│   ├── interview_router.py   # /interview/stream SSE 엔드포인트
│   ├── sessions.py           # UUID 세션 관리
│   └── agents_router.py      # /agents/stream 에이전트 엔드포인트
├── core/
│   ├── roles.py              # 면접관 역할 프리셋 (8주차 재사용)
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

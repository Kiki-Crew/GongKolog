# GongKolog — Backend (FastAPI)

채용공고 ↔ 자소서 의미 매칭 분석 엔진.

## 실행

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 키 채우기

uvicorn app.main:app --reload --port 8000
```

> 첫 실행 시 BGE-M3 모델(~2GB)을 다운로드한다. lifespan에서 1회만 로딩.

## 구조

```
app/
  main.py              # FastAPI 진입점, lifespan에서 BGE-M3 로딩, CORS, 라우터
  config.py            # .env 설정
  models/schemas.py    # Pydantic (요청/응답)
  services/
    llm.py             # 멀티 LLM 호출 + 폴백 (Groq/Gemini)
    embedding.py       # BGE-M3 임베딩 + 후보 검색
    prompts.py         # 추출/판정 프롬프트
    analyzer.py        # 분석 파이프라인 (추출→문장분리→임베딩→판정→조립)
  db/supabase_client.py # service_role 클라이언트
  api/
    deps.py            # JWT 인증 의존성
    routes/
      analyze.py       # POST /api/analyze
      analyses.py      # GET /api/analyses, /api/analyses/{id}
      documents.py     # 자소서/공고 CRUD (라우터 팩토리)
```

## 엔드포인트

| 메서드 | 경로 | 인증 |
|---|---|---|
| POST | `/api/analyze` | 선택 |
| GET | `/api/analyses/{id}` | 불필요 |
| GET | `/api/analyses` | 필요 |
| POST/GET/DELETE | `/api/cover-letters` | 필요 |
| POST/GET/DELETE | `/api/job-postings` | 필요 |

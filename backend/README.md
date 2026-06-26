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

## 스모크 테스트 (키 없이 파이프라인 검증)

키·모델 없이 mock 모드로 `analyze()`를 끝에서 끝까지 1회 돌리고 응답 스키마를 검증한다:

```bash
cd backend
MOCK_LLM=true MOCK_EMBEDDING=true python scripts/smoke_test.py
```

- `MOCK_LLM=true` → LLM 호출 대신 규칙 기반 추출/판정
- `MOCK_EMBEDDING=true` → BGE-M3 대신 문자 n-gram Jaccard 유사도
- 실제 LLM으로 돌리려면 `.env`에 키 채우고 `MOCK_*=false`

## 레이어 구조

요청은 `api`(라우트) → `core`(분석 엔진) / `services`(DB) 한 방향으로 흐른다.

```
app/
  main.py              # FastAPI 앱, CORS, 라우터 등록, lifespan(BGE-M3 로딩)
  config.py            # 환경변수(pydantic-settings), 모델명 상수
  api/                 # 라우터 — 엔드포인트 정의만, 로직은 core/services로 위임
    analyze.py         # POST /api/analyze, GET /api/analyses/{id}, GET /api/analyses
    cover_letters.py   # POST/GET/DELETE /api/cover-letters
    job_postings.py    # POST/GET/DELETE /api/job-postings
  schemas/
    analysis.py        # Status, AnalyzeRequest/Response, Requirement, Summary ...
  core/                # ── 분석 엔진 (스펙 4장) ──
    llm.py             # call_llm / call_with_fallback (Gemini+Groq)
    prompts.py         # EXTRACT_PROMPT, JUDGE_PROMPT
    extract.py         # 1단계: 요구사항 추출
    sentences.py       # 2단계: kss 문장 분리 + id 부여
    embedding.py       # 3단계: BGE-M3 임베딩 + 코사인 후보 검색
    judge.py           # 4단계: 판정 + build_judge_input
    pipeline.py        # 5단계: analyze() 전체 조립
    utils.py           # safe_json 등 파싱 헬퍼
  services/            # DB 접근 계층 (Supabase service_role 경유)
    supabase_client.py # supabase-py 싱글톤
    analyses.py        # 분석 결과 저장/조회
    cover_letters.py   # (내부 _documents.py 공유)
    job_postings.py
  auth/
    dependencies.py    # Supabase JWT 검증 → user_id 추출 (Depends)
```

## 엔드포인트

| 메서드 | 경로 | 인증 |
|---|---|---|
| POST | `/api/analyze` | 선택 |
| GET | `/api/analyses/{id}` | 불필요 |
| GET | `/api/analyses` | 필요 |
| POST/GET/DELETE | `/api/cover-letters` | 필요 |
| POST/GET/DELETE | `/api/job-postings` | 필요 |

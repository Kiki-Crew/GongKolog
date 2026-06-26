# GongKolog

채용 공고의 요구 역량을 추출하고, 자소서에 담긴 경험을 의미 단위로 비교-점검하여, 누락되거나 미흡한 항목을 짚어주는 AI 자소서 점검 서비스.

> 키워드 매칭이 아니라 **의미**로 읽고, 각 요구사항을 **충족(🟢) / 약함(🟡) / 공백(🔴)** 3색으로 시각화한다.

핵심 차별점: **임베딩으로 후보를 좁히고 LLM으로 충족 여부를 판정하는 2단계 구조.**

## 기술 스택

| 영역 | 스택 |
|---|---|
| Frontend | React + TypeScript + Vite + Tailwind + Axios + react-router |
| Backend | FastAPI (Python) |
| LLM | Gemini + Groq 멀티 LLM (역할 분담 + 폴백) |
| 임베딩 | BGE-M3 (로컬, sentence-transformers) |
| DB / Auth | Supabase (PostgreSQL + Google OAuth) |

## 모노레포 구조

```
.
├── backend/                # FastAPI 분석 엔진 (→ backend/README.md)
│   └── app/
│       ├── main.py         # 앱·CORS·라우터·lifespan(BGE-M3)
│       ├── config.py
│       ├── api/            # 라우트 (analyze, cover_letters, job_postings)
│       ├── schemas/        # Pydantic 계약 (analysis.py)
│       ├── core/           # 엔진: llm, prompts, extract, sentences,
│       │                   #       embedding, judge, pipeline, utils
│       ├── services/       # DB 계층: supabase_client, analyses, ...
│       └── auth/           # dependencies (JWT)
├── frontend/               # React + Vite
│   └── src/
│       ├── pages/          # Landing, Analyze, Result, MyPage, Share
│       ├── components/     # result/(SplitView 등), auth/, common/
│       ├── hooks/          # useAuth, useAnalyze
│       ├── lib/            # api, supabase
│       ├── types/          # analysis.ts
│       └── mock/           # sampleResponse.ts
└── supabase/
    ├── schema.sql          # 테이블
    ├── policies.sql        # RLS 정책
    └── triggers.sql        # 가입 시 profiles 자동 생성
```

## 데이터 흐름

```
공고 ──[LLM 추출]──> 요구사항 리스트
자소서 ─[문장분리]──> 문장 리스트
              [BGE-M3 임베딩 + 코사인유사도] → 요구사항별 후보 추림
              [LLM 판정] 충족/약함/공백 + 근거 + 제안
              [조립] → 응답 JSON → Supabase 저장
```

## 로컬 실행

```bash
# 1) DB: supabase/schema.sql 을 Supabase SQL Editor에서 실행
# 2) 백엔드
cd backend && cp .env.example .env   # 키 채우기
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# 3) 프론트
cd frontend && cp .env.example .env  # 키 채우기
npm install && npm run dev
```

## 보안

- `.env`는 커밋 금지(`.env.example`만). API 키·service_role 키 절대 노출 금지.
- 프론트엔 anon 키만, 백엔드에만 service_role 키.
- 자소서는 개인정보 → RLS 필수.

# GongKolog 셋업 가이드

분석→결과까지는 키만 있으면 되고, 저장·공유·마이페이지는 Supabase + Google OAuth가 필요하다.

---

## 1. Supabase 테이블 생성 (스키마)

Supabase 대시보드 → **SQL Editor** → 아래 순서로 각각 붙여넣고 Run:

1. `supabase/schema.sql` — 테이블 4개 (profiles, cover_letters, job_postings, analyses)
2. `supabase/policies.sql` — RLS 정책
3. `supabase/triggers.sql` — 가입 시 profiles 자동 생성

확인: **Table Editor**에 4개 테이블이 보이면 성공.

> 이미 v1 `cover_letters(content)`로 만들었다면 먼저 `drop table if exists cover_letters cascade;` 실행 후 schema.sql 재실행.

---

## 2. 키 채우기 (.env)

Supabase → **Project Settings → API** 에서 값 복사.

### backend/.env
```
GROQ_API_KEY=...

GROQ_EXTRACT_PRIMARY_MODEL=llama-3.3-70b-versatile
GROQ_EXTRACT_BACKUP_MODEL=openai/gpt-oss-120b

GROQ_JUDGE_PRIMARY_MODEL=openai/gpt-oss-120b
GROQ_JUDGE_BACKUP_MODEL=llama-3.3-70b-versatile

GROQ_JOB_CONTEXT_PRIMARY_MODEL=qwen/qwen3-32b
GROQ_JOB_CONTEXT_BACKUP_MODEL=llama-3.3-70b-versatile

SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...      # service_role (secret, 절대 노출 금지)
SUPABASE_JWT_SECRET=...            # Settings > API > JWT Settings 의 JWT Secret

MOCK_LLM=false
MOCK_EMBEDDING=false
FRONTEND_ORIGIN=http://localhost:5173
```

### frontend/.env
```
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=...         # anon public 키
```

> `.env`는 절대 커밋 금지(.gitignore 등록됨). 키는 .env에만.

---

## 3. Google OAuth (로그인 — 저장·마이페이지·공유 전제)

세 곳을 연결해야 한다: Google Cloud ↔ Supabase ↔ 프론트.

### 3-1. Google Cloud Console
1. https://console.cloud.google.com → APIs & Services → **Credentials**
2. **Create Credentials → OAuth client ID → Web application**
3. **Authorized redirect URIs** 에 Supabase 콜백 추가:
   ```
   https://xxxx.supabase.co/auth/v1/callback
   ```
   (xxxx = 본인 프로젝트. Supabase Auth > Providers > Google 화면에 정확한 값이 표시됨)
4. 생성된 **Client ID / Client Secret** 복사

### 3-2. Supabase
1. Authentication → **Providers → Google** → Enable
2. 위 Client ID / Secret 붙여넣고 저장
3. Authentication → **URL Configuration → Redirect URLs** 에 추가:
   ```
   http://localhost:5173
   ```
   (배포 시 배포 주소도 추가)

### 3-3. 프론트
별도 작업 없음. `signInWithGoogle()`이 `redirectTo: window.location.origin`로 동작.

---

## 4. LLM 사용량/한도 처리

Groq API는 조직/API 키/모델/서비스 티어 기준으로 토큰 한도가 적용됨.
organization 한도에 걸린 상태에서 백업 모델을 계속 호출하면 실패 로그와 불필요한 요청만 늘어날 수 있고,
분석 중 일일 토큰 한도(TPD/RPD)에 도달하면 백업 모델로 넘기지 않고 분석을 중단함. 

사용자 화면에는 공급자명, HTTP 상태 코드, 원본 API 오류를 노출하지 않습니다. 일일 토큰 한도 초과 시에는 아래 문구만 표시하도록 작성함.

```text
하루에 사용 가능한 토큰 개수를 모두 소진했습니다.
```

그리고 상세 원인은 서버 로그에서 확인하도록 했음.

```text
[LLM 일일 한도 초과] wait_seconds=... header_wait_seconds=... rate_limit_headers=... error=...
[ANALYZE ERROR] status=429 error=...
```

성공한 LLM 호출은 서버 로그에 `[LLM 사용량] ... total_tokens=...` 형태로 기록됩니다. 이 값은 해당 호출에서 사용한 토큰 수이며, 남은 일일 토큰 수를 정확히 계산하는 값은 아닙니다. 남은 한도는 Groq 서버가 조직/모델/시간창/동시 요청 기준으로 판단하므로, 한도 초과 시 서버 로그의 `error=` 원본 오류 메시지나 `rate_limit_headers=`에 값이 제공될 때만 참고값으로 확인합니다.

---

## 5. 실행

```bash
# 백엔드
cd backend && python -m uvicorn app.main:app --port 8000
# 프론트 (다른 터미널)
cd frontend && npm run dev      # http://localhost:5173
```

---

## 6. 검증 순서

1. **비로그인 분석**: `/analyze` → 진단 → 결과 화면. (저장 안 됨 = 새로고침하면 사라짐. 정상)
2. **로그인**: 마이페이지 → Google 로그인 → 돌아오면 세션 유지.
3. **로그인 분석 + 저장**: 로그인 상태로 분석 → Supabase **Table Editor → analyses** 에 row(`user_id` 채워짐) 확인.
4. **마이페이지 기록**: `/mypage` 에 방금 분석이 목록으로.
5. **공유**: 결과 id로 `/share/:id` 열림.

---

## 동작 정책 (B안)
- 비로그인 분석은 **저장하지 않음** (분석 후 즉시 폐기 — 개인정보 보호).
- 저장·공유·마이페이지는 **로그인 사용자만**.

## 자주 막히는 곳
- **흰 화면** → 브라우저 콘솔(F12) 에러. 보통 `.env` 미설정 후 Vite 재시작 안 함.
- **분석 404** → `VITE_API_BASE_URL` 미설정 → Vite 재시작.
- **로그인 후 안 돌아옴** → Supabase Redirect URLs 에 `http://localhost:5173` 누락.
- **로그인 분석인데 저장 안 됨** → backend `.env`의 `SUPABASE_JWT_SECRET` 불일치 (토큰 검증 실패로 user_id 추출 안 됨).
- **.env 바꾸면 백엔드/프론트 둘 다 재시작** (env는 시작 시 1회 로딩).

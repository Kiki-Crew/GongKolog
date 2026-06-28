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
GEMINI_API_KEY=...
GROQ_API_KEY=...
GROQ_MODEL=qwen/qwen3-32b

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

## 4. 실행

```bash
# 백엔드
cd backend && python -m uvicorn app.main:app --port 8000
# 프론트 (다른 터미널)
cd frontend && npm run dev      # http://localhost:5173
```

---

## 5. 검증 순서

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

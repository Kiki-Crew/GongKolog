-- =====================================================================
-- GongKolog — 테이블 스키마 (스펙 5.1)
-- 실행 순서: schema.sql → policies.sql → triggers.sql
-- =====================================================================

-- ── 사용자 (Supabase Auth 연결) ────────────────────────────────────
create table if not exists profiles (
  id uuid primary key references auth.users on delete cascade,
  email text,
  created_at timestamptz default now()
);

-- ── 저장된 자소서 ──────────────────────────────────────────────────
create table if not exists cover_letters (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  title text,
  content text,
  created_at timestamptz default now()
);

-- ── 저장된 공고 ────────────────────────────────────────────────────
create table if not exists job_postings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  title text,
  content text,
  created_at timestamptz default now()
);

-- ── 분석 결과 ──────────────────────────────────────────────────────
create table if not exists analyses (
  id uuid primary key default gen_random_uuid(),  -- = 응답의 analysis_id
  user_id uuid references profiles(id) on delete cascade,  -- 비로그인 분석은 null 허용
  cover_letter_id uuid references cover_letters(id) on delete set null,
  job_posting_id uuid references job_postings(id) on delete set null,
  result_json jsonb,                              -- 응답 JSON 통째 저장
  created_at timestamptz default now()
);
-- 결과는 정규화하지 말고 result_json jsonb 한 칸에 통째로 저장.

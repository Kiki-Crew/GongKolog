-- =====================================================================
-- GongKolog — Supabase / PostgreSQL 스키마
-- 스펙 5장 기준. Supabase SQL Editor에 붙여넣어 실행.
-- =====================================================================

-- ── 1. 사용자 (Supabase Auth 연결) ──────────────────────────────────
create table if not exists profiles (
  id uuid primary key references auth.users on delete cascade,
  email text,
  created_at timestamptz default now()
);

-- ── 2. 저장된 자소서 ────────────────────────────────────────────────
create table if not exists cover_letters (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  title text,
  content text,
  created_at timestamptz default now()
);

-- ── 3. 저장된 공고 ──────────────────────────────────────────────────
create table if not exists job_postings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  title text,
  content text,
  created_at timestamptz default now()
);

-- ── 4. 분석 결과 ────────────────────────────────────────────────────
create table if not exists analyses (
  id uuid primary key default gen_random_uuid(),  -- = 응답의 analysis_id
  user_id uuid references profiles(id) on delete cascade,  -- 비로그인 분석은 null 허용
  cover_letter_id uuid references cover_letters(id) on delete set null,
  job_posting_id uuid references job_postings(id) on delete set null,
  result_json jsonb,                              -- 응답 JSON 통째 저장
  created_at timestamptz default now()
);

-- =====================================================================
-- RLS (Row Level Security) — 필수
-- 본 프로젝트는 FastAPI 경유 + service_role 키 방식(택1-B).
-- service_role 키는 RLS를 우회하므로, 실제 user_id 체크는 백엔드 코드에서 수행.
-- 아래 정책은 anon 키로 직접 접근하는 경로가 생길 경우의 안전장치.
-- =====================================================================
alter table cover_letters enable row level security;
alter table job_postings  enable row level security;
alter table analyses      enable row level security;

create policy "본인 자소서만" on cover_letters
  for all using (auth.uid() = user_id);

create policy "본인 공고만" on job_postings
  for all using (auth.uid() = user_id);

-- 분석: 본인 것 또는 공개 열람(공유 링크)은 백엔드가 service_role로 처리.
create policy "본인 분석만" on analyses
  for all using (auth.uid() = user_id);

-- =====================================================================
-- auth.users 가입 시 profiles row 자동 생성 트리거
-- =====================================================================
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email)
  on conflict (id) do nothing;
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

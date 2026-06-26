-- =====================================================================
-- GongKolog — RLS 정책 (스펙 5.2)
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

-- 분석: 본인 것만. 공개 열람(공유 링크)은 백엔드가 service_role로 처리.
create policy "본인 분석만" on analyses
  for all using (auth.uid() = user_id);

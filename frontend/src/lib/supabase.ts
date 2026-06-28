// Supabase 클라이언트 (anon 키 — 스펙 5.3 / 7.5)
// 환경변수가 없으면 null. (Supabase 미설정 상태에서도 앱이 뜨고 분석은 동작해야 함)
import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL;
const key = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase: SupabaseClient | null =
  url && key ? createClient(url, key) : null;

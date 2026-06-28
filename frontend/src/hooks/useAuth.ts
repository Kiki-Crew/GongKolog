// Supabase 세션 관리 훅 + Google OAuth (스펙 7.5)
// Supabase 미설정(supabase=null)이면 항상 비로그인 상태로 동작.
import { useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";

import { supabase } from "../lib/supabase";

export function useAuth() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });
    const { data: sub } = supabase.auth.onAuthStateChange((_e, s) => {
      setSession(s);
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  return { session, loading };
}

export function signInWithGoogle() {
  if (!supabase) {
    alert("로그인은 Supabase 설정 후 사용할 수 있습니다.");
    return;
  }
  return supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: window.location.origin },
  });
}

export function signOut() {
  return supabase?.auth.signOut();
}

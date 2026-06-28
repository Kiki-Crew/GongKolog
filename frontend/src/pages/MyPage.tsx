// 마이페이지 — 저장한 자소서/공고, 분석 기록 (스펙 1.4 / 7.2 "/mypage")
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import GoogleLoginButton from "../components/auth/GoogleLoginButton";
import Spinner from "../components/common/Spinner";
import { useAuth, signOut } from "../hooks/useAuth";
import { listAnalyses } from "../lib/api";
import type { AnalysisHistoryItem } from "../types/analysis";

export default function MyPage() {
  const { session, loading } = useAuth();
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);

  useEffect(() => {
    if (session) listAnalyses().then(setHistory).catch(() => setHistory([]));
  }, [session]);

  if (loading) return <Spinner />;

  if (!session) {
    return (
      <div className="flex flex-col items-center gap-4 py-20">
        <p>로그인하면 자소서·공고 저장과 분석 기록을 볼 수 있습니다.</p>
        <GoogleLoginButton />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-brand-accent">마이페이지</h1>
        <button onClick={() => signOut()} className="text-sm text-muted">
          로그아웃
        </button>
      </div>

      {/* 분석 기록 */}
      <section>
        <h2 className="mb-2 font-semibold">내 분석 기록</h2>
        <ul className="flex flex-col gap-2">
          {history.map((h) => (
            <li key={h.id}>
              <Link
                to={`/result/${h.id}`}
                className="block rounded-lg bg-surface p-3 ring-1 ring-border hover:bg-brand/10"
              >
                {h.created_at?.slice(0, 10)} — 문항 {h.overall_summary?.total_items}개 /
                카테고리 {h.overall_summary?.total_categories}개 중{" "}
                {h.overall_summary?.met}개 충족
              </Link>
            </li>
          ))}
          {history.length === 0 && (
            <p className="text-muted">아직 분석 기록이 없습니다.</p>
          )}
        </ul>
      </section>

      {/* TODO: 저장한 자소서/공고 목록 + 저장/삭제 (스펙 1.4) */}
    </div>
  );
}

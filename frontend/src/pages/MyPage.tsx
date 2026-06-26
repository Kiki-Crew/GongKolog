// 마이페이지 — 저장한 자소서/공고, 분석 기록 (스펙 1.4 / 7.2 "/mypage")
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listAnalyses } from "../lib/api";
import { signInWithGoogle, signOut, useAuth } from "../lib/useAuth";
import type { AnalysisHistoryItem } from "../types";

export default function MyPage() {
  const { session, loading } = useAuth();
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);

  useEffect(() => {
    if (session) listAnalyses().then(setHistory).catch(() => setHistory([]));
  }, [session]);

  if (loading) return <p className="text-gray-400">불러오는 중...</p>;

  if (!session) {
    return (
      <div className="flex flex-col items-center gap-4 py-20">
        <p>로그인하면 자소서·공고 저장과 분석 기록을 볼 수 있습니다.</p>
        <button
          onClick={() => signInWithGoogle()}
          className="rounded-lg bg-nano-primary px-6 py-3 font-semibold hover:bg-nano-accent"
        >
          Google로 로그인
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-nano-accent">마이페이지</h1>
        <button onClick={() => signOut()} className="text-sm text-gray-400">
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
                className="block rounded-lg bg-black/30 p-3 hover:bg-black/50"
              >
                {h.created_at?.slice(0, 10)} — 총 {h.summary?.total}개 중{" "}
                {h.summary?.met}개 충족
              </Link>
            </li>
          ))}
          {history.length === 0 && (
            <p className="text-gray-400">아직 분석 기록이 없습니다.</p>
          )}
        </ul>
      </section>

      {/* TODO: 저장한 자소서/공고 목록 + 저장/삭제 (스펙 1.4) */}
    </div>
  );
}

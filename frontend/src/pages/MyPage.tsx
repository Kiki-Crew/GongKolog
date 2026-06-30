// 마이페이지 — 저장한 자소서/공고, 분석 기록 (스펙 1.4 / 7.2 "/mypage")
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import GoogleLoginButton from "../components/auth/GoogleLoginButton";
import Logo from "../components/common/Logo";
import Spinner from "../components/common/Spinner";
import { useAuth, signOut } from "../hooks/useAuth";
import {
  deleteAccount,
  deleteCoverLetter,
  deleteJobPosting,
  listAnalyses,
  listCoverLetters,
  listJobPostings,
  updateCoverLetter,
  updateJobPosting,
} from "../lib/api";
import type {
  AnalysisHistoryItem,
  SavedCoverLetter,
  SavedJobPosting,
} from "../types/analysis";

function Count({ color, n }: { color: string; n?: number }) {
  return (
    <span className="flex items-center gap-1 tabular-nums">
      <span className={`inline-block h-2 w-2 rounded-full ${color}`} />
      {n ?? 0}
    </span>
  );
}

export default function MyPage() {
  const { session, loading } = useAuth();
  const navigate = useNavigate();
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
  const [jobs, setJobs] = useState<SavedJobPosting[]>([]);
  const [letters, setLetters] = useState<SavedCoverLetter[]>([]);

  useEffect(() => {
    if (!session) return;
    listAnalyses().then(setHistory).catch(() => setHistory([]));
    listJobPostings().then(setJobs).catch(() => setJobs([]));
    listCoverLetters().then(setLetters).catch(() => setLetters([]));
  }, [session]);

  async function removeJob(id: string) {
    await deleteJobPosting(id);
    setJobs((prev) => prev.filter((d) => d.id !== id));
  }
  async function removeLetter(id: string) {
    await deleteCoverLetter(id);
    setLetters((prev) => prev.filter((d) => d.id !== id));
  }
  async function renameJob(d: SavedJobPosting) {
    const title = window.prompt("새 이름", d.title)?.trim();
    if (!title || title === d.title) return;
    try {
      await updateJobPosting(d.id, { title });
      setJobs((prev) => prev.map((x) => (x.id === d.id ? { ...x, title } : x)));
    } catch {
      alert("같은 이름이 이미 있거나 수정에 실패했습니다.");
    }
  }
  async function renameLetter(d: SavedCoverLetter) {
    const title = window.prompt("새 이름", d.title)?.trim();
    if (!title || title === d.title) return;
    try {
      await updateCoverLetter(d.id, { title });
      setLetters((prev) => prev.map((x) => (x.id === d.id ? { ...x, title } : x)));
    } catch {
      alert("같은 이름이 이미 있거나 수정에 실패했습니다.");
    }
  }
  async function onDeleteAccount() {
    if (!window.confirm("정말 탈퇴하시겠어요? 저장된 자소서·공고·분석 기록이 모두 삭제됩니다.")) {
      return;
    }
    try {
      await deleteAccount();
      await signOut();
      navigate("/");
    } catch {
      alert("회원 탈퇴에 실패했습니다.");
    }
  }

  if (loading) return <Spinner />;

  if (!session) {
    return (
      <div className="flex flex-col items-center gap-4 py-20">
        <Logo size={88} />
        <p>로그인하면 자소서·공고 저장과 분석 기록을 볼 수 있습니다.</p>
        <GoogleLoginButton />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      {/* 헤더 */}
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-brand-accent">마이페이지</h1>
          {session.user?.email && (
            <p className="mt-1 text-sm text-muted">{session.user.email}</p>
          )}
        </div>
        <div className="flex items-center gap-3 text-sm">
          <Link to="/analyze" className="text-brand-accent hover:underline">
            새 진단
          </Link>
          <button onClick={() => signOut()} className="text-muted hover:text-fg">
            로그아웃
          </button>
        </div>
      </div>

      {/* 분석 기록 */}
      <section>
        <h2 className="mb-2 font-semibold">내 분석 기록 ({history.length})</h2>
        <ul className="flex flex-col gap-2">
          {history.map((h) => (
            <li key={h.id}>
              <Link
                to={`/result/${h.id}`}
                className="flex items-center justify-between gap-3 rounded-lg bg-surface p-3 ring-1 ring-border hover:bg-brand/10"
              >
                <span className="text-sm">
                  {h.created_at?.slice(0, 10)}
                  <span className="ml-2 text-muted">
                    문항 {h.overall_summary?.total_items}개 · 카테고리{" "}
                    {h.overall_summary?.total_categories}개
                  </span>
                </span>
                <span className="flex shrink-0 gap-3 text-sm">
                  <Count color="bg-met" n={h.overall_summary?.met} />
                  <Count color="bg-weak" n={h.overall_summary?.weak} />
                  <Count color="bg-missing" n={h.overall_summary?.missing} />
                </span>
              </Link>
            </li>
          ))}
          {history.length === 0 && (
            <p className="text-muted">아직 분석 기록이 없습니다.</p>
          )}
        </ul>
      </section>

      {/* 저장한 공고 / 자소서 (2단) */}
      <div className="grid gap-6 md:grid-cols-2">
        <section>
          <h2 className="mb-2 font-semibold">내 공고 ({jobs.length})</h2>
          <ul className="flex flex-col gap-2">
            {jobs.map((d) => (
              <li
                key={d.id}
                className="flex items-center justify-between gap-2 rounded-lg bg-surface p-3 ring-1 ring-border"
              >
                <span className="truncate">{d.title}</span>
                <span className="flex shrink-0 gap-3 text-sm text-muted">
                  <button onClick={() => renameJob(d)} className="hover:text-fg">
                    이름 수정
                  </button>
                  <button onClick={() => removeJob(d.id)} className="hover:text-missing">
                    삭제
                  </button>
                </span>
              </li>
            ))}
            {jobs.length === 0 && (
              <p className="text-sm text-muted">저장한 공고가 없습니다. 분석 화면에서 저장할 수 있어요.</p>
            )}
          </ul>
        </section>

        <section>
          <h2 className="mb-2 font-semibold">내 자소서 ({letters.length})</h2>
          <ul className="flex flex-col gap-2">
            {letters.map((d) => (
              <li
                key={d.id}
                className="flex items-center justify-between gap-2 rounded-lg bg-surface p-3 ring-1 ring-border"
              >
                <span className="truncate">
                  {d.title}{" "}
                  <span className="text-sm text-muted">({d.items?.length ?? 0}문항)</span>
                </span>
                <span className="flex shrink-0 gap-3 text-sm text-muted">
                  <button onClick={() => renameLetter(d)} className="hover:text-fg">
                    이름 수정
                  </button>
                  <button onClick={() => removeLetter(d.id)} className="hover:text-missing">
                    삭제
                  </button>
                </span>
              </li>
            ))}
            {letters.length === 0 && (
              <p className="text-sm text-muted">저장한 자소서가 없습니다. 분석 화면에서 저장할 수 있어요.</p>
            )}
          </ul>
        </section>
      </div>

      {/* 회원 탈퇴 */}
      <section className="mt-2 rounded-lg border border-border p-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium">회원 탈퇴</p>
            <p className="text-sm text-muted">저장된 모든 데이터가 영구 삭제됩니다.</p>
          </div>
          <button
            onClick={onDeleteAccount}
            className="shrink-0 rounded-lg border border-missing/50 px-3 py-1.5 text-sm text-missing hover:bg-missing/10"
          >
            탈퇴하기
          </button>
        </div>
      </section>
    </div>
  );
}

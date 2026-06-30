// 마이페이지 — 저장한 자소서/공고, 분석 기록 (스펙 1.4 / 7.2 "/mypage")
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import GoogleLoginButton from "../components/auth/GoogleLoginButton";
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

      {/* 저장한 공고 */}
      <section>
        <h2 className="mb-2 font-semibold">내 공고</h2>
        <ul className="flex flex-col gap-2">
          {jobs.map((d) => (
            <li
              key={d.id}
              className="flex items-center justify-between rounded-lg bg-surface p-3 ring-1 ring-border"
            >
              <span>{d.title}</span>
              <span className="flex gap-3 text-sm text-muted">
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
            <p className="text-muted">저장한 공고가 없습니다. 분석 화면에서 저장할 수 있어요.</p>
          )}
        </ul>
      </section>

      {/* 저장한 자소서 */}
      <section>
        <h2 className="mb-2 font-semibold">내 자소서</h2>
        <ul className="flex flex-col gap-2">
          {letters.map((d) => (
            <li
              key={d.id}
              className="flex items-center justify-between rounded-lg bg-surface p-3 ring-1 ring-border"
            >
              <span>
                {d.title}{" "}
                <span className="text-sm text-muted">({d.items?.length ?? 0}문항)</span>
              </span>
              <span className="flex gap-3 text-sm text-muted">
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
            <p className="text-muted">저장한 자소서가 없습니다. 분석 화면에서 저장할 수 있어요.</p>
          )}
        </ul>
      </section>

      {/* 회원 탈퇴 */}
      <section className="mt-4 border-t border-border pt-6">
        <button
          onClick={onDeleteAccount}
          className="text-sm text-muted hover:text-missing"
        >
          회원 탈퇴
        </button>
      </section>
    </div>
  );
}

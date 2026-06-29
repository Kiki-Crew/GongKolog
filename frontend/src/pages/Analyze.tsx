// 입력·분석 (스펙 v2 5장) — 공고(필수) + 문항 반복(최대 5)
// 로그인 사용자는 저장한 공고/자소서를 불러오거나 새로 저장할 수 있다 (Tier 3).
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import Button from "../components/common/Button";
import { useAnalyze } from "../hooks/useAnalyze";
import { useAuth } from "../hooks/useAuth";
import {
  createCoverLetter,
  createJobPosting,
  listCoverLetters,
  listJobPostings,
} from "../lib/api";
import type {
  AnalyzeItemInput,
  SavedCoverLetter,
  SavedJobPosting,
} from "../types/analysis";

const MAX_ITEMS = 5;
const EMPTY: AnalyzeItemInput = { question: "", answer: "" };

export default function Analyze() {
  const { session } = useAuth();
  const [jobPosting, setJobPosting] = useState("");
  const [items, setItems] = useState<AnalyzeItemInput[]>([{ ...EMPTY }]);
  const { run, loading, error } = useAnalyze();
  const navigate = useNavigate();

  // 저장된 공고/자소서 (로그인 시)
  const [savedJobs, setSavedJobs] = useState<SavedJobPosting[]>([]);
  const [savedLetters, setSavedLetters] = useState<SavedCoverLetter[]>([]);

  function reloadSaved() {
    if (!session) return;
    listJobPostings().then(setSavedJobs).catch(() => setSavedJobs([]));
    listCoverLetters().then(setSavedLetters).catch(() => setSavedLetters([]));
  }
  useEffect(reloadSaved, [session]);

  function update(i: number, field: keyof AnalyzeItemInput, value: string) {
    setItems((prev) => prev.map((it, idx) => (idx === i ? { ...it, [field]: value } : it)));
  }
  function addItem() {
    setItems((prev) => (prev.length < MAX_ITEMS ? [...prev, { ...EMPTY }] : prev));
  }
  function removeItem(i: number) {
    setItems((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function saveJob() {
    if (!jobPosting.trim()) return alert("저장할 공고 내용이 비어 있습니다.");
    const title = window.prompt("공고 제목", "내 공고");
    if (!title) return;
    try {
      await createJobPosting(title, jobPosting);
      reloadSaved();
      alert("공고를 저장했습니다.");
    } catch {
      alert("저장 실패");
    }
  }

  async function saveLetter() {
    const valid = items.filter((it) => it.question.trim() && it.answer.trim());
    if (!valid.length) return alert("저장할 문항이 비어 있습니다.");
    const title = window.prompt("자소서 제목", "내 자소서");
    if (!title) return;
    try {
      await createCoverLetter(title, valid);
      reloadSaved();
      alert("자소서를 저장했습니다.");
    } catch {
      alert("저장 실패");
    }
  }

  async function onSubmit() {
    const result = await run(jobPosting, items);
    if (result) {
      navigate(`/result/${result.analysis_id}`, { state: result });
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <h1 className="text-2xl font-bold text-brand-accent">자소서 진단</h1>

      {/* 공고 (공통, 필수) */}
      <section className="flex flex-col gap-2">
        <div className="flex items-center justify-between gap-2">
          <label className="font-semibold">
            채용공고 <span className="text-missing">*</span>
          </label>
          {session && (
            <div className="flex items-center gap-2 text-sm">
              <select
                className="rounded-lg border border-border bg-surface p-1"
                value=""
                onChange={(e) => {
                  const doc = savedJobs.find((d) => d.id === e.target.value);
                  if (doc) setJobPosting(doc.content);
                }}
              >
                <option value="">📁 저장한 공고 불러오기</option>
                {savedJobs.map((d) => (
                  <option key={d.id} value={d.id}>{d.title}</option>
                ))}
              </select>
              <button onClick={saveJob} className="text-brand-accent hover:underline">
                💾 저장
              </button>
            </div>
          )}
        </div>
        <p className="text-sm text-muted">모든 문항에 공통 적용됩니다 (회사 인재상 반영).</p>
        <textarea
          className="h-40 rounded-lg bg-surface p-3 ring-1 ring-border"
          placeholder="채용공고 원문을 붙여넣으세요"
          value={jobPosting}
          onChange={(e) => setJobPosting(e.target.value)}
        />
      </section>

      {/* 문항 반복 */}
      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between gap-2">
          <label className="font-semibold">자소서 문항 ({items.length}/{MAX_ITEMS})</label>
          {session && (
            <div className="flex items-center gap-2 text-sm">
              <select
                className="rounded-lg border border-border bg-surface p-1"
                value=""
                onChange={(e) => {
                  const doc = savedLetters.find((d) => d.id === e.target.value);
                  if (doc && doc.items?.length) setItems(doc.items.map((x) => ({ ...x })));
                }}
              >
                <option value="">📁 저장한 자소서 불러오기</option>
                {savedLetters.map((d) => (
                  <option key={d.id} value={d.id}>{d.title}</option>
                ))}
              </select>
              <button onClick={saveLetter} className="text-brand-accent hover:underline">
                💾 저장
              </button>
            </div>
          )}
        </div>
        {items.map((it, i) => (
          <div key={i} className="flex flex-col gap-2 rounded-lg border border-border p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-brand-accent">문항 {i + 1}</span>
              {items.length > 1 && (
                <button onClick={() => removeItem(i)} className="text-sm text-muted hover:text-missing">
                  삭제
                </button>
              )}
            </div>
            <input
              className="rounded-lg bg-surface p-2 ring-1 ring-border"
              placeholder="질문 (예: 협업에서 중요한 요소와 사례는?)"
              value={it.question}
              onChange={(e) => update(i, "question", e.target.value)}
            />
            <textarea
              className="h-28 rounded-lg bg-surface p-2 ring-1 ring-border"
              placeholder="답변"
              value={it.answer}
              onChange={(e) => update(i, "answer", e.target.value)}
            />
          </div>
        ))}
        {items.length < MAX_ITEMS && (
          <button
            onClick={addItem}
            className="self-start rounded-lg border border-border px-4 py-2 text-sm hover:bg-brand/10"
          >
            + 문항 추가
          </button>
        )}
      </section>

      {error && <p className="text-missing">{error}</p>}
      <Button onClick={onSubmit} disabled={loading} className="self-start">
        {loading ? "분석 중..." : "진단하기"}
      </Button>
      {!session && (
        <p className="text-sm text-muted">
          로그인하면 공고·자소서를 저장해두고 다음에 불러올 수 있어요.
        </p>
      )}
    </div>
  );
}

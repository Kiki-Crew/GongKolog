// 입력·분석 (스펙 v2 5장) — 공고(필수) + 문항 반복(최대 5)
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import Button from "../components/common/Button";
import { useAnalyze } from "../hooks/useAnalyze";
import type { AnalyzeItemInput } from "../types/analysis";

const MAX_ITEMS = 5;
const EMPTY: AnalyzeItemInput = { question: "", answer: "" };

export default function Analyze() {
  const [jobPosting, setJobPosting] = useState("");
  const [items, setItems] = useState<AnalyzeItemInput[]>([{ ...EMPTY }]);
  const { run, loading, error } = useAnalyze();
  const navigate = useNavigate();

  function update(i: number, field: keyof AnalyzeItemInput, value: string) {
    setItems((prev) => prev.map((it, idx) => (idx === i ? { ...it, [field]: value } : it)));
  }
  function addItem() {
    setItems((prev) => (prev.length < MAX_ITEMS ? [...prev, { ...EMPTY }] : prev));
  }
  function removeItem(i: number) {
    setItems((prev) => prev.filter((_, idx) => idx !== i));
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
        <label className="font-semibold">채용공고 <span className="text-missing">*</span></label>
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
        <label className="font-semibold">자소서 문항 ({items.length}/{MAX_ITEMS})</label>
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
      {/* TODO: 로그인 시 저장된 자소서/공고 불러오기 (스펙 1.4) */}
    </div>
  );
}

// 결과 split view (스펙 7.3) — 좌: 자소서 / 우: 요구사항 리스트
// 요구사항 클릭 → evidence_ids 문장 하이라이트.
import { useState } from "react";

import type { AnalyzeResponse, Status } from "../types";

const STATUS_STYLE: Record<Status, { dot: string; label: string; ring: string }> = {
  met: { dot: "🟢", label: "충족", ring: "border-met" },
  weak: { dot: "🟡", label: "약함", ring: "border-weak" },
  missing: { dot: "🔴", label: "공백", ring: "border-missing" },
};

export default function SplitView({ result }: { result: AnalyzeResponse }) {
  const [activeReq, setActiveReq] = useState<string | null>(null);

  const highlighted = new Set(
    activeReq
      ? result.requirements.find((r) => r.id === activeReq)?.evidence_ids ?? []
      : [],
  );

  const { summary } = result;

  return (
    <div className="flex flex-col gap-4">
      {/* 헤드라인 요약 */}
      <div className="rounded-lg bg-nano-primary/20 p-4 text-lg">
        총 {summary.total}개 중 <b className="text-met">{summary.met}개 충족</b>,{" "}
        <b className="text-weak">{summary.weak}개 약함</b>,{" "}
        <b className="text-missing">{summary.missing}개 공백</b>
        {summary.coverage_score != null && (
          <span className="ml-2 text-gray-400">
            (커버리지 {Math.round(summary.coverage_score * 100)}%)
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {/* 좌: 자소서 */}
        <div className="rounded-lg bg-black/30 p-4">
          <h2 className="mb-2 font-bold text-nano-accent">자소서</h2>
          <p className="leading-relaxed">
            {result.cover_letter_sentences.map((s) => (
              <span
                key={s.id}
                className={
                  highlighted.has(s.id)
                    ? "rounded bg-nano-accent/40 px-0.5"
                    : ""
                }
              >
                {s.text}{" "}
              </span>
            ))}
          </p>
        </div>

        {/* 우: 요구사항 리스트 */}
        <div className="flex flex-col gap-2">
          <h2 className="font-bold text-nano-accent">요구사항</h2>
          {result.requirements.map((r) => {
            const st = STATUS_STYLE[r.status];
            return (
              <button
                key={r.id}
                onClick={() => setActiveReq(r.id === activeReq ? null : r.id)}
                className={`rounded-lg border-l-4 ${st.ring} bg-black/30 p-3 text-left transition ${
                  r.id === activeReq ? "ring-2 ring-nano-accent" : ""
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold">
                    {st.dot} {r.text}
                  </span>
                  {r.category && (
                    <span className="text-xs text-gray-400">{r.category}</span>
                  )}
                </div>
                <p className="mt-1 text-sm text-gray-300">{r.comment}</p>
                {r.suggestion && (
                  <p className="mt-1 text-sm text-weak">💡 {r.suggestion}</p>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

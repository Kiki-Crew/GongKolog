// 상단 요약 헤드라인 — "8개 중 5개 충족" (스펙 7.3)
import type { Summary } from "../../types/analysis";

export default function SummaryHeader({ summary }: { summary: Summary }) {
  return (
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
  );
}

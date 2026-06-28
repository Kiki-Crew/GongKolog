// 상단 전체 요약 헤드라인 (스펙 v2)
import type { OverallSummary } from "../../types/analysis";

export default function OverallHeader({ summary }: { summary: OverallSummary }) {
  return (
    <div className="rounded-lg bg-nano-primary/20 p-4 text-lg">
      문항 {summary.total_items}개 · 카테고리 {summary.total_categories}개 중{" "}
      <b className="text-met">{summary.met} 충족</b>,{" "}
      <b className="text-weak">{summary.weak} 약함</b>,{" "}
      <b className="text-missing">{summary.missing} 공백</b>
      {summary.coverage_score != null && (
        <span className="ml-2 text-gray-400">
          (커버리지 {Math.round(summary.coverage_score * 100)}%)
        </span>
      )}
    </div>
  );
}

// 결과 전체 뷰 — 상단 요약 + (공유 버튼) + 문항별 패널 (스펙 v2)
import ItemPanel from "./ItemPanel";
import OverallHeader from "./OverallHeader";
import ShareButton from "./ShareButton";
import type { AnalyzeResponse } from "../../types/analysis";

export default function ResultView({
  result,
  showShare = false,
}: {
  result: AnalyzeResponse;
  showShare?: boolean;
}) {
  return (
    <div className="flex flex-col gap-4">
      <OverallHeader summary={result.overall_summary} />
      {showShare && (
        <div className="flex justify-end">
          <ShareButton id={result.analysis_id} />
        </div>
      )}
      <div className="flex flex-col gap-3">
        {result.items.map((it, i) => (
          <ItemPanel key={it.item_id} item={it} defaultOpen={i === 0} />
        ))}
      </div>
    </div>
  );
}

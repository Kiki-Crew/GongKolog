// 좌우 split (데모의 얼굴 — 스펙 7.3)
// 요구사항 선택 → evidence_ids 문장 하이라이트.
import { useState } from "react";

import CoverLetterPane from "./CoverLetterPane";
import RequirementList from "./RequirementList";
import SummaryHeader from "./SummaryHeader";
import type { AnalyzeResponse } from "../../types/analysis";

export default function SplitView({ result }: { result: AnalyzeResponse }) {
  const [activeReq, setActiveReq] = useState<string | null>(null);

  const highlighted = new Set(
    activeReq
      ? result.requirements.find((r) => r.id === activeReq)?.evidence_ids ?? []
      : [],
  );

  return (
    <div className="flex flex-col gap-4">
      <SummaryHeader summary={result.summary} />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <CoverLetterPane
          sentences={result.cover_letter_sentences}
          highlighted={highlighted}
        />
        <RequirementList
          requirements={result.requirements}
          activeId={activeReq}
          onSelect={setActiveReq}
        />
      </div>
    </div>
  );
}

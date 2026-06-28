// 문항 1개 패널 (아코디언) — 좌 답변 / 우 카테고리 (스펙 v2)
// 카테고리 클릭 → 그 item의 evidence 문장만 하이라이트 (스코프 분리)
import { useState } from "react";

import AnswerPane from "./AnswerPane";
import CategoryList from "./CategoryList";
import type { ItemResult } from "../../types/analysis";

export default function ItemPanel({
  item,
  defaultOpen = false,
}: {
  item: ItemResult;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const [activeCat, setActiveCat] = useState<string | null>(null);

  const highlighted = new Set(
    activeCat
      ? item.categories.find((c) => c.id === activeCat)?.evidence_ids ?? []
      : [],
  );
  const s = item.summary;

  return (
    <div className="rounded-lg border border-border">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-2 p-4 text-left"
      >
        <span className="font-semibold">
          {open ? "▾" : "▸"} {item.question}
        </span>
        <span className="shrink-0 text-sm text-muted">
          🟢 {s.met} 🟡 {s.weak} 🔴 {s.missing}
        </span>
      </button>
      {open && (
        <div className="grid grid-cols-1 gap-4 p-4 pt-0 md:grid-cols-2">
          <AnswerPane sentences={item.answer_sentences} highlighted={highlighted} />
          <CategoryList
            categories={item.categories}
            activeId={activeCat}
            onSelect={setActiveCat}
          />
        </div>
      )}
    </div>
  );
}

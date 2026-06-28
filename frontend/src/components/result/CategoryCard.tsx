// 우: 카테고리 카드 — from 배지 + criteria + status (스펙 v2)
import type { Category, Status } from "../../types/analysis";

const STATUS_STYLE: Record<Status, { dot: string; ring: string }> = {
  met: { dot: "🟢", ring: "border-met" },
  weak: { dot: "🟡", ring: "border-weak" },
  missing: { dot: "🔴", ring: "border-missing" },
};

function FromBadge({ from }: { from: string }) {
  // 문항=accent, 공고=primary 로 출처 구분 (스펙 v2 신규 차별 포인트)
  const cls = from === "문항" ? "bg-nano-accent/30" : "bg-nano-primary/40";
  return <span className={`rounded px-1.5 py-0.5 text-xs ${cls}`}>{from}</span>;
}

interface Props {
  category: Category;
  active: boolean;
  onClick: () => void;
}

export default function CategoryCard({ category: c, active, onClick }: Props) {
  const st = STATUS_STYLE[c.status];
  return (
    <button
      onClick={onClick}
      className={`rounded-lg border-l-4 ${st.ring} bg-black/30 p-3 text-left transition ${
        active ? "ring-2 ring-nano-accent" : ""
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-semibold">
          {st.dot} {c.category}
        </span>
        <span className="flex shrink-0 gap-1">
          {c.from.map((f) => (
            <FromBadge key={f} from={f} />
          ))}
        </span>
      </div>
      <p className="mt-1 text-xs text-gray-400">{c.criteria}</p>
      <p className="mt-1 text-sm text-gray-300">{c.comment}</p>
      {c.suggestion && <p className="mt-1 text-sm text-weak">💡 {c.suggestion}</p>}
    </button>
  );
}

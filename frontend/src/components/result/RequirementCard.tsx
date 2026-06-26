// 우: 요구사항 카드 — status/comment/suggestion (스펙 7.3)
import type { Requirement, Status } from "../../types/analysis";

const STATUS_STYLE: Record<Status, { dot: string; ring: string }> = {
  met: { dot: "🟢", ring: "border-met" },
  weak: { dot: "🟡", ring: "border-weak" },
  missing: { dot: "🔴", ring: "border-missing" },
};

interface Props {
  requirement: Requirement;
  active: boolean;
  onClick: () => void;
}

export default function RequirementCard({ requirement: r, active, onClick }: Props) {
  const st = STATUS_STYLE[r.status];
  return (
    <button
      onClick={onClick}
      className={`rounded-lg border-l-4 ${st.ring} bg-black/30 p-3 text-left transition ${
        active ? "ring-2 ring-nano-accent" : ""
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="font-semibold">
          {st.dot} {r.text}
        </span>
        {r.category && <span className="text-xs text-gray-400">{r.category}</span>}
      </div>
      <p className="mt-1 text-sm text-gray-300">{r.comment}</p>
      {r.suggestion && <p className="mt-1 text-sm text-weak">💡 {r.suggestion}</p>}
    </button>
  );
}

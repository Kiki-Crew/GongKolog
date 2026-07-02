// 우: 카테고리 카드 — from 배지 + criteria + status (스펙 v2)
import type { Category, Status } from "../../types/analysis";

const STATUS_STYLE: Record<Status, { dot: string; ring: string }> = {
  met: { dot: "🟢", ring: "border-met" },
  weak: { dot: "🟡", ring: "border-weak" },
  missing: { dot: "🔴", ring: "border-missing" },
};

function FromBadge({ from }: { from: string }) {
  // 문항=accent, 공고=brand 로 출처 구분
  const cls =
    from === "문항"
      ? "bg-brand-accent/20 text-brand-accent"
      : "bg-brand/20 text-brand";

  return <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${cls}`}>{from}</span>;
}

function EvidenceTerms({ terms }: { terms?: string[] }) {
  const visibleTerms = (terms ?? []).filter(Boolean).slice(0, 4);

  if (visibleTerms.length === 0) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-1">
      {visibleTerms.map((term) => (
        <span
          key={term}
          className="rounded bg-brand-accent/10 px-1.5 py-0.5 text-xs text-brand-accent"
        >
          {term}
        </span>
      ))}
    </div>
  );
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
      className={`rounded-lg border-l-4 ${st.ring} bg-surface p-3 text-left ring-1 ring-border transition ${
        active ? "ring-2 ring-brand-accent" : ""
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

      <p className="mt-1 text-xs text-muted">{c.criteria}</p>

      <EvidenceTerms terms={c.evidence_terms} />

      <p className="mt-2 text-sm text-fg/80">{c.comment}</p>

      {c.analysis && (
        <div className="mt-2 rounded-md bg-bg/70 p-2 text-sm leading-relaxed text-fg/80">
          <span className="font-semibold text-fg">분석 </span>
          {c.analysis}
        </div>
      )}

      {c.suggestion && <p className="mt-2 text-sm text-weak">💡 {c.suggestion}</p>}
    </button>
  );
}
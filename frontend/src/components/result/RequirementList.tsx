// 우: 요구사항 리스트 🟢🟡🔴 (스펙 7.3)
import RequirementCard from "./RequirementCard";
import type { Requirement } from "../../types/analysis";

interface Props {
  requirements: Requirement[];
  activeId: string | null;
  onSelect: (id: string | null) => void;
}

export default function RequirementList({ requirements, activeId, onSelect }: Props) {
  return (
    <div className="flex flex-col gap-2">
      <h2 className="font-bold text-nano-accent">요구사항</h2>
      {requirements.map((r) => (
        <RequirementCard
          key={r.id}
          requirement={r}
          active={r.id === activeId}
          onClick={() => onSelect(r.id === activeId ? null : r.id)}
        />
      ))}
    </div>
  );
}

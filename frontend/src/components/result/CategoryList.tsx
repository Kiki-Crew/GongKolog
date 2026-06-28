// 우: 카테고리 리스트 (스펙 v2)
import CategoryCard from "./CategoryCard";
import type { Category } from "../../types/analysis";

interface Props {
  categories: Category[];
  activeId: string | null;
  onSelect: (id: string | null) => void;
}

export default function CategoryList({ categories, activeId, onSelect }: Props) {
  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-bold text-nano-accent">평가 카테고리</h3>
      {categories.map((c) => (
        <CategoryCard
          key={c.id}
          category={c}
          active={c.id === activeId}
          onClick={() => onSelect(c.id === activeId ? null : c.id)}
        />
      ))}
    </div>
  );
}

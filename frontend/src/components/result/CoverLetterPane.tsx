// 좌: 자소서 + 하이라이트 (스펙 7.3)
// activeReq에 연결된 evidence 문장 id를 강조.
import type { Sentence } from "../../types/analysis";

interface Props {
  sentences: Sentence[];
  highlighted: Set<string>;
}

export default function CoverLetterPane({ sentences, highlighted }: Props) {
  return (
    <div className="rounded-lg bg-black/30 p-4">
      <h2 className="mb-2 font-bold text-nano-accent">자소서</h2>
      <p className="leading-relaxed">
        {sentences.map((s) => (
          <span
            key={s.id}
            className={highlighted.has(s.id) ? "rounded bg-nano-accent/40 px-0.5" : ""}
          >
            {s.text}{" "}
          </span>
        ))}
      </p>
    </div>
  );
}

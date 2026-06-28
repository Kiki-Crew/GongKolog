// 좌: 답변 본문 + 하이라이트 (스펙 v2) — evidence는 같은 item 스코프
import type { Sentence } from "../../types/analysis";

interface Props {
  sentences: Sentence[];
  highlighted: Set<string>;
}

export default function AnswerPane({ sentences, highlighted }: Props) {
  return (
    <div className="rounded-lg bg-black/30 p-4">
      <h3 className="mb-2 text-sm font-bold text-nano-accent">답변</h3>
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

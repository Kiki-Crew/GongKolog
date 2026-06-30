// 랜딩 (스펙 7.2 "/")
import { useNavigate } from "react-router-dom";

import Button from "../components/common/Button";
import Logo from "../components/common/Logo";

function Legend({ color, label, desc }: { color: string; label: string; desc: string }) {
  return (
    <span className="flex items-center gap-2">
      <span className={`h-2.5 w-2.5 rounded-full ${color}`} />
      <span className="font-semibold">{label}</span>
      <span className="text-muted">{desc}</span>
    </span>
  );
}

function Feature({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5 text-left">
      <h3 className="font-semibold text-brand-accent">{title}</h3>
      <p className="mt-1.5 text-sm leading-relaxed text-muted">{desc}</p>
    </div>
  );
}

export default function Landing() {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center gap-12 py-16 text-center">
      {/* 히어로 */}
      <div className="flex flex-col items-center gap-5">
        <Logo size={112} />
        <span className="rounded-full border border-border px-3 py-1 text-sm text-muted">
          AI 자소서 진단
        </span>
        <h1 className="max-w-2xl text-4xl font-bold leading-snug sm:text-5xl">
          공고가 요구하는데,
          <br />
          <span className="text-brand-accent">내 자소서엔 빠진 부분은?</span>
        </h1>
        <p className="max-w-xl text-lg leading-relaxed text-muted">
          채용공고와 자소서를 의미 단위로 맞대어,
          <br />
          무엇이 충족됐고 무엇이 빠졌는지 한눈에 보여드립니다.
        </p>
        <div className="mt-2 flex flex-col items-center gap-2">
          <Button onClick={() => navigate("/analyze")}>진단 시작하기</Button>
          <span className="text-sm text-muted">로그인 없이 바로 진단할 수 있어요.</span>
        </div>
      </div>

      {/* 3색 범례 */}
      <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-sm">
        <Legend color="bg-met" label="충족" desc="기준을 잘 보여줌" />
        <Legend color="bg-weak" label="약함" desc="근거가 부족함" />
        <Legend color="bg-missing" label="공백" desc="답변에 없음" />
      </div>

      {/* 특징 */}
      <div className="grid w-full max-w-3xl grid-cols-1 gap-4 sm:grid-cols-3">
        <Feature
          title="문항별 평가"
          desc="각 자소서 문항을 공고의 인재상과 맞춰 평가 기준을 만듭니다."
        />
        <Feature
          title="의미 기반 매칭"
          desc="키워드가 아니라 의미로 읽어 놓친 역량을 짚어냅니다."
        />
        <Feature
          title="보완 제안"
          desc="약하거나 빠진 항목마다 무엇을 더 쓰면 좋을지 알려줍니다."
        />
      </div>
    </div>
  );
}

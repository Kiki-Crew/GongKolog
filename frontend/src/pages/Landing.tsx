// 랜딩 (스펙 7.2 "/") — 히어로 + 작동방식 + 기능 + CTA
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import Button from "../components/common/Button";

// 스크롤 등장 효과
function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll(".reveal");
    const io = new IntersectionObserver(
      (entries) =>
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("on");
            io.unobserve(e.target);
          }
        }),
      { threshold: 0.1 },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);
}

// ── 작은 조각들 ──
function StatusDot({ color }: { color: string }) {
  return <span className={`inline-block h-2.5 w-2.5 rounded-full ${color}`} />;
}

function CountPill({ color, n }: { color: string; n: number }) {
  return (
    <span className="flex items-center gap-1">
      <StatusDot color={color} />
      <span className="tabular-nums">{n}</span>
    </span>
  );
}

function FromBadge({ from }: { from: string }) {
  const cls =
    from === "문항" ? "bg-brand-accent/20 text-brand-accent" : "bg-brand/20 text-brand";
  return <span className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${cls}`}>{from}</span>;
}

// 히어로 우측 — 진단 결과 미리보기 카드
function MockResult() {
  const rows = [
    {
      name: "협업 가치관 및 실행력",
      from: ["문항", "공고"],
      border: "border-met",
      dot: "bg-met",
      comment: "코드리뷰 문화 도입을 주도하고 정량 성과를 제시했습니다.",
    },
    {
      name: "주도적 문제 해결",
      from: ["공고"],
      border: "border-weak",
      dot: "bg-weak",
      comment: "관련 노력은 보이나 어떤 문제를 해결했는지 더 구체화가 필요합니다.",
    },
    {
      name: "학습 및 성장",
      from: ["공고"],
      border: "border-met",
      dot: "bg-met",
      comment: "새로운 기술을 빠르게 습득해 적용한 과정이 드러납니다.",
    },
  ];
  return (
    <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-sm font-semibold">협업에서 중요한 요소와 사례는?</span>
        <span className="flex gap-2 text-xs text-muted">
          <CountPill color="bg-met" n={2} />
          <CountPill color="bg-weak" n={1} />
          <CountPill color="bg-missing" n={0} />
        </span>
      </div>
      <div className="flex flex-col gap-2">
        {rows.map((r) => (
          <div key={r.name} className={`rounded-lg border-l-4 ${r.border} bg-bg/50 p-3`}>
            <div className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-2 text-sm font-medium">
                <StatusDot color={r.dot} />
                {r.name}
              </span>
              <span className="flex shrink-0 gap-1">
                {r.from.map((f) => (
                  <FromBadge key={f} from={f} />
                ))}
              </span>
            </div>
            <p className="mt-1 text-xs leading-relaxed text-muted">{r.comment}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function StepCard({ n, title, desc }: { n: string; title: string; desc: string }) {
  return (
    <div className="reveal flex flex-col gap-2 rounded-xl border border-border bg-surface p-5 text-left">
      <span className="text-sm font-bold text-brand-accent">Step {n}</span>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="text-sm leading-relaxed text-muted">{desc}</p>
    </div>
  );
}

function Feature({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="reveal rounded-xl border border-border bg-surface p-5 text-left">
      <h3 className="font-semibold text-brand-accent">{title}</h3>
      <p className="mt-1.5 text-sm leading-relaxed text-muted">{desc}</p>
    </div>
  );
}

export default function Landing() {
  const navigate = useNavigate();
  useReveal();
  const scrollTo = (id: string) =>
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  return (
    <div className="flex flex-col gap-24 py-8">
      {/* HERO */}
      <section className="grid items-center gap-10 md:grid-cols-2">
        <div className="flex flex-col items-start gap-5">
          <span className="rounded-full border border-border px-3 py-1 text-sm text-muted">
            AI 자소서 진단
          </span>
          <h1 className="text-4xl font-bold leading-snug sm:text-5xl">
            공고가 요구하는데,
            <br />
            <span className="text-brand-accent">내 자소서엔 빠진 부분</span>은?
          </h1>
          <p className="max-w-md text-lg leading-relaxed text-muted">
            채용공고와 자소서를 의미 단위로 맞대어, 무엇이 충족됐고 무엇이 빠졌는지
            충족·약함·공백 3색으로 보여드립니다.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={() => navigate("/analyze")}>진단 시작하기</Button>
            <button
              onClick={() => scrollTo("how")}
              className="rounded-lg border border-border px-5 py-3 font-semibold hover:bg-brand/10"
            >
              작동 방식 보기
            </button>
          </div>
          <span className="text-sm text-muted">로그인 없이 바로 진단할 수 있어요.</span>
        </div>
        <MockResult />
      </section>

      {/* HOW IT WORKS */}
      <section id="how" className="flex flex-col gap-8">
        <div className="reveal text-center">
          <h2 className="text-3xl font-bold">3단계면 끝</h2>
          <p className="mt-2 text-muted">붙여넣고, 분석하고, 빈틈을 확인하세요.</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          <StepCard n="01" title="입력" desc="채용공고와 자소서 문항을 붙여넣습니다. 문항은 여러 개도 가능해요." />
          <StepCard
            n="02"
            title="의미 매칭"
            desc="문항과 공고를 합쳐 평가 기준을 만들고, 임베딩으로 관련 답변을 찾아 LLM이 판정합니다."
          />
          <StepCard
            n="03"
            title="3색 진단"
            desc="충족·약함·공백을 색으로 보여주고, 약하거나 빠진 부분엔 보완 제안을 함께 드립니다."
          />
        </div>
      </section>

      {/* FEATURES */}
      <section className="flex flex-col gap-8">
        <div className="reveal text-center">
          <h2 className="text-3xl font-bold">키워드가 아니라 의미로</h2>
          <p className="mt-2 text-muted">그냥 통째로 넣는 것과 다른 점.</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Feature
            title="의미 기반 매칭"
            desc='"팀 프로젝트 참여"가 "리더십"을 충족하는지까지 의미로 따져, 단어만 겹치는 착시를 걸러냅니다.'
          />
          <Feature
            title="문항별 평가"
            desc="각 자소서 문항을 공고의 인재상과 맞춰 평가 카테고리를 만들고, 출처(문항·공고)를 함께 표시합니다."
          />
          <Feature
            title="보완 제안"
            desc="약하거나 빠진 항목마다 무엇을 더 쓰면 좋을지 한 문장으로 제안합니다."
          />
          <Feature
            title="개인정보 보호"
            desc="비로그인 분석은 서버에 저장하지 않고 즉시 폐기합니다. 보관·공유는 로그인 시에만."
          />
        </div>
      </section>

      {/* CTA */}
      <section className="reveal flex flex-col items-center gap-4 rounded-2xl bg-brand/10 p-10 text-center">
        <h2 className="text-2xl font-bold">지금 바로 내 자소서를 진단해보세요</h2>
        <p className="text-muted">로그인 없이 시작할 수 있어요.</p>
        <Button onClick={() => navigate("/analyze")}>진단 시작하기</Button>
      </section>

      {/* FOOTER */}
      <footer className="flex items-center justify-between border-t border-border pt-6 text-sm text-muted">
        <span className="font-bold text-brand-accent">GongKolog</span>
        <span>AI 자소서 진단</span>
      </footer>
    </div>
  );
}

// 더미 JSON (백과 독립 개발용 — 스펙 v2)
import type { AnalyzeResponse } from "../types/analysis";

export const SAMPLE_RESPONSE: AnalyzeResponse = {
  analysis_id: "sample-0000",
  overall_summary: {
    total_items: 2,
    total_categories: 6,
    met: 2,
    weak: 3,
    missing: 1,
    coverage_score: 0.33,
  },
  items: [
    {
      item_id: "i1",
      question: "협업에서 가장 중요하다고 생각하는 요소와 그 사례는?",
      answer_sentences: [
        { id: "s1", text: "팀 프로젝트에서 정산 API를 함께 개발했습니다." },
        { id: "s2", text: "코드리뷰 문화를 제가 먼저 제안해 도입했고, 리뷰를 통해 버그를 30% 줄였습니다." },
        { id: "s3", text: "서로의 코드를 이해하려 매주 짧은 공유 세션도 열었습니다." },
      ],
      summary: { total: 3, met: 1, weak: 2, missing: 0 },
      categories: [
        {
          id: "c1",
          category: "협업 가치관 및 실행력",
          from: ["문항", "공고"],
          criteria: "협업에서 중요하게 생각하는 가치를 제시하고 실제 사례에서 본인 기여를 보여줘야 함",
          status: "met",
          evidence_ids: ["s2"],
          comment: "코드리뷰 문화 도입을 주도하고 정량 성과(버그 30% 감소)를 제시했습니다.",
          suggestion: null,
        },
        {
          id: "c2",
          category: "주도적 문제 해결",
          from: ["공고"],
          criteria: "문제를 주도적으로 인식하고 해결한 구체적 행동과 결과",
          status: "weak",
          evidence_ids: ["s3"],
          comment: "공유 세션 운영은 보이나 어떤 문제를 해결하려 했는지 불명확합니다.",
          suggestion: "이 세션이 어떤 문제를 해결하려 시작됐는지 맥락을 추가하세요.",
        },
        {
          id: "c3",
          category: "학습 및 성장",
          from: ["공고"],
          criteria: "협업 과정에서 새로운 지식·기술을 학습하고 적용한 경험",
          status: "weak",
          evidence_ids: ["s1"],
          comment: "협업 경험은 있으나 구체적 학습·성장 내용이 드러나지 않습니다.",
          suggestion: "협업 중 새로 배운 점과 그것을 어떻게 적용했는지 보강하세요.",
        },
      ],
    },
    {
      item_id: "i2",
      question: "어려운 목표에 도전해 본 경험은?",
      answer_sentences: [
        { id: "s1", text: "처음 써보는 FastAPI로 2주 만에 사내 도구를 출시해야 했습니다." },
        { id: "s2", text: "공식 문서를 빠르게 읽고 작은 프로토타입부터 만들어 점진적으로 확장했습니다." },
      ],
      summary: { total: 3, met: 1, weak: 1, missing: 1 },
      categories: [
        {
          id: "c1",
          category: "도전 목표 설정 및 실행",
          from: ["문항", "공고"],
          criteria: "어려운 목표를 주도적으로 설정하고 해결 과정을 구체적으로 제시",
          status: "weak",
          evidence_ids: ["s1"],
          comment: "도전 상황은 있으나 목표를 주도적으로 설정했는지 불명확합니다.",
          suggestion: "어떤 목표를 스스로 설정했는지와 해결 과정의 본인 역할을 명확히 하세요.",
        },
        {
          id: "c2",
          category: "학습 및 성장",
          from: ["문항", "공고"],
          criteria: "목표 달성을 위해 새 기술을 학습·적용하며 성장한 경험",
          status: "met",
          evidence_ids: ["s1", "s2"],
          comment: "새 기술을 빠르게 습득하고 점진적 개발로 적용한 과정이 드러납니다.",
          suggestion: null,
        },
        {
          id: "c3",
          category: "협업 및 소통",
          from: ["공고"],
          criteria: "목표 달성 과정에서 동료와 협력·소통하며 기여한 경험",
          status: "missing",
          evidence_ids: [],
          comment: "개인 작업에 초점이 맞춰져 협업·소통 내용이 없습니다.",
          suggestion: "동료와 어떻게 협력하고 기여했는지 사례를 추가하세요.",
        },
      ],
    },
  ],
};

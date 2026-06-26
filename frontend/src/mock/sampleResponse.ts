// 더미 JSON (백과 독립 개발용 — 스펙 Day2~3)
import type { AnalyzeResponse } from "../types/analysis";

export const SAMPLE_RESPONSE: AnalyzeResponse = {
  analysis_id: "sample-0000",
  summary: { total: 8, met: 5, weak: 2, missing: 1, coverage_score: 0.75 },
  cover_letter_sentences: [
    { id: "s1", text: "저는 스위프트로 앱을 출시한 경험이 있습니다." },
    { id: "s2", text: "팀 프로젝트로 일정 관리 서비스를 만들었습니다." },
    { id: "s3", text: "사용자 피드백을 받아 UI를 개선했습니다." },
  ],
  requirements: [
    {
      id: "r1",
      text: "iOS 개발 경험",
      category: "기술역량",
      status: "met",
      evidence_ids: ["s1"],
      comment: "스위프트 앱 출시 경험으로 충족됨",
      suggestion: null,
    },
    {
      id: "r2",
      text: "리더십 경험",
      category: "인성역량",
      status: "weak",
      evidence_ids: ["s2"],
      comment: "팀 프로젝트 참여는 있으나 주도적 역할이 드러나지 않음",
      suggestion: "본인이 주도한 의사결정이나 갈등 조율 사례를 한 문장 추가하세요.",
    },
    {
      id: "r3",
      text: "데이터 분석 역량",
      category: "기술역량",
      status: "missing",
      evidence_ids: [],
      comment: "자소서에서 관련 내용을 찾지 못함",
      suggestion: "공고가 데이터 분석을 요구합니다. 관련 경험이 있다면 추가하세요.",
    },
  ],
};

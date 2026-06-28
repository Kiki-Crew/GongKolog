// 응답 스키마 타입 (스펙 v2 5장)

export type Status = "met" | "weak" | "missing";

export interface Sentence {
  id: string;
  text: string;
}

export interface Category {
  id: string;
  category: string;
  from: string[]; // "문항" / "공고" / 둘 다
  criteria: string;
  status: Status;
  evidence_ids: string[]; // 같은 item 내 답변 문장 id만 유효 (스코프 분리)
  comment: string;
  suggestion?: string | null;
}

export interface ItemSummary {
  total: number;
  met: number;
  weak: number;
  missing: number;
}

export interface ItemResult {
  item_id: string;
  question: string;
  answer_sentences: Sentence[];
  summary: ItemSummary;
  categories: Category[];
}

export interface OverallSummary {
  total_items: number;
  total_categories: number;
  met: number;
  weak: number;
  missing: number;
  coverage_score?: number | null;
}

export interface AnalyzeResponse {
  analysis_id: string;
  overall_summary: OverallSummary;
  items: ItemResult[];
}

// ── 요청 ──
export interface AnalyzeItemInput {
  question: string;
  answer: string;
}

// ── 마이페이지 ──
export interface SavedDocument {
  id: string;
  user_id: string;
  title: string;
  content: string;
  created_at: string;
}

export interface AnalysisHistoryItem {
  id: string;
  created_at: string;
  overall_summary: OverallSummary;
}

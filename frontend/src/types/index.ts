// 응답 스키마 타입 (스펙 7.4 / 3장)

export type Status = "met" | "weak" | "missing";

export interface Sentence {
  id: string;
  text: string;
}

export interface Requirement {
  id: string;
  text: string;
  status: Status;
  evidence_ids: string[];
  comment: string;
  category?: string | null;
  suggestion?: string | null;
}

export interface Summary {
  total: number;
  met: number;
  weak: number;
  missing: number;
  coverage_score?: number | null;
}

export interface AnalyzeResponse {
  analysis_id: string;
  summary: Summary;
  cover_letter_sentences: Sentence[];
  requirements: Requirement[];
}

// 마이페이지용
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
  summary: Summary;
}

// Axios 인스턴스 + 인터셉터 (스펙 7.5)
// 모든 요청 헤더에 Supabase JWT 자동 첨부.
import axios from "axios";

import { supabase } from "./supabase";
import type {
  AnalysisHistoryItem,
  AnalyzeItemInput,
  AnalyzeResponse,
  SavedDocument,
} from "../types/analysis";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

api.interceptors.request.use(async (config) => {
  // Supabase 미설정이면 토큰 없이 진행 (비로그인 분석 가능)
  if (supabase) {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }
  }
  return config;
});

// ── API 함수 ──────────────────────────────────────────────────────
export async function analyze(
  job_posting: string,
  items: AnalyzeItemInput[],
): Promise<AnalyzeResponse> {
  const { data } = await api.post<AnalyzeResponse>("/api/analyze", {
    job_posting,
    items,
  });
  return data;
}

export async function getAnalysis(id: string): Promise<AnalyzeResponse> {
  const { data } = await api.get<AnalyzeResponse>(`/api/analyses/${id}`);
  return data;
}

export async function listAnalyses(): Promise<AnalysisHistoryItem[]> {
  const { data } = await api.get<AnalysisHistoryItem[]>("/api/analyses");
  return data;
}

export async function listDocuments(
  kind: "cover-letters" | "job-postings",
): Promise<SavedDocument[]> {
  const { data } = await api.get<SavedDocument[]>(`/api/${kind}`);
  return data;
}

export async function saveDocument(
  kind: "cover-letters" | "job-postings",
  title: string,
  content: string,
): Promise<SavedDocument> {
  const { data } = await api.post<SavedDocument>(`/api/${kind}`, { title, content });
  return data;
}

export async function deleteDocument(
  kind: "cover-letters" | "job-postings",
  id: string,
): Promise<void> {
  await api.delete(`/api/${kind}/${id}`);
}

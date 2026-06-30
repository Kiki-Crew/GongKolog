// Axios 인스턴스 + 인터셉터 (스펙 7.5)
// 모든 요청 헤더에 Supabase JWT 자동 첨부.
import axios from "axios";

import { supabase } from "./supabase";
import type {
  AnalysisHistoryItem,
  AnalyzeItemInput,
  AnalyzeResponse,
  SavedCoverLetter,
  SavedJobPosting,
} from "../types/analysis";

// VITE_API_BASE_URL 미설정 시 로컬 백엔드로 폴백 (.env 없어도 개발 동작)
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
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

// ── 저장된 공고 (title + content) ──
export async function listJobPostings(): Promise<SavedJobPosting[]> {
  const { data } = await api.get<SavedJobPosting[]>("/api/job-postings");
  return data;
}

export async function createJobPosting(
  title: string,
  content: string,
): Promise<SavedJobPosting> {
  const { data } = await api.post<SavedJobPosting>("/api/job-postings", {
    title,
    content,
  });
  return data;
}

export async function updateJobPosting(
  id: string,
  fields: { title?: string; content?: string },
): Promise<SavedJobPosting> {
  const { data } = await api.patch<SavedJobPosting>(`/api/job-postings/${id}`, fields);
  return data;
}

export async function deleteJobPosting(id: string): Promise<void> {
  await api.delete(`/api/job-postings/${id}`);
}

// ── 저장된 자소서 (title + items) ──
export async function listCoverLetters(): Promise<SavedCoverLetter[]> {
  const { data } = await api.get<SavedCoverLetter[]>("/api/cover-letters");
  return data;
}

export async function createCoverLetter(
  title: string,
  items: AnalyzeItemInput[],
): Promise<SavedCoverLetter> {
  const { data } = await api.post<SavedCoverLetter>("/api/cover-letters", {
    title,
    items,
  });
  return data;
}

export async function updateCoverLetter(
  id: string,
  fields: { title?: string; items?: AnalyzeItemInput[] },
): Promise<SavedCoverLetter> {
  const { data } = await api.patch<SavedCoverLetter>(`/api/cover-letters/${id}`, fields);
  return data;
}

export async function deleteCoverLetter(id: string): Promise<void> {
  await api.delete(`/api/cover-letters/${id}`);
}

// ── 회원 탈퇴 ──
export async function deleteAccount(): Promise<void> {
  await api.delete("/api/account");
}

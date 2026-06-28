// 분석 요청 상태 관리 훅 (스펙 v2)
import axios from "axios";
import { useState } from "react";

import { analyze } from "../lib/api";
import type { AnalyzeItemInput, AnalyzeResponse } from "../types/analysis";

export function useAnalyze() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(
    jobPosting: string,
    items: AnalyzeItemInput[],
  ): Promise<AnalyzeResponse | null> {
    if (!jobPosting.trim()) {
      setError("채용공고를 입력하세요.");
      return null;
    }
    const valid = items.filter((it) => it.question.trim() && it.answer.trim());
    if (!valid.length) {
      setError("문항(질문 + 답변)을 1개 이상 입력하세요.");
      return null;
    }
    setLoading(true);
    setError(null);
    try {
      return await analyze(jobPosting, valid);
    } catch (e) {
      // 백엔드가 준 실제 원인을 화면에 노출 (FastAPI는 {detail: "..."} 형식)
      let detail = "알 수 없는 오류";
      if (axios.isAxiosError(e)) {
        if (e.response) {
          const d = e.response.data?.detail;
          detail = `${e.response.status} ${typeof d === "string" ? d : JSON.stringify(e.response.data)}`;
        } else {
          detail = `서버에 연결할 수 없습니다 (${e.message}). 백엔드 실행/주소·CORS 확인.`;
        }
      } else if (e instanceof Error) {
        detail = e.message;
      }
      setError(`분석 실패: ${detail}`);
      return null;
    } finally {
      setLoading(false);
    }
  }

  return { run, loading, error };
}

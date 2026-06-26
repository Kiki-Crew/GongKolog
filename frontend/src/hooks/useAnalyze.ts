// 분석 요청 상태 관리 훅
import { useState } from "react";

import { analyze } from "../lib/api";
import type { AnalyzeResponse } from "../types/analysis";

export function useAnalyze() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(
    jobPosting: string,
    coverLetter: string,
  ): Promise<AnalyzeResponse | null> {
    if (!jobPosting.trim() || !coverLetter.trim()) {
      setError("공고와 자소서를 모두 입력하세요.");
      return null;
    }
    setLoading(true);
    setError(null);
    try {
      return await analyze(jobPosting, coverLetter);
    } catch {
      setError("분석에 실패했습니다. 잠시 후 다시 시도하세요.");
      return null;
    } finally {
      setLoading(false);
    }
  }

  return { run, loading, error };
}

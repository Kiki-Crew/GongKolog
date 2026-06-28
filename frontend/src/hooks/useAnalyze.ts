// 분석 요청 상태 관리 훅 (스펙 v2)
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
    } catch {
      setError("분석에 실패했습니다. 잠시 후 다시 시도하세요.");
      return null;
    } finally {
      setLoading(false);
    }
  }

  return { run, loading, error };
}

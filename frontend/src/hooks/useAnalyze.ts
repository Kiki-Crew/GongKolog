import axios from "axios";
import { useState } from "react";

import { analyze } from "../lib/api";
import type { AnalyzeItemInput, AnalyzeResponse } from "../types/analysis";

export type AnalyzeBlockReason = "daily-token-limit" | "request-too-large" | null;

export function useAnalyze() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [blockReason, setBlockReason] = useState<AnalyzeBlockReason>(null);

  function resetBlock() {
    if (blockReason) {
      setBlockReason(null);
      setError(null);
    }
  }

  function formatErrorDetail(data: unknown): string {
    const detail = (data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    return JSON.stringify(data);
  }

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
    setBlockReason(null);

    try {
      return await analyze(jobPosting, valid);
    } catch (e) {
      let detail = "알 수 없는 오류";

      if (axios.isAxiosError(e)) {
        if (e.response) {
          const status = e.response.status;
          detail = formatErrorDetail(e.response.data);

          if (status === 429) {
            setBlockReason("daily-token-limit");
          } else if (status === 413) {
            setBlockReason("request-too-large");
          }
        } else {
          detail = `서버에 연결할 수 없습니다 (${e.message}). 백엔드 실행, 주소, CORS 설정을 확인해 주세요.`;
        }
      } else if (e instanceof Error) {
        detail = e.message;
      }

      setError(detail);
      return null;
    } finally {
      setLoading(false);
    }
  }

  return { run, loading, error, blockReason, resetBlock };
}

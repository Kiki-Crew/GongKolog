// 결과 (스펙 7.2 "/result/:id")
import { useEffect, useState } from "react";
import { useLocation, useParams } from "react-router-dom";

import Spinner from "../components/common/Spinner";
import ResultView from "../components/result/ResultView";
import { useAuth } from "../hooks/useAuth";
import { getAnalysis } from "../lib/api";
import type { AnalyzeResponse } from "../types/analysis";

export default function Result() {
  const { id } = useParams();
  const location = useLocation();
  const { session } = useAuth();
  // 분석 직후엔 navigate state로 전달받음, 새로고침/공유 시 id로 재조회
  const [result, setResult] = useState<AnalyzeResponse | null>(
    (location.state as AnalyzeResponse) ?? null,
  );
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!result && id) {
      getAnalysis(id).then(setResult).catch(() => setNotFound(true));
    }
  }, [id, result]);

  if (notFound) {
    return (
      <p className="text-muted">
        결과를 찾을 수 없습니다. 비로그인 분석은 저장되지 않아 새로고침·공유로 다시 열 수
        없어요. 결과를 보관하려면 <b>로그인 후 분석</b>하세요.
      </p>
    );
  }
  if (!result) return <Spinner label="결과를 불러오는 중..." />;
  // 로그인 사용자 = 저장된 분석 → 공유 링크 유효
  return <ResultView result={result} showShare={!!session} />;
}

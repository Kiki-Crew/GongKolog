// 결과 (스펙 7.2 "/result/:id")
import { useEffect, useState } from "react";
import { useLocation, useParams } from "react-router-dom";

import Spinner from "../components/common/Spinner";
import SplitView from "../components/result/SplitView";
import { getAnalysis } from "../lib/api";
import type { AnalyzeResponse } from "../types/analysis";

export default function Result() {
  const { id } = useParams();
  const location = useLocation();
  // 분석 직후엔 navigate state로 전달받음, 새로고침/공유 시 id로 재조회
  const [result, setResult] = useState<AnalyzeResponse | null>(
    (location.state as AnalyzeResponse) ?? null,
  );

  useEffect(() => {
    if (!result && id) {
      getAnalysis(id).then(setResult).catch(() => setResult(null));
    }
  }, [id, result]);

  if (!result) return <Spinner label="결과를 불러오는 중..." />;
  return <SplitView result={result} />;
}

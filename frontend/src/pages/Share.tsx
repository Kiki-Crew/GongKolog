// 공유 결과 — 로그인 없이 열람 (스펙 7.2 "/share/:id")
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import Spinner from "../components/common/Spinner";
import ResultView from "../components/result/ResultView";
import { getAnalysis } from "../lib/api";
import type { AnalyzeResponse } from "../types/analysis";

export default function Share() {
  const { id } = useParams();
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (id) getAnalysis(id).then(setResult).catch(() => setNotFound(true));
  }, [id]);

  if (notFound) {
    return <p className="text-muted">결과를 찾을 수 없습니다 (만료되었거나 저장되지 않은 분석).</p>;
  }
  if (!result) return <Spinner label="결과를 불러오는 중..." />;
  return (
    <div>
      <p className="mb-4 text-sm text-muted">공유된 진단 결과입니다.</p>
      <ResultView result={result} />
    </div>
  );
}

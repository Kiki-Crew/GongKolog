// 공유 결과 — 로그인 없이 열람 (스펙 7.2 "/share/:id")
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import SplitView from "../components/SplitView";
import { getAnalysis } from "../lib/api";
import type { AnalyzeResponse } from "../types";

export default function Share() {
  const { id } = useParams();
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  useEffect(() => {
    if (id) getAnalysis(id).then(setResult).catch(() => setResult(null));
  }, [id]);

  if (!result) return <p className="text-gray-400">결과를 불러오는 중...</p>;
  return (
    <div>
      <p className="mb-4 text-sm text-gray-400">공유된 진단 결과입니다.</p>
      <SplitView result={result} />
    </div>
  );
}

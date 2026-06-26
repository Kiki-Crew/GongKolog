// 입력·분석 (스펙 7.2 "/analyze")
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import Button from "../components/common/Button";
import { useAnalyze } from "../hooks/useAnalyze";

export default function Analyze() {
  const [jobPosting, setJobPosting] = useState("");
  const [coverLetter, setCoverLetter] = useState("");
  const { run, loading, error } = useAnalyze();
  const navigate = useNavigate();

  async function onSubmit() {
    const result = await run(jobPosting, coverLetter);
    if (result) {
      // 결과는 백엔드가 저장 → id로 결과 페이지 이동
      navigate(`/result/${result.analysis_id}`, { state: result });
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold text-nano-accent">자소서 진단</h1>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <textarea
          className="h-72 rounded-lg bg-black/30 p-3"
          placeholder="채용공고를 붙여넣으세요"
          value={jobPosting}
          onChange={(e) => setJobPosting(e.target.value)}
        />
        <textarea
          className="h-72 rounded-lg bg-black/30 p-3"
          placeholder="자소서를 붙여넣으세요"
          value={coverLetter}
          onChange={(e) => setCoverLetter(e.target.value)}
        />
      </div>
      {error && <p className="text-missing">{error}</p>}
      <Button onClick={onSubmit} disabled={loading} className="self-start">
        {loading ? "분석 중..." : "진단하기"}
      </Button>
      {/* TODO: 로그인 시 저장된 자소서/공고 불러오기 (스펙 1.4) */}
    </div>
  );
}

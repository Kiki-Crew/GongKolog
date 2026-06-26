// 랜딩 (스펙 7.2 "/")
import { useNavigate } from "react-router-dom";

import Button from "../components/common/Button";

export default function Landing() {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center gap-6 py-20 text-center">
      <h1 className="text-4xl font-bold text-nano-accent">
        공고가 요구하는데, 내 자소서엔 빠진 부분은?
      </h1>
      <p className="max-w-xl text-gray-300">
        채용공고와 자소서를 의미 단위로 맞대어, 충족 / 약함 / 공백을 3색으로
        진단합니다.
      </p>
      <Button onClick={() => navigate("/analyze")}>진단 시작하기</Button>
    </div>
  );
}

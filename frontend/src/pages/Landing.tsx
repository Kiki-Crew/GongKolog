// 랜딩 (스펙 7.2 "/")
import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="flex flex-col items-center gap-6 py-20 text-center">
      <h1 className="text-4xl font-bold text-nano-accent">
        공고가 요구하는데, 내 자소서엔 빠진 부분은?
      </h1>
      <p className="max-w-xl text-gray-300">
        채용공고와 자소서를 의미 단위로 맞대어, 충족 / 약함 / 공백을 3색으로
        진단합니다.
      </p>
      <Link
        to="/analyze"
        className="rounded-lg bg-nano-primary px-6 py-3 font-semibold hover:bg-nano-accent"
      >
        진단 시작하기
      </Link>
    </div>
  );
}

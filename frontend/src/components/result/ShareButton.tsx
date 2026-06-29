// 공유 링크 복사 버튼 (저장된 분석에만 — 로그인 사용자)
import { useState } from "react";

export default function ShareButton({ id }: { id: string }) {
  const [copied, setCopied] = useState(false);
  const url = `${window.location.origin}/share/${id}`;

  async function copy() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // 클립보드 권한 없을 때 폴백
      window.prompt("아래 링크를 복사하세요", url);
    }
  }

  return (
    <button
      onClick={copy}
      className="shrink-0 rounded-lg border border-border px-3 py-1.5 text-sm hover:bg-brand/10"
    >
      {copied ? "✅ 복사됨" : "🔗 공유 링크 복사"}
    </button>
  );
}

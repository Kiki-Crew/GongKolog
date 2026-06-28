// 로딩 표시
export default function Spinner({ label = "불러오는 중..." }: { label?: string }) {
  return <p className="text-muted">{label}</p>;
}

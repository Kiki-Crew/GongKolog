// 라이트/다크 전환 버튼
import { useTheme } from "../../hooks/useTheme";

export default function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button
      onClick={toggle}
      title={theme === "dark" ? "라이트 모드로" : "다크 모드로"}
      aria-label="테마 전환"
      className="rounded-lg border border-border px-2 py-1 text-sm hover:bg-brand/10"
    >
      {theme === "dark" ? "☀️ 라이트" : "🌙 다크"}
    </button>
  );
}

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // 시맨틱 토큰 — 값은 index.css의 CSS 변수(:root / .dark)에서 주입
        bg: "rgb(var(--bg) / <alpha-value>)",
        surface: "rgb(var(--surface) / <alpha-value>)",
        fg: "rgb(var(--fg) / <alpha-value>)",
        muted: "rgb(var(--muted) / <alpha-value>)",
        border: "rgb(var(--border) / <alpha-value>)",
        brand: {
          DEFAULT: "rgb(var(--brand) / <alpha-value>)",
          accent: "rgb(var(--brand-accent) / <alpha-value>)",
        },
        // 3색 status (라이트/다크 공통)
        met: "#22c55e", // 🟢
        weak: "#d97706", // 🟡 (라이트에서도 보이도록 약간 진하게)
        missing: "#ef4444", // 🔴
      },
    },
  },
  plugins: [],
};

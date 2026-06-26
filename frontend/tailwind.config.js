/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // NANO 다크퍼플 (스펙 7.3)
        nano: {
          bg: "#0a0a1a",
          primary: "#534AB7",
          accent: "#7F77DD",
        },
        // 3색 status
        met: "#22c55e",     // 🟢
        weak: "#eab308",    // 🟡
        missing: "#ef4444", // 🔴
      },
    },
  },
  plugins: [],
};

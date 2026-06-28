// 라우팅 (스펙 7.2)
import { Link, Route, Routes } from "react-router-dom";

import ThemeToggle from "./components/common/ThemeToggle";
import Landing from "./pages/Landing";
import Analyze from "./pages/Analyze";
import Result from "./pages/Result";
import MyPage from "./pages/MyPage";
import Share from "./pages/Share";

export default function App() {
  return (
    <div className="min-h-screen">
      <nav className="flex items-center gap-4 border-b border-border p-4">
        <Link to="/" className="font-bold text-brand-accent">
          GongKolog
        </Link>
        <Link to="/analyze">분석</Link>
        <Link to="/mypage">마이페이지</Link>
        <div className="ml-auto">
          <ThemeToggle />
        </div>
      </nav>
      <main className="mx-auto max-w-5xl p-6">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/result/:id" element={<Result />} />
          <Route path="/mypage" element={<MyPage />} />
          <Route path="/share/:id" element={<Share />} />
        </Routes>
      </main>
    </div>
  );
}

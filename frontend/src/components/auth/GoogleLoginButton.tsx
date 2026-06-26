// Google OAuth 로그인 버튼 (스펙 7.5)
import { signInWithGoogle } from "../../hooks/useAuth";

export default function GoogleLoginButton() {
  return (
    <button
      onClick={() => signInWithGoogle()}
      className="rounded-lg bg-nano-primary px-6 py-3 font-semibold hover:bg-nano-accent"
    >
      Google로 로그인
    </button>
  );
}

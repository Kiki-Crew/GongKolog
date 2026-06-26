// 공용 버튼
import type { ButtonHTMLAttributes } from "react";

export default function Button({
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={`rounded-lg bg-nano-primary px-6 py-3 font-semibold hover:bg-nano-accent disabled:opacity-50 ${className}`}
      {...props}
    />
  );
}

// 공용 버튼
import type { ButtonHTMLAttributes } from "react";

export default function Button({
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={`rounded-lg bg-brand px-6 py-3 font-semibold text-white hover:bg-brand-accent disabled:opacity-50 ${className}`}
      {...props}
    />
  );
}

// GongKolog 로고 마크 (텍스트 없이 심볼만). 색은 brand 팔레트에 맞춤.
export default function Logo({
  size = 120,
  className = "",
}: {
  size?: number;
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 300 300"
      width={size}
      height={size}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      role="img"
      aria-label="GongKolog 로고"
    >
      <defs>
        <linearGradient id="gkLogoGradient" x1="40" y1="20" x2="260" y2="260">
          <stop offset="0%" stopColor="#7F77DD" />
          <stop offset="100%" stopColor="#453B98" />
        </linearGradient>
      </defs>

      {/* G */}
      <path
        d="
        M150 30
        C230 30 270 85 270 150
        C270 225 215 270 145 270
        C75 270 30 215 30 150
        C30 80 75 30 150 30
        Z

        M150 75
        C100 75 70 108 70 150
        C70 192 100 225 150 225
        C190 225 220 205 225 170
        H165
        C155 170 148 163 148 153
        C148 143 155 136 165 136
        H230
        C230 95 200 75 150 75
        Z"
        fill="url(#gkLogoGradient)"
        fillRule="evenodd"
      />

      {/* 문서 영역 */}
      <rect x="90" y="112" width="78" height="96" rx="16" fill="#F4F1FF" />
      <rect x="108" y="138" width="34" height="7" rx="3.5" fill="#B7AEEA" />
      <rect x="108" y="160" width="44" height="7" rx="3.5" fill="#B7AEEA" />
      <rect x="108" y="182" width="28" height="7" rx="3.5" fill="#B7AEEA" />
    </svg>
  );
}

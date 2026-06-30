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
          <stop offset="100%" stopColor="#534AB7" />
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
      <path
        d="M62 104C62 98 67 93 73 93H128V182H73C67 182 62 177 62 171V104Z"
        fill="#F4F1FF"
      />
      <rect x="80" y="118" width="32" height="6" rx="3" fill="#B7AEEA" />
      <rect x="80" y="140" width="40" height="6" rx="3" fill="#B7AEEA" />
      <rect x="80" y="162" width="28" height="6" rx="3" fill="#B7AEEA" />

      {/* 연결 포인트 */}
      <rect x="175" y="150" width="45" height="20" rx="10" fill="#7F77DD" opacity="0.3" />
    </svg>
  );
}

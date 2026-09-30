type SirLogoProps = {
  /** Altura em px (SVG escala proporcionalmente) */
  size?: number;
  /** Mostrar apenas o símbolo (sem wordmark) */
  markOnly?: boolean;
  /** Variante para fundo escuro (wordmark branco) */
  inverted?: boolean;
  className?: string;
};

export function SirLogo({
  size = 48,
  markOnly = false,
  inverted = false,
  className,
}: SirLogoProps) {
  const inkColor = inverted ? "#FFFFFF" : "#0F172A";
  const subColor = inverted ? "#93C5FD" : "#64748B";

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox={markOnly ? "0 0 40 40" : "0 0 200 48"}
      height={size}
      role="img"
      aria-label="SIR — Sistema Inteligente de Recrutamento"
      className={className}
      fill="none"
    >
      {/* Símbolo */}
      <rect width="40" height="40" rx="10" fill="#2563EB" />
      <path
        d="M14 20C14 16.6863 16.6863 14 20 14C23.3137 14 26 16.6863 26 20C26 23.3137 23.3137 26 20 26C16.6863 26 14 23.3137 14 20Z"
        stroke="white"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path
        d="M12 30C12 27.5 15 26 20 26C25 26 28 27.5 28 30"
        stroke="white"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path
        d="M25 15L28 12M28 12L31 15M28 12V18"
        stroke="#93C5FD"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="28" cy="12" r="1.5" fill="#60A5FA" />

      {/* Wordmark */}
      {!markOnly && (
        <>
          <text
            x="48"
            y="24"
            fill={inkColor}
            fontFamily="Inter, system-ui, sans-serif"
            fontSize="16"
            fontWeight="700"
            letterSpacing="-0.02em"
          >
            SIR
          </text>
          <text
            x="48"
            y="34"
            fill={subColor}
            fontFamily="Inter, system-ui, sans-serif"
            fontSize="10"
            fontWeight="500"
          >
            Recrutamento Inteligente
          </text>
        </>
      )}
    </svg>
  );
}
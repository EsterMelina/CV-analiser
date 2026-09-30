import "./TechBackdrop.css";

export function TechBackdrop() {
  return (
    <div aria-hidden="true" className="tb" data-purpose="neural-visual-background">
      {/* Gradiente base */}
      <div className="tb__base" />

      {/* Ondas de scanning */}
      <svg
        className="tb__svg"
        viewBox="0 0 1440 900"
        preserveAspectRatio="xMidYMid slice"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <radialGradient id="scanFade" cx="50%" cy="50%" r="75%">
            <stop offset="0%" stopColor="white" stopOpacity="1" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </radialGradient>
          <mask id="scanMask">
            <rect width="1440" height="900" fill="url(#scanFade)" />
          </mask>

          <radialGradient id="hubGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.55" />
            <stop offset="60%" stopColor="#60A5FA" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#93C5FD" stopOpacity="0" />
          </radialGradient>
        </defs>

        <g mask="url(#scanMask)">
          {/* Hub central */}
          <circle cx="720" cy="450" r="160" fill="url(#hubGlow)" />

          <circle cx="720" cy="450" r="0" fill="none" stroke="#1D4ED8" strokeWidth="1.6" className="tb__ring" />
          <circle cx="720" cy="450" r="0" fill="none" stroke="#2563EB" strokeWidth="1.4" className="tb__ring" style={{ animationDelay: "-1.6s" }} />
          <circle cx="720" cy="450" r="0" fill="none" stroke="#3B82F6" strokeWidth="1.2" className="tb__ring" style={{ animationDelay: "-3.2s" }} />

          <circle cx="720" cy="450" r="7" fill="#1D4ED8" />
          <circle cx="720" cy="450" r="3" fill="white" opacity="0.95" />

          {/* Scanner superior esquerdo */}
          <circle cx="220" cy="180" r="0" fill="none" stroke="#2563EB" strokeWidth="1.2" className="tb__ring" style={{ animationDuration: "7s", animationDelay: "-1s" }} />
          <circle cx="220" cy="180" r="0" fill="none" stroke="#60A5FA" strokeWidth="1" className="tb__ring" style={{ animationDuration: "7s", animationDelay: "-4.5s" }} />
          <circle cx="220" cy="180" r="3" fill="#2563EB" />

          {/* Scanner inferior direito */}
          <circle cx="1200" cy="720" r="0" fill="none" stroke="#2563EB" strokeWidth="1.2" className="tb__ring" style={{ animationDuration: "8s", animationDelay: "-2s" }} />
          <circle cx="1200" cy="720" r="0" fill="none" stroke="#60A5FA" strokeWidth="1" className="tb__ring" style={{ animationDuration: "8s", animationDelay: "-6s" }} />
          <circle cx="1200" cy="720" r="3" fill="#2563EB" />
        </g>
      </svg>

      {/* Vinheta */}
      <div className="tb__vignette" />
    </div>
  );
}
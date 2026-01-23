"use client";

interface NanoIconProps {
  size?: "large" | "small";
}

export function NanoIcon({ size = "large" }: NanoIconProps) {
  const dimensions = size === "large" ? "w-40 h-40 md:w-52 md:h-52" : "w-12 h-12";

  return (
    <div
      className={`${dimensions} rounded-full p-2 ${size === "large" ? "p-6" : "p-2"}`}
      style={{
        backgroundColor: size === "large" ? "#1a1816" : "transparent",
        border: size === "large" ? "1px solid rgba(255, 107, 53, 0.15)" : "none",
      }}
    >
      <svg
        viewBox="0 0 120 120"
        className="w-full h-full"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Outer ring - rotating */}
        <g>
          <circle
            cx="60"
            cy="60"
            r="54"
            stroke="url(#gradient1)"
            strokeWidth="2"
            strokeDasharray="8 4"
          />
          <animateTransform
            attributeName="transform"
            type="rotate"
            from="0 60 60"
            to="360 60 60"
            dur="20s"
            repeatCount="indefinite"
          />
        </g>

        {/* Middle ring */}
        <circle
          cx="60"
          cy="60"
          r="42"
          stroke="url(#gradient2)"
          strokeWidth="1.5"
          opacity="0.6"
        />

        {/* Inner glow circle - pulsing */}
        <circle cx="60" cy="60" r="30" fill="url(#radialGlow)">
          <animate
            attributeName="opacity"
            values="0.3;0.6;0.3"
            dur="3s"
            repeatCount="indefinite"
          />
        </circle>

        {/* Core particle - pulsing */}
        <circle cx="60" cy="60" r="18" fill="url(#coreGradient)">
          <animate attributeName="r" values="18;20;18" dur="2s" repeatCount="indefinite" />
        </circle>

        {/* Orbital particles - outer ring (clockwise) */}
        <g>
          <circle cx="60" cy="12" r="5" fill="#ff6b35">
            <animate
              attributeName="opacity"
              values="1;0.6;1"
              dur="2s"
              repeatCount="indefinite"
            />
          </circle>
          <circle cx="102" cy="78" r="4" fill="#ff8c5a">
            <animate
              attributeName="opacity"
              values="0.8;0.4;0.8"
              dur="2.5s"
              repeatCount="indefinite"
            />
          </circle>
          <circle cx="18" cy="78" r="4" fill="#ff8c5a">
            <animate
              attributeName="opacity"
              values="0.6;1;0.6"
              dur="1.8s"
              repeatCount="indefinite"
            />
          </circle>
          <animateTransform
            attributeName="transform"
            type="rotate"
            from="0 60 60"
            to="360 60 60"
            dur="8s"
            repeatCount="indefinite"
          />
        </g>

        {/* Orbital particles - inner ring (counter-clockwise) */}
        <g>
          <circle cx="60" cy="28" r="3" fill="#ffaa80">
            <animate
              attributeName="opacity"
              values="0.7;1;0.7"
              dur="1.5s"
              repeatCount="indefinite"
            />
          </circle>
          <circle cx="88" cy="76" r="2.5" fill="#ffaa80">
            <animate
              attributeName="opacity"
              values="1;0.5;1"
              dur="2s"
              repeatCount="indefinite"
            />
          </circle>
          <circle cx="32" cy="76" r="2.5" fill="#ffaa80">
            <animate
              attributeName="opacity"
              values="0.5;1;0.5"
              dur="1.7s"
              repeatCount="indefinite"
            />
          </circle>
          <animateTransform
            attributeName="transform"
            type="rotate"
            from="360 60 60"
            to="0 60 60"
            dur="5s"
            repeatCount="indefinite"
          />
        </g>

        {/* Twinkling accent particles */}
        <circle cx="80" cy="30" r="2" fill="#f5f0e8">
          <animate
            attributeName="opacity"
            values="0.3;1;0.3"
            dur="1.5s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="r"
            values="1.5;2.5;1.5"
            dur="1.5s"
            repeatCount="indefinite"
          />
        </circle>
        <circle cx="35" cy="45" r="1.5" fill="#f5f0e8">
          <animate
            attributeName="opacity"
            values="0.6;0.2;0.6"
            dur="2s"
            begin="0.3s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="r"
            values="1;2;1"
            dur="2s"
            begin="0.3s"
            repeatCount="indefinite"
          />
        </circle>
        <circle cx="85" cy="85" r="2" fill="#f5f0e8">
          <animate
            attributeName="opacity"
            values="0.2;0.9;0.2"
            dur="1.8s"
            begin="0.7s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="r"
            values="1.5;2.5;1.5"
            dur="1.8s"
            begin="0.7s"
            repeatCount="indefinite"
          />
        </circle>
        <circle cx="40" cy="90" r="1.5" fill="#f5f0e8">
          <animate
            attributeName="opacity"
            values="0.4;1;0.4"
            dur="2.2s"
            begin="1s"
            repeatCount="indefinite"
          />
        </circle>

        <defs>
          <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ff6b35" />
            <stop offset="100%" stopColor="#ff8c5a" />
          </linearGradient>
          <linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f5f0e8" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#ff6b35" stopOpacity="0.3" />
          </linearGradient>
          <radialGradient id="radialGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#ff6b35" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#ff6b35" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="coreGradient" cx="30%" cy="30%" r="70%">
            <stop offset="0%" stopColor="#ff8c5a" />
            <stop offset="100%" stopColor="#e55a2b" />
          </radialGradient>
        </defs>
      </svg>
    </div>
  );
}


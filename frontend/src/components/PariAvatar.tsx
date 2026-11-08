// Pari's avatar: an original, hand-built SVG character (no third-party artwork).
// States drive the animation: idle (breathe + blink), listening (pulse rings),
// thinking (orbiting sparks), speaking (mouth + halo glow).

import { useId } from "react";

export type AvatarState = "idle" | "listening" | "thinking" | "speaking";

export default function PariAvatar({ state = "idle", size = 160, className = "" }: {
  state?: AvatarState;
  size?: number;
  className?: string;
}) {
  // Unique SVG ids per instance: several avatars share the page, and a hidden one
  // must not own the gradients the visible ones reference.
  const u = "pa" + useId().replace(/[^a-zA-Z0-9]/g, "");
  return (
    <div className={`pari-avatar relative shrink-0 ${className}`} data-state={state} style={{ width: size, height: size }}>
      <div className="pari-glow absolute inset-[-12%] rounded-full" />
      <svg viewBox="0 0 200 200" className="relative size-full" role="img" aria-label={`Pari (${state})`}>
        <defs>
          <linearGradient id={`${u}ring`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#22d3ee" />
            <stop offset=".5" stopColor="#a855f7" />
            <stop offset="1" stopColor="#f472b6" />
          </linearGradient>
          <radialGradient id={`${u}bg`} cx=".5" cy=".42" r=".6">
            <stop offset="0" stopColor="#2a1b4d" />
            <stop offset="1" stopColor="#0d0a1c" />
          </radialGradient>
          <linearGradient id={`${u}skin`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#f6d9c8" />
            <stop offset="1" stopColor="#e2b39c" />
          </linearGradient>
          <linearGradient id={`${u}hair`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#4c2a7a" />
            <stop offset=".5" stopColor="#24123f" />
            <stop offset="1" stopColor="#6d28d9" />
          </linearGradient>
          <linearGradient id={`${u}hair-hi`} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#c084fc" stopOpacity="0" />
            <stop offset=".5" stopColor="#c084fc" stopOpacity=".55" />
            <stop offset="1" stopColor="#22d3ee" stopOpacity="0" />
          </linearGradient>
          <linearGradient id={`${u}suit`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#3b2a6b" />
            <stop offset="1" stopColor="#140d2a" />
          </linearGradient>
          <radialGradient id={`${u}iris`} cx=".4" cy=".4" r=".7">
            <stop offset="0" stopColor="#a5f3fc" />
            <stop offset=".6" stopColor="#22d3ee" />
            <stop offset="1" stopColor="#6d28d9" />
          </radialGradient>
          <clipPath id={`${u}clip`}>
            <circle cx="100" cy="100" r="88" />
          </clipPath>
          <filter id={`${u}soft`} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="2.2" />
          </filter>
        </defs>

        {/* halo */}
        <circle cx="100" cy="100" r="95" fill="none" stroke={`url(#${u}ring)`} strokeWidth="1.5" opacity=".9" />
        <g className="pa-spin">
          <circle cx="100" cy="100" r="95" fill="none" stroke={`url(#${u}ring)`} strokeWidth="3"
            strokeDasharray="38 260" strokeLinecap="round" />
        </g>
        <circle cx="100" cy="100" r="88" fill={`url(#${u}bg)`} />

        <g clipPath={`url(#${u}clip)`}>
          <g className="pa-breathe">
            {/* hair, back layer */}
            <path d="M100 28 C58 28 40 60 42 98 C44 132 34 160 26 200 L174 200 C166 160 156 132 158 98 C160 60 142 28 100 28 Z"
              fill={`url(#${u}hair)`} />
            {/* shoulders + collar */}
            <path d="M30 200 C36 168 62 152 100 150 C138 152 164 168 170 200 Z" fill={`url(#${u}suit)`} />
            <path d="M72 160 L100 182 L128 160" fill="none" stroke="#22d3ee" strokeWidth="1.3" opacity=".8" />
            <circle cx="100" cy="182" r="2.4" fill="#67e8f9" className="pa-core" />
            {/* neck */}
            <path d="M89 130 L89 152 C95 158 105 158 111 152 L111 130 Z" fill="#d9a68e" />
            {/* face */}
            <path d="M68 90 C68 62 82 46 100 46 C118 46 132 62 132 90 C132 116 119 138 100 142 C81 138 68 116 68 90 Z"
              fill={`url(#${u}skin)`} />
            {/* cheeks */}
            <ellipse cx="82" cy="112" rx="7" ry="4" fill="#f9a8d4" opacity=".35" filter={`url(#${u}soft)`} />
            <ellipse cx="118" cy="112" rx="7" ry="4" fill="#f9a8d4" opacity=".35" filter={`url(#${u}soft)`} />
            {/* brows */}
            <path d="M77 85 Q85 80 93 83.5" fill="none" stroke="#2b1747" strokeWidth="2" strokeLinecap="round" />
            <path d="M107 83.5 Q115 80 123 85" fill="none" stroke="#2b1747" strokeWidth="2" strokeLinecap="round" />
            {/* eyes */}
            <g className="pa-eyes">
              <path d="M77 95 Q85 88.5 93 95 Q85 99.5 77 95 Z" fill="#fff" />
              <path d="M107 95 Q115 88.5 123 95 Q115 99.5 107 95 Z" fill="#fff" />
              <circle cx="85" cy="94.6" r="3.6" fill={`url(#${u}iris)`} />
              <circle cx="115" cy="94.6" r="3.6" fill={`url(#${u}iris)`} />
              <circle cx="85" cy="94.6" r="1.4" fill="#1e1035" />
              <circle cx="115" cy="94.6" r="1.4" fill="#1e1035" />
              <circle cx="86.2" cy="93.4" r=".8" fill="#fff" />
              <circle cx="116.2" cy="93.4" r=".8" fill="#fff" />
              <path d="M76 94.6 Q85 87.5 94 94.6" fill="none" stroke="#1e1035" strokeWidth="1.6" strokeLinecap="round" />
              <path d="M106 94.6 Q115 87.5 124 94.6" fill="none" stroke="#1e1035" strokeWidth="1.6" strokeLinecap="round" />
              <path d="M76 94.6 L72.5 92.6" stroke="#1e1035" strokeWidth="1.3" strokeLinecap="round" />
              <path d="M124 94.6 L127.5 92.6" stroke="#1e1035" strokeWidth="1.3" strokeLinecap="round" />
            </g>
            {/* nose */}
            <path d="M100.5 100 Q103 109 99 111" fill="none" stroke="#c48a74" strokeWidth="1.2" strokeLinecap="round" />
            {/* mouth */}
            <g className="pa-mouth">
              <path d="M91 122 Q100 119.5 109 122 Q100 128.5 91 122 Z" fill="#d9467a" />
              <path d="M91 122 Q100 123.5 109 122" fill="none" stroke="#9d2456" strokeWidth=".9" />
            </g>
            {/* forehead gem */}
            <circle cx="100" cy="74" r="2.2" fill="#67e8f9" className="pa-core" />
            {/* hair, front fringe (side-swept) */}
            <path d="M66 104 C58 62 78 36 106 36 C130 37 144 56 138 84 C132 70 122 62 110 60 C100 60 92 62 86 68 C78 76 72 88 70 104 Z"
              fill={`url(#${u}hair)`} />
            <path d="M66 96 C62 124 58 150 50 178 C58 176 64 168 66 156 C70 138 70 118 70 104 Z" fill={`url(#${u}hair)`} />
            <path d="M136 84 C140 118 144 150 152 178 C144 176 138 168 135 156 C131 136 130 112 131 92 Z" fill={`url(#${u}hair)`} />
            <path d="M78 48 C92 40 116 40 130 52" fill="none" stroke={`url(#${u}hair-hi)`} strokeWidth="3" strokeLinecap="round" />
            {/* earrings */}
            <circle cx="67" cy="110" r="2" fill="#f0abfc" className="pa-core" />
            <circle cx="133" cy="110" r="2" fill="#f0abfc" className="pa-core" />
          </g>
        </g>

        {/* thinking sparks */}
        <g className="pa-sparks">
          <circle cx="100" cy="6" r="3" fill="#67e8f9" />
          <circle cx="194" cy="100" r="2.4" fill="#f0abfc" />
          <circle cx="34" cy="166" r="2" fill="#c084fc" />
        </g>
      </svg>
      <div className="pa-pulse absolute inset-0 rounded-full" />
      <div className="pa-pulse pa-pulse-2 absolute inset-0 rounded-full" />
    </div>
  );
}

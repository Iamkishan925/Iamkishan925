import { useEffect, useRef, type RefObject } from "react";
import { prefersReducedMotion } from "../lib/util";

// Canvas waveform. With an analyser it draws real microphone levels;
// without one it shows a calm idle line (or a livelier one while `busy`).
export default function Waveform({ analyser, busy = false, className = "" }: {
  analyser?: RefObject<AnalyserNode | null>;
  busy?: boolean;
  className?: string;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const el = canvas.current;
    if (!el) return;
    const g = el.getContext("2d");
    if (!g) return;
    const reduced = prefersReducedMotion();
    let raf = 0;
    const bars = 48;
    const data = new Uint8Array(128);

    const draw = (t: number) => {
      const dpr = window.devicePixelRatio || 1;
      const w = el.clientWidth;
      const h = el.clientHeight;
      if (el.width !== w * dpr || el.height !== h * dpr) {
        el.width = w * dpr;
        el.height = h * dpr;
      }
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
      g.clearRect(0, 0, w, h);
      const grad = g.createLinearGradient(0, 0, w, 0);
      grad.addColorStop(0, "#22d3ee");
      grad.addColorStop(0.5, "#a855f7");
      grad.addColorStop(1, "#f472b6");
      g.fillStyle = grad;

      const a = analyser?.current;
      if (a) a.getByteFrequencyData(data);
      const gap = 3;
      const bw = Math.max(2, (w - gap * (bars - 1)) / bars);
      for (let i = 0; i < bars; i++) {
        let v: number;
        if (a) {
          // Fold the spectrum so the middle bars carry the voice band.
          const idx = Math.floor((Math.abs(i - bars / 2) / (bars / 2)) * 60);
          v = data[idx] / 255;
        } else {
          const amp = busy ? 0.55 : 0.12;
          v = reduced ? amp * 0.5 : amp * (0.5 + 0.5 * Math.sin(t / (busy ? 160 : 600) + i * 0.45)) * (1 - Math.abs(i - bars / 2) / bars);
        }
        const bh = Math.max(2, v * h);
        const x = i * (bw + gap);
        g.globalAlpha = 0.35 + 0.65 * Math.min(1, v * 1.6);
        g.beginPath();
        g.roundRect(x, (h - bh) / 2, bw, bh, bw / 2);
        g.fill();
      }
      if (!reduced || a) raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [analyser, busy]);

  return <canvas ref={canvas} className={`block w-full ${className}`} aria-hidden />;
}

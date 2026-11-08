import { useEffect, useState } from "react";
import PariAvatar from "./PariAvatar";
import { prefersReducedMotion } from "../lib/util";

// Startup animation: rings converge, Pari fades in, name reveals. ~2.4s, click to skip.
export default function Intro({ onDone, skipLabel }: { onDone: () => void; skipLabel: string }) {
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    if (prefersReducedMotion()) {
      onDone();
      return;
    }
    const a = setTimeout(() => setLeaving(true), 2300);
    const b = setTimeout(onDone, 2800);
    return () => {
      clearTimeout(a);
      clearTimeout(b);
    };
  }, [onDone]);

  return (
    <div className={`fixed inset-0 z-50 grid place-items-center bg-[var(--bg)] ${leaving ? "intro-out" : ""}`}
      onClick={onDone} role="presentation">
      <div className="aurora"><div className="grid-overlay" /></div>
      <div className="relative grid place-items-center">
        <div className="absolute size-[340px] rounded-full intro-ring" />
        <div className="absolute size-[260px] rounded-full intro-ring" />
        <div className="absolute size-[200px] rounded-full intro-ring" />
        <div className="intro-avatar"><PariAvatar size={160} state="speaking" /></div>
        <div className="intro-title font-display absolute top-[calc(100%+70px)] text-2xl font-semibold tracking-[0.32em] gradient-text">
          PARI
        </div>
      </div>
      <button className="absolute bottom-8 right-6 muted text-sm" onClick={onDone}>{skipLabel}</button>
    </div>
  );
}

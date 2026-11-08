import { useCallback, useEffect, useRef, useState } from "react";

// Microphone access + live levels via the Web Audio API. Audio never leaves the
// browser here; speech-to-text (which does send audio to a provider) is Phase 3.
export function useMic() {
  const [active, setActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const analyser = useRef<AnalyserNode | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const ctx = useRef<AudioContext | null>(null);

  const stop = useCallback(() => {
    stream.current?.getTracks().forEach((t) => t.stop());
    ctx.current?.close().catch(() => {});
    stream.current = null;
    ctx.current = null;
    analyser.current = null;
    setActive(false);
  }, []);

  const start = useCallback(async () => {
    setError(null);
    try {
      const s = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
      const c = new AudioContext();
      const a = c.createAnalyser();
      a.fftSize = 256;
      a.smoothingTimeConstant = 0.75;
      c.createMediaStreamSource(s).connect(a);
      stream.current = s;
      ctx.current = c;
      analyser.current = a;
      setActive(true);
    } catch (e) {
      setError(e instanceof Error ? e.name : "error");
      stop();
    }
  }, [stop]);

  useEffect(() => stop, [stop]);

  return { active, error, analyser, start, stop, toggle: () => (active ? stop() : start()) };
}

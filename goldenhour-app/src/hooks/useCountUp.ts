/* useCountUp — smooth numeric interpolation (~600ms) */
import { useState, useEffect, useRef } from 'react';

export function useCountUp(target: number, duration = 600): number {
  const safeTarget = typeof target === 'number' && Number.isFinite(target) ? target : 0;
  const [value, setValue] = useState(safeTarget);
  const prevRef = useRef(safeTarget);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const to = typeof target === 'number' && Number.isFinite(target) ? target : 0;
    const from = typeof prevRef.current === 'number' && Number.isFinite(prevRef.current) ? prevRef.current : 0;
    if (from === to) {
      setValue(to);
      return;
    }

    const start = performance.now();
    const animate = (time: number) => {
      const elapsed = time - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out quad
      const eased = 1 - (1 - progress) * (1 - progress);
      const current = Math.round(from + (to - from) * eased);
      setValue(Number.isFinite(current) ? current : to);

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      } else {
        prevRef.current = to;
      }
    };

    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);

  return value;
}

/* usePointerFx — button ripple + magnetic hover (disabled on pointer:coarse) */
import { useEffect, useRef, useCallback } from 'react';

export function usePointerFx(ref: React.RefObject<HTMLElement | null>) {
  const isCoarse = useRef(false);

  useEffect(() => {
    isCoarse.current = window.matchMedia('(pointer: coarse)').matches;
  }, []);

  const handleClick = useCallback((e: MouseEvent) => {
    if (isCoarse.current) return;
    const el = ref.current;
    if (!el) return;

    const rect = el.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const ripple = document.createElement('span');
    ripple.style.cssText = `
      position:absolute; left:${x}px; top:${y}px;
      width:0; height:0; border-radius:50%;
      background:rgba(255,255,255,.35);
      transform:translate(-50%,-50%);
      pointer-events:none;
      animation: rippleOut .6s var(--ease) forwards;
    `;
    el.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
  }, [ref]);

  useEffect(() => {
    const el = ref.current;
    if (!el || isCoarse.current) return;

    el.addEventListener('click', handleClick);
    return () => el.removeEventListener('click', handleClick);
  }, [ref, handleClick]);
}

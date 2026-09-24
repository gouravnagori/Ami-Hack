/* useParallax — pointer-based parallax via data-depth */
import { useEffect, useRef } from 'react';

export function useParallax(containerRef: React.RefObject<HTMLElement | null>) {
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Skip on touch devices
    if (window.matchMedia('(pointer: coarse)').matches) return;

    const handleMove = (e: MouseEvent) => {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(() => {
        const rect = container.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width - 0.5;
        const y = (e.clientY - rect.top) / rect.height - 0.5;

        container.querySelectorAll<HTMLElement>('[data-depth]').forEach((el) => {
          const depth = parseFloat(el.dataset.depth || '0');
          const moveX = x * depth * 30;
          const moveY = y * depth * 20;
          el.style.transform = `translate3d(${moveX}px, ${moveY}px, 0)`;
        });
      });
    };

    const handleLeave = () => {
      container.querySelectorAll<HTMLElement>('[data-depth]').forEach((el) => {
        el.style.transform = '';
      });
    };

    container.addEventListener('mousemove', handleMove);
    container.addEventListener('mouseleave', handleLeave);

    return () => {
      cancelAnimationFrame(rafRef.current);
      container.removeEventListener('mousemove', handleMove);
      container.removeEventListener('mouseleave', handleLeave);
    };
  }, [containerRef]);
}

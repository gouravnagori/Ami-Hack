/* useReveal — IntersectionObserver for data-reveal sections */
import { useEffect } from 'react';

export function useReveal() {
  useEffect(() => {
    document.documentElement.classList.add('js-ready');

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );

    document.querySelectorAll('[data-reveal], [data-mask]').forEach((el) => {
      observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);
}

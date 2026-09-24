import React, { useState } from 'react';
import styles from './FAQ.module.css';

export interface FAQItem {
  q?: string;
  a?: string;
  question?: string;
  answer?: string;
}

export const FAQ: React.FC<{ items: FAQItem[] }> = ({ items }) => {
  const [openIdx, setOpenIdx] = useState<number | null>(null);

  return (
    <div className={styles.faq}>
      {items.map((item, i) => {
        const questionText = item.question || item.q || '';
        const answerText = item.answer || item.a || '';

        return (
          <div key={i} className={`${styles.item} ${openIdx === i ? styles.open : ''}`}>
            <button
              className={styles.button}
              onClick={() => setOpenIdx(openIdx === i ? null : i)}
              aria-expanded={openIdx === i}
            >
              {questionText}
              <span>+</span>
            </button>
            <div className={styles.answer} role="region">
              <div>
                <p>{answerText}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

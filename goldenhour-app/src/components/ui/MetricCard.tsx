import React from 'react';
import { useCountUp } from '../../hooks/useCountUp';
import styles from './MetricCard.module.css';

interface MetricCardProps {
  label: string;
  value: number;
  format?: (n: number) => string;
  sub?: string;
  variant?: 'default' | 'blue' | 'warning';
  wide?: boolean;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  format,
  sub,
  variant = 'default',
  wide = false,
  className = '',
}) => {
  const safeValue = typeof value === 'number' && Number.isFinite(value) ? value : 0;
  const tweened = useCountUp(safeValue);
  const safeTweened = typeof tweened === 'number' && Number.isFinite(tweened) ? tweened : safeValue;

  let display: string;
  if (format) {
    try {
      display = format(safeTweened);
    } catch {
      display = safeTweened.toString();
    }
  } else {
    display = safeTweened.toString();
  }

  if (display.includes('NaN')) {
    display = display.replace(/NaN/g, '0');
  }

  return (
    <div className={`${styles.card} ${styles[variant]} ${wide ? styles.wide : ''} ${className}`}>
      <small>{label}</small>
      <strong>{display}</strong>
      {sub && <em>{sub}</em>}
    </div>
  );
};

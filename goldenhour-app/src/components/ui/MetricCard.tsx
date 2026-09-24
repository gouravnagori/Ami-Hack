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
  const tweened = useCountUp(value);
  const display = format ? format(tweened) : tweened.toString();

  return (
    <div className={`${styles.card} ${styles[variant]} ${wide ? styles.wide : ''} ${className}`}>
      <small>{label}</small>
      <strong>{display}</strong>
      {sub && <em>{sub}</em>}
    </div>
  );
};

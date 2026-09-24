/* ============================================================
   GoldenHour — CountdownRing (THE signature component)
   SVG ring that drains in real time toward the safe-until deadline.
   ============================================================ */
import React, { useMemo } from 'react';
import { useRemainingSeconds } from '../../hooks/useNow';
import { formatCountdown, formatTime } from '../../lib/format';
import type { Risk } from '../../types/api';
import styles from './CountdownRing.module.css';

interface CountdownRingProps {
  deadline: string;
  startedAt?: string;
  initialSeconds?: number;
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  className?: string;
}

const SIZES = { sm: 44, md: 88, lg: 168 } as const;

function getRisk(remaining: number, total: number): Risk {
  if (total <= 0) return 'critical';
  const ratio = remaining / total;
  if (ratio > 0.30) return 'safe';
  if (ratio > 0.10) return 'tight';
  return 'critical';
}

const RISK_COLORS: Record<Risk, { stroke: string; track: string }> = {
  safe: { stroke: 'var(--green)', track: 'var(--soft)' },
  tight: { stroke: 'var(--peach)', track: 'var(--warn-tint)' },
  critical: { stroke: 'var(--red)', track: 'var(--warn-tint)' },
};

export const CountdownRing: React.FC<CountdownRingProps> = ({
  deadline,
  startedAt,
  initialSeconds,
  size = 'md',
  label,
  className = '',
}) => {
  const remaining = useRemainingSeconds(deadline);
  const total = useMemo(() => {
    if (initialSeconds && initialSeconds > 0) return initialSeconds;
    const start = startedAt ? new Date(startedAt).getTime() : new Date(deadline).getTime() - 3600 * 1000;
    const end = new Date(deadline).getTime();
    return Math.max(1, Math.floor((end - start) / 1000));
  }, [startedAt, deadline, initialSeconds]);

  const risk = getRisk(remaining, total);
  const progress = Math.max(0, Math.min(1, remaining / total));
  const dim = SIZES[size];
  const strokeWidth = size === 'sm' ? 3 : size === 'md' ? 4 : 6;
  const radius = (dim - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference * (1 - progress);
  const colors = RISK_COLORS[risk];

  const countdownText = formatCountdown(remaining);
  const labelText = label || `safe until ${formatTime(deadline)}`;

  return (
    <div
      className={`${styles.ring} ${styles[size]} ${risk === 'critical' ? styles.critical : ''} ${className}`}
      role="timer"
      aria-label={`${Math.ceil(remaining / 60)} minutes left to deliver`}
    >
      <svg width={dim} height={dim} viewBox={`0 0 ${dim} ${dim}`}>
        {/* Track */}
        <circle
          cx={dim / 2}
          cy={dim / 2}
          r={radius}
          fill="none"
          stroke={colors.track}
          strokeWidth={strokeWidth}
        />
        {/* Progress */}
        <circle
          cx={dim / 2}
          cy={dim / 2}
          r={radius}
          fill="none"
          stroke={colors.stroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          transform={`rotate(-90 ${dim / 2} ${dim / 2})`}
          style={{ transition: 'stroke-dashoffset 1s linear, stroke .3s ease' }}
        />
      </svg>
      <div className={styles.center}>
        <span className={styles.time}>{countdownText}</span>
        {size !== 'sm' && <span className={styles.label}>{labelText}</span>}
      </div>
    </div>
  );
};

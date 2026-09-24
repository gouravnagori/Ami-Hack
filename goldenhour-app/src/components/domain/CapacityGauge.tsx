import React from 'react';
import { useCountUp } from '../../hooks/useCountUp';

interface CapacityGaugeProps {
  available: number;
  max: number;
  committed?: number;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const CapacityGauge: React.FC<CapacityGaugeProps> = ({
  available,
  max,
  committed = 0,
  label = 'Available Portions',
  size = 'md',
}) => {
  const animatedAvailable = useCountUp(available, 600);
  const percent = max > 0 ? Math.min(100, Math.round((animatedAvailable / max) * 100)) : 0;

  // Sizing
  const dim = size === 'sm' ? 120 : size === 'lg' ? 220 : 160;
  const stroke = size === 'sm' ? 10 : size === 'lg' ? 18 : 14;
  const radius = (dim - stroke) / 2;
  const circum = 2 * Math.PI * radius;
  const strokeDashoffset = circum - (percent / 100) * circum;

  const color = percent < 15 ? 'var(--red)' : percent < 40 ? 'var(--peach)' : 'var(--green)';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
      <div style={{ position: 'relative', width: dim, height: dim }}>
        <svg width={dim} height={dim} style={{ transform: 'rotate(-90deg)' }}>
          {/* Track */}
          <circle
            cx={dim / 2}
            cy={dim / 2}
            r={radius}
            fill="transparent"
            stroke="var(--line)"
            strokeWidth={stroke}
          />
          {/* Filled Arc */}
          <circle
            cx={dim / 2}
            cy={dim / 2}
            r={radius}
            fill="transparent"
            stroke={color}
            strokeWidth={stroke}
            strokeDasharray={circum}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.6s var(--ease), stroke 0.4s ease' }}
          />
        </svg>

        {/* Center label */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <span
            style={{
              fontSize: size === 'sm' ? '1.5rem' : size === 'lg' ? '2.8rem' : '2.1rem',
              fontWeight: 800,
              lineHeight: 1,
              color: 'var(--ink)',
            }}
          >
            {Math.round(animatedAvailable)}
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '2px' }}>
            / {max} slots
          </span>
        </div>
      </div>

      <div style={{ marginTop: '10px' }}>
        <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--deep)' }}>{label}</div>
        {committed > 0 && (
          <div style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: '2px' }}>
            +{committed} committed incoming
          </div>
        )}
      </div>
    </div>
  );
};

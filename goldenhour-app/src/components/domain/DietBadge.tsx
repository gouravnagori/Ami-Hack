import React from 'react';
import type { DietType } from '../../types/api';

const DIET_CONFIG: Record<DietType, { color: string; label: string }> = {
  veg: { color: '#2e7d32', label: 'Veg' },
  egg: { color: '#d4a762', label: 'Egg' },
  non_veg: { color: '#c62828', label: 'Non-veg' },
};

export const DietBadge: React.FC<{ diet: DietType; className?: string }> = ({ diet, className = '' }) => {
  const cfg = DIET_CONFIG[diet];
  return (
    <span className={className} style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '5px',
      fontSize: '.75rem',
      fontWeight: 600,
    }}>
      <span style={{
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        background: cfg.color,
        flexShrink: 0,
      }} aria-hidden="true" />
      {cfg.label}
    </span>
  );
};

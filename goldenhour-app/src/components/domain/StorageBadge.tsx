import React from 'react';
import type { StorageCondition } from '../../types/api';

const CONFIG: Record<StorageCondition, { label: string; icon: string; bg: string; color: string; border: string }> = {
  ambient: {
    label: 'Ambient',
    icon: '📦',
    bg: 'var(--soft)',
    color: 'var(--deep)',
    border: 'var(--line)',
  },
  hot: {
    label: 'Keep Warm',
    icon: '♨️',
    bg: '#fff5f1',
    color: 'var(--red)',
    border: '#f5b19d',
  },
  cold: {
    label: 'Refrigerated',
    icon: '❄️',
    bg: 'var(--blue-tint)',
    color: 'var(--blue-text)',
    border: 'var(--blue)',
  },
};

export const StorageBadge: React.FC<{
  storage: StorageCondition;
  className?: string;
}> = ({ storage, className = '' }) => {
  const c = CONFIG[storage] || CONFIG.ambient;
  return (
    <span
      className={`storage-badge ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        padding: '3px 9px',
        borderRadius: 'var(--r-pill)',
        fontSize: '0.78rem',
        fontWeight: 600,
        background: c.bg,
        color: c.color,
        border: `1px solid ${c.border}`,
        whiteSpace: 'nowrap',
      }}
    >
      <span aria-hidden="true" style={{ fontSize: '0.85em' }}>{c.icon}</span>
      <span>{c.label}</span>
    </span>
  );
};

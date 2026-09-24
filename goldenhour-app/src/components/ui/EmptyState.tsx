import React from 'react';
import { Button } from './Button';

interface EmptyStateProps {
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionLabel,
  onAction,
  icon = '📦',
}) => (
  <div style={{
    textAlign: 'center',
    padding: '60px 24px',
    maxWidth: '420px',
    margin: '0 auto',
  }}>
    <div style={{ fontSize: '2.5rem', marginBottom: '16px' }}>{icon}</div>
    <h3 style={{ fontSize: '1.1rem', marginBottom: '8px' }}>{title}</h3>
    {description && (
      <p style={{ color: 'var(--muted)', fontSize: '.92rem', marginBottom: '20px' }}>{description}</p>
    )}
    {actionLabel && onAction && (
      <Button variant="primary" onClick={onAction}>{actionLabel}</Button>
    )}
  </div>
);

import React from 'react';

export const LiveBadge: React.FC<{ text?: string; className?: string }> = ({
  text = 'Live',
  className = '',
}) => (
  <span className={`live-badge ${className}`} style={{
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    padding: '7px 9px',
    borderRadius: '99px',
    background: 'var(--soft)',
    fontSize: '.67rem',
    color: 'var(--deep)',
    fontWeight: 700,
  }}>
    <span style={{
      width: '7px',
      height: '7px',
      borderRadius: '50%',
      background: 'var(--green-dark)',
      boxShadow: '0 0 0 0 #69a83f55',
      animation: 'livePulse 2s infinite, liveBeat 3.5s ease-in-out infinite',
      flexShrink: 0,
    }} />
    {text}
  </span>
);

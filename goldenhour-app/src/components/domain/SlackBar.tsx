import React from 'react';
import type { Risk } from '../../types/api';
import { formatSlack } from '../../lib/format';

interface SlackBarProps {
  slackSeconds: number;
  totalSeconds?: number;
  windowTotalSeconds?: number;
  risk: Risk;
  className?: string;
}

const RISK_COLORS: Record<Risk, string> = {
  safe: 'var(--green)',
  tight: 'var(--peach)',
  critical: 'var(--red)',
};

export const SlackBar: React.FC<SlackBarProps> = ({
  slackSeconds,
  totalSeconds,
  windowTotalSeconds,
  risk,
  className = '',
}) => {
  const effectiveTotal = totalSeconds || windowTotalSeconds || 3600;
  const ratio = Math.max(0, Math.min(1, slackSeconds / Math.max(1, effectiveTotal)));

  return (
    <div className={className} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div style={{
        flex: 1,
        height: '4px',
        borderRadius: '4px',
        background: 'var(--soft)',
        overflow: 'hidden',
      }}>
        <div style={{
          height: '100%',
          width: `${ratio * 100}%`,
          borderRadius: '4px',
          background: RISK_COLORS[risk],
          transition: 'width 1s linear, background .3s ease',
        }} />
      </div>
      <span style={{
        fontSize: '0.75rem',
        color: RISK_COLORS[risk],
        fontWeight: 600,
        whiteSpace: 'nowrap',
      }}>
        {formatSlack(slackSeconds)} slack
      </span>
    </div>
  );
};

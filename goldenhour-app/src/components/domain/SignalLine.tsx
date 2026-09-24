import React from 'react';

interface SignalLineProps {
  className?: string;
  variant?: 'curved' | 'straight';
}

export const SignalLine: React.FC<SignalLineProps> = ({
  className = '',
  variant = 'curved',
}) => {
  return (
    <svg
      className={className}
      viewBox="0 0 400 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{
        width: '100%',
        height: '100%',
        overflow: 'visible',
      }}
    >
      <path
        d={
          variant === 'curved'
            ? 'M 20 60 C 140 10, 260 110, 380 60'
            : 'M 20 60 L 380 60'
        }
        stroke="var(--green)"
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray="6 8"
        style={{
          animation: 'signalDraw 1.3s var(--ease) forwards',
        }}
      />
      {/* Moving pulse dot along the path */}
      <circle r="5" fill="var(--deep)">
        <animateMotion
          path={
            variant === 'curved'
              ? 'M 20 60 C 140 10, 260 110, 380 60'
              : 'M 20 60 L 380 60'
          }
          dur="3s"
          repeatCount="indefinite"
        />
      </circle>
    </svg>
  );
};

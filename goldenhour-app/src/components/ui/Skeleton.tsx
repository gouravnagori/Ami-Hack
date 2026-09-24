import React from 'react';

export const Skeleton: React.FC<{
  width?: string;
  height?: string;
  radius?: string;
  className?: string;
}> = ({ width = '100%', height = '20px', radius = '8px', className = '' }) => (
  <div
    className={className}
    style={{
      width,
      height,
      borderRadius: radius,
      background: `linear-gradient(90deg, var(--soft) 25%, var(--line) 50%, var(--soft) 75%)`,
      backgroundSize: '200% 100%',
      animation: 'shimmer 1.5s ease-in-out infinite',
    }}
    aria-hidden="true"
  />
);

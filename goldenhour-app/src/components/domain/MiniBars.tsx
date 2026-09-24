import React from 'react';

interface MiniBarsProps {
  values?: number[];
  activeIndex?: number;
  height?: number;
}

export const MiniBars: React.FC<MiniBarsProps> = ({
  values = [35, 55, 40, 75, 90, 60, 85, 45, 70, 95, 65, 80],
  activeIndex = 9,
  height = 42,
}) => {
  const max = Math.max(...values, 100);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-end',
        gap: '4px',
        height: `${height}px`,
        width: '100%',
      }}
    >
      {values.map((v, i) => {
        const heightPct = Math.round((v / max) * 100);
        const isActive = i === activeIndex;

        return (
          <div
            key={i}
            style={{
              flex: 1,
              height: `${heightPct}%`,
              background: isActive ? 'var(--green)' : 'var(--bar-idle)',
              borderRadius: '3px 3px 0 0',
              transition: 'height 0.4s var(--ease), background 0.3s ease',
              animation: `barIn 0.6s var(--ease) ${i * 40}ms both`,
            }}
          />
        );
      })}
    </div>
  );
};

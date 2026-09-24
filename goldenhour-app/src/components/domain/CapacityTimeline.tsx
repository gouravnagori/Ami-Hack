import React from 'react';

interface TimelineSlot {
  at: string; // ISO string
  available: number;
}

export const CapacityTimeline: React.FC<{
  projection: TimelineSlot[];
  maxCapacity: number;
}> = ({ projection, maxCapacity }) => {
  return (
    <div style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase' }}>
          6-Hour Projected Availability
        </span>
        <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
          Max {maxCapacity}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px', height: '80px', padding: '6px 0' }}>
        {projection.slice(0, 6).map((slot, i) => {
          const heightPct = maxCapacity > 0 ? Math.max(8, Math.min(100, (slot.available / maxCapacity) * 100)) : 10;
          const timeLabel = new Date(slot.at).toLocaleTimeString([], { hour: 'numeric' });
          const isLow = slot.available < maxCapacity * 0.2;

          return (
            <div
              key={slot.at || i}
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                height: '100%',
                justifyContent: 'flex-end',
              }}
            >
              <div
                title={`${slot.available} portions available at ${timeLabel}`}
                style={{
                  width: '100%',
                  height: `${heightPct}%`,
                  background: isLow ? 'var(--peach)' : 'var(--green)',
                  borderRadius: '4px 4px 0 0',
                  transition: 'height 0.4s var(--ease)',
                  minHeight: '4px',
                }}
              />
              <span style={{ fontSize: '0.68rem', color: 'var(--muted)', marginTop: '4px', whiteSpace: 'nowrap' }}>
                {timeLabel}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

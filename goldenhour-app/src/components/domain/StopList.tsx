import React from 'react';
import type { Stop } from '../../types/api';
import { DietBadge } from './DietBadge';
import { StorageBadge } from './StorageBadge';
import { SlackBar } from './SlackBar';

interface StopListProps {
  stops: Stop[];
  activeStopIndex?: number;
  onSelectStop?: (stop: Stop) => void;
}

export const StopList: React.FC<StopListProps> = ({
  stops,
  activeStopIndex = 0,
  onSelectStop,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {stops.map((stop, idx) => {
        const isCurrent = idx === activeStopIndex;
        const isPast = idx < activeStopIndex;
        const isPickup = stop.type === 'pickup';

        return (
          <div
            key={stop.id}
            onClick={() => onSelectStop && onSelectStop(stop)}
            style={{
              display: 'flex',
              gap: '14px',
              padding: '14px',
              borderRadius: 'var(--r-card-sm)',
              background: isCurrent ? 'var(--white)' : 'var(--paper)',
              border: isCurrent ? '2px solid var(--deep)' : '1px solid var(--line)',
              boxShadow: isCurrent ? 'var(--shadow-soft)' : 'none',
              cursor: onSelectStop ? 'pointer' : 'default',
              transition: 'all 0.2s var(--ease)',
              opacity: isPast ? 0.65 : 1,
            }}
          >
            {/* Seq badge with connecting indicator */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  background: isPast
                    ? 'var(--line)'
                    : isPickup
                    ? 'var(--deep)'
                    : 'var(--green-dark)',
                  color: isPast ? 'var(--muted)' : 'var(--white)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                }}
              >
                {isPast ? '✓' : stop.seq}
              </div>
              <span
                style={{
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  color: isPickup ? 'var(--deep)' : 'var(--green-dark)',
                }}
              >
                {isPickup ? 'Pick' : 'Drop'}
              </span>
            </div>

            {/* Stop content */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                <h5 style={{ fontSize: '0.95rem', fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
                  {stop.place.name}
                </h5>
                <span
                  style={{
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    color: stop.risk === 'critical' ? 'var(--red)' : 'var(--muted)',
                  }}
                >
                  ETA {new Date(stop.planned_arrival).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>

              {stop.place.address && (
                <p style={{ fontSize: '0.8rem', color: 'var(--muted)', margin: '3px 0 6px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {stop.place.address}
                </p>
              )}

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', marginTop: '6px' }}>
                <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--deep)' }}>
                  {stop.portions} portions
                </span>
                <DietBadge diet={stop.diet} />
                <StorageBadge storage={stop.storage} />
                {stop.container_label && (
                  <span
                    style={{
                      fontSize: '0.72rem',
                      fontFamily: 'monospace',
                      background: 'var(--paper)',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      border: '1px solid var(--line)',
                    }}
                  >
                    #{stop.container_label}
                  </span>
                )}
              </div>

              {/* Real-time Slack bar if active */}
              {isCurrent && (
                <div style={{ marginTop: '10px' }}>
                  <SlackBar
                    slackSeconds={stop.slack_seconds}
                    windowTotalSeconds={1800}
                    risk={stop.risk}
                  />
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

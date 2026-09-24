import React from 'react';

export interface StepItem {
  id: string;
  label: string;
  sublabel?: string;
}

const DEFAULT_STEPS: StepItem[] = [
  { id: 'posted', label: 'Posted' },
  { id: 'matched', label: 'Matched' },
  { id: 'driver_assigned', label: 'Driver Picked' },
  { id: 'in_transit', label: 'In Transit' },
  { id: 'delivered', label: 'Delivered' },
];

export const StatusStepper: React.FC<{
  currentStepIndex: number;
  steps?: StepItem[];
  isFallback?: boolean;
}> = ({ currentStepIndex, steps = DEFAULT_STEPS, isFallback = false }) => {
  return (
    <div style={{ width: '100%', margin: '14px 0' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'relative',
        }}
      >
        {/* Track Line behind steps */}
        <div
          style={{
            position: 'absolute',
            top: '15px',
            left: '20px',
            right: '20px',
            height: '3px',
            background: 'var(--line)',
            zIndex: 1,
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${Math.min(100, (currentStepIndex / (steps.length - 1)) * 100)}%`,
              background: isFallback ? 'var(--peach)' : 'var(--green)',
              transition: 'width 0.4s var(--ease)',
            }}
          />
        </div>

        {/* Step nodes */}
        {steps.map((step, idx) => {
          const isDone = idx < currentStepIndex;
          const isCurrent = idx === currentStepIndex;
          return (
            <div
              key={step.id}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                zIndex: 2,
                position: 'relative',
                flex: 1,
              }}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  background: isDone
                    ? 'var(--deep)'
                    : isCurrent
                    ? 'var(--green)'
                    : 'var(--paper)',
                  color: isDone || isCurrent ? 'var(--white)' : 'var(--muted)',
                  border: isCurrent
                    ? '3px solid var(--deep)'
                    : isDone
                    ? 'none'
                    : '2px solid var(--line)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  boxShadow: isCurrent ? '0 0 14px rgba(143,211,90,0.5)' : 'none',
                  animation: isCurrent ? 'nodePulse 2s infinite' : 'none',
                  transition: 'all 0.3s var(--ease)',
                }}
              >
                {isDone ? '✓' : idx + 1}
              </div>
              <span
                style={{
                  marginTop: '8px',
                  fontSize: '0.78rem',
                  fontWeight: isCurrent ? 700 : 500,
                  color: isCurrent ? 'var(--deep)' : isDone ? 'var(--ink)' : 'var(--muted)',
                  textAlign: 'center',
                  lineHeight: 1.2,
                }}
              >
                {step.label}
              </span>
              {step.sublabel && (
                <span
                  style={{
                    fontSize: '0.7rem',
                    color: 'var(--muted)',
                    marginTop: '2px',
                  }}
                >
                  {step.sublabel}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

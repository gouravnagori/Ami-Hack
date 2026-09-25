import React, { useState } from 'react';
import { api } from '../../../lib/api';
import { useUiStore } from '../../../store/ui';
import type { SimScenario, ChaosKind } from '../../../types/api';

// Scenario metadata — display-only, no mock logic
const SCENARIOS: Record<SimScenario, { name: string; description: string }> = {
  normal: { name: 'Normal Operations', description: 'Standard evening surplus flow across corridors.' },
  wedding_night: { name: 'Wedding Night Surge', description: 'High-volume catering surplus from multiple banquet venues.' },
  rush_hour: { name: 'Rush Hour Stress', description: 'Peak traffic congestion with tight delivery windows.' },
};

export const SimulatePanel: React.FC = () => {
  const { addToast } = useUiStore();
  const [currentScenario, setCurrentScenario] = useState<SimScenario>('normal');
  const [loading, setLoading] = useState(false);

  const handleSwitchScenario = async (scenario: SimScenario) => {
    setCurrentScenario(scenario);
    setLoading(true);
    try {
      await api.post('/admin/simulate', { scenario });
      addToast(`Scenario activated: ${SCENARIOS[scenario].name}`, 'success');
    } catch {
      addToast('Failed to activate scenario on backend', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleInjectChaos = async (kind: ChaosKind) => {
    try {
      await api.post('/admin/chaos', { kind });
      addToast(`Chaos Injected: ${kind.replace('_', ' ').toUpperCase()}`, 'warning');
    } catch {
      addToast('Failed to inject chaos on backend', 'error');
    }
  };

  return (
    <div
      style={{
        background: 'var(--white)',
        border: '1px solid var(--line)',
        borderRadius: 'var(--r-card-lg)',
        padding: '20px',
        boxShadow: 'var(--shadow-soft)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <h4 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--deep)', margin: 0 }}>
          🎮 Simulation & Stress Testing
        </h4>
        <span style={{ fontSize: '0.72rem', background: 'var(--soft)', color: 'var(--deep)', padding: '2px 8px', borderRadius: 'var(--r-pill)', fontWeight: 700 }}>
          Active
        </span>
      </div>

      {/* Scenario Buttons */}
      <div style={{ marginBottom: '16px' }}>
        <div style={{ fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '6px' }}>
          Select Traffic & Surplus Pattern:
        </div>
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {(Object.keys(SCENARIOS) as SimScenario[]).map((key) => {
            const sc = SCENARIOS[key];
            const isSelected = currentScenario === key;
            return (
              <button
                key={key}
                type="button"
                onClick={() => handleSwitchScenario(key)}
                disabled={loading}
                style={{
                  padding: '6px 12px',
                  borderRadius: 'var(--r-pill)',
                  fontSize: '0.78rem',
                  fontWeight: isSelected ? 800 : 500,
                  background: isSelected ? 'var(--deep)' : 'var(--paper)',
                  color: isSelected ? 'var(--white)' : 'var(--ink)',
                  border: isSelected ? 'none' : '1px solid var(--line)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                {sc.name.split(' (')[0]}
              </button>
            );
          })}
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '6px', fontStyle: 'italic' }}>
          {SCENARIOS[currentScenario].description}
        </div>
      </div>

      {/* Chaos Injections */}
      <div>
        <div style={{ fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '6px' }}>
          Inject Real-Time Anomalies (Failover Verification):
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
          <button
            type="button"
            onClick={() => handleInjectChaos('driver_drop')}
            style={{
              padding: '8px 4px',
              borderRadius: 'var(--r-card-sm)',
              fontSize: '0.75rem',
              fontWeight: 700,
              background: '#fff5f1',
              color: 'var(--red)',
              border: '1px solid #f5b19d',
            }}
          >
            🛵 Driver Drop
          </button>
          <button
            type="button"
            onClick={() => handleInjectChaos('org_full')}
            style={{
              padding: '8px 4px',
              borderRadius: 'var(--r-card-sm)',
              fontSize: '0.75rem',
              fontWeight: 700,
              background: 'var(--blue-tint)',
              color: 'var(--blue-text)',
              border: '1px solid var(--blue)',
            }}
          >
            🏠 Shelter Full
          </button>
          <button
            type="button"
            onClick={() => handleInjectChaos('traffic_spike')}
            style={{
              padding: '8px 4px',
              borderRadius: 'var(--r-card-sm)',
              fontSize: '0.75rem',
              fontWeight: 700,
              background: 'var(--soft)',
              color: 'var(--deep)',
              border: '1px solid var(--green)',
            }}
          >
            🚦 Traffic Jam
          </button>
        </div>
      </div>
    </div>
  );
};

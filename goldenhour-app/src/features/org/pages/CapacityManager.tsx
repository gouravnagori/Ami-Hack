import React, { useEffect, useState } from 'react';
import { api } from '../../../lib/api';
import { useUiStore } from '../../../store/ui';
import type { CapacitySnapshot, DietType } from '../../../types/api';
import { CapacityTimeline } from '../../../components/domain/CapacityTimeline';
import { Button } from '../../../components/ui/Button';

export const CapacityManager: React.FC = () => {
  const { addToast } = useUiStore();
  const [capacity, setCapacity] = useState<CapacitySnapshot | null>(null);
  const [maxPortions, setMaxPortions] = useState(150);
  const [serviceRate, setServiceRate] = useState(30);
  const [coldMax, setColdMax] = useState(50);
  const [vegOnly, setVegOnly] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .get<CapacitySnapshot>('/api/capacity/current')
      .then((res) => {
        setCapacity(res);
        setMaxPortions(res.max_portions);
        setServiceRate(res.service_rate_per_hour);
        setColdMax(res.cold.max);
        setVegOnly(!res.accepts.diets.includes('non_veg'));
      })
      .catch((err) => console.error(err));
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const diets: DietType[] = vegOnly ? ['veg'] : ['veg', 'egg', 'non_veg'];
      const updated = await api.post<CapacitySnapshot>('/api/capacity', {
        max_portions: maxPortions,
        service_rate_per_hour: serviceRate,
        cold: { max: coldMax, used: capacity?.cold.used || 0 },
        accepts: {
          diets,
          storage: ['ambient', 'hot', 'cold'],
        },
      });
      setCapacity(updated);
      addToast('Shelter capacity limits & policies updated!', 'success');
    } catch {
      addToast('Failed to save settings', 'error');
    } finally {
      setSaving(false);
    }
  };

  if (!capacity) {
    return <div style={{ textAlign: 'center', padding: '60px', color: 'var(--muted)' }}>Loading capacity settings...</div>;
  }

  return (
    <div style={{ maxWidth: '820px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '2rem', color: 'var(--deep)', fontWeight: 800 }}>
          Shelter Capacity & Intake Policies
        </h2>
        <p style={{ color: 'var(--muted)', fontSize: '0.95rem' }}>
          Configure live intake constraints to prevent kitchen overcrowding and enforce dietary standards.
        </p>
      </div>

      <form onSubmit={handleSave}>
        {/* 6-Hour Projection Preview */}
        <div
          style={{
            background: 'var(--white)',
            border: '1px solid var(--line)',
            borderRadius: 'var(--r-card-lg)',
            padding: '24px',
            boxShadow: 'var(--shadow-soft)',
            marginBottom: '24px',
          }}
        >
          <CapacityTimeline projection={capacity.projection} maxCapacity={maxPortions} />
        </div>

        {/* Configuration Parameters */}
        <div
          style={{
            background: 'var(--white)',
            border: '1px solid var(--line)',
            borderRadius: 'var(--r-card-lg)',
            padding: '28px',
            boxShadow: 'var(--shadow-soft)',
            display: 'flex',
            flexDirection: 'column',
            gap: '24px',
            marginBottom: '24px',
          }}
        >
          {/* Max Portions Stepper */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <div>
                <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--deep)' }}>
                  Total Kitchen Holding Limit
                </span>
                <div style={{ fontSize: '0.78rem', color: 'var(--muted)' }}>
                  Maximum meal servings your dining hall can stage at one time
                </div>
              </div>
              <strong style={{ fontSize: '1.3rem', color: 'var(--ink)' }}>{maxPortions} portions</strong>
            </div>
            <input
              type="range"
              min={50}
              max={500}
              step={25}
              value={maxPortions}
              onChange={(e) => setMaxPortions(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--green-dark)' }}
            />
          </div>

          {/* Service Rate Per Hour */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <div>
                <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--deep)' }}>
                  Distribution Rate Per Hour
                </span>
                <div style={{ fontSize: '0.78rem', color: 'var(--muted)' }}>
                  Rate at which beds/patrons consume meals, freeing up slots
                </div>
              </div>
              <strong style={{ fontSize: '1.1rem', color: 'var(--deep)' }}>{serviceRate} meals/hr</strong>
            </div>
            <input
              type="range"
              min={10}
              max={150}
              step={10}
              value={serviceRate}
              onChange={(e) => setServiceRate(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--green-dark)' }}
            />
          </div>

          {/* Cold Storage Capacity */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <div>
                <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--deep)' }}>
                  Refrigerated Storage Slots
                </span>
                <div style={{ fontSize: '0.78rem', color: 'var(--muted)' }}>
                  Dedicated refrigeration space for perishable items and desserts
                </div>
              </div>
              <strong style={{ fontSize: '1.1rem', color: 'var(--blue-text)' }}>{coldMax} slots</strong>
            </div>
            <input
              type="range"
              min={0}
              max={200}
              step={10}
              value={coldMax}
              onChange={(e) => setColdMax(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--blue)' }}
            />
          </div>

          {/* Dietary Restrictions Switch */}
          <div
            style={{
              padding: '16px',
              borderRadius: 'var(--r-card-sm)',
              background: 'var(--paper)',
              border: '1px solid var(--line)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--deep)' }}>
                Strict Pure-Veg Intake Only
              </span>
              <div style={{ fontSize: '0.78rem', color: 'var(--muted)' }}>
                Automatically reject any offers containing egg or meat
              </div>
            </div>
            <button
              type="button"
              onClick={() => setVegOnly(!vegOnly)}
              style={{
                padding: '6px 14px',
                borderRadius: 'var(--r-pill)',
                fontSize: '0.85rem',
                fontWeight: 700,
                background: vegOnly ? 'var(--green)' : 'var(--line)',
                color: 'var(--deep)',
                border: 'none',
              }}
            >
              {vegOnly ? '🟢 Pure Veg Active' : '⚪ All Foods Accepted'}
            </button>
          </div>
        </div>

        <Button type="submit" variant="primary" size="lg" block arrow disabled={saving}>
          {saving ? 'Saving...' : 'Save Capacity Configuration'}
        </Button>
      </form>
    </div>
  );
};

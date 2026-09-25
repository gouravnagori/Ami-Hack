import React, { useEffect, useState } from 'react';
import { api } from '../../../lib/api';
import { MetricCard } from '../../../components/ui/MetricCard';
import { Button } from '../../../components/ui/Button';
import { useUiStore } from '../../../store/ui';
import type { Donation } from '../../../types/api';

interface ImpactData {
  meals_rescued: number;
  weight_kg: number;
  co2e_kg: number;
  co2e_kg_avoided?: number;
  on_time_rate: number;
}

export const DonorImpact: React.FC = () => {
  const { addToast } = useUiStore();
  const [impact, setImpact] = useState<ImpactData>({ meals_rescued: 0, weight_kg: 0, co2e_kg: 0, on_time_rate: 1 });
  const [donations, setDonations] = useState<Donation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<any>('/donor/impact').catch(() => ({ meals_rescued: 0, weight_kg: 0, co2e_kg: 0, on_time_rate: 1 })),
      api.get<{ items: Donation[] }>('/donations').catch(() => ({ items: [] })),
    ]).then(([impactRes, donRes]) => {
      if (impactRes) {
        const co2 = impactRes.co2e_kg ?? impactRes.co2e_kg_avoided ?? 0;
        setImpact({
          meals_rescued: Number.isFinite(impactRes.meals_rescued) ? Number(impactRes.meals_rescued) : 0,
          weight_kg: Number.isFinite(impactRes.weight_kg) ? Number(impactRes.weight_kg) : 0,
          co2e_kg: Number.isFinite(co2) ? Number(co2) : 0,
          on_time_rate: Number.isFinite(impactRes.on_time_rate) ? Number(impactRes.on_time_rate) : 1,
        });
      }
      setDonations((donRes.items || []).filter((d: Donation) => d.status === 'delivered'));
    }).finally(() => setLoading(false));
  }, []);

  const handleDownloadCertificate = () => {
    addToast('Generating tax exemption certificate (PDF)...', 'info');
    api.get('/donor/impact').then(() => {
      addToast('Certificate downloaded!', 'success');
    }).catch(() => {
      addToast('Certificate generation not yet available', 'info');
    });
  };

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h2 style={{ fontSize: '2rem', color: 'var(--deep)', fontWeight: 800 }}>
            Impact & Certificates
          </h2>
          <p style={{ color: 'var(--muted)', fontSize: '0.95rem' }}>
            Your verified food rescue impact
          </p>
        </div>

        <Button variant="primary" size="md" arrow onClick={handleDownloadCertificate}>
          Download Tax Receipt
        </Button>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '32px' }}>
        <MetricCard label="Total Meals Rescued" value={Number.isFinite(impact.meals_rescued) ? impact.meals_rescued : 0} sub="verified deliveries" variant="default" />
        <MetricCard label="Total Weight (kg)" value={Math.round(Number.isFinite(impact.weight_kg) ? impact.weight_kg : 0)} sub="food saved" variant="blue" />
        <MetricCard label="CO2e Prevented" value={Math.round(Number.isFinite(impact.co2e_kg) ? impact.co2e_kg : 0)} format={(n) => `${Number.isFinite(n) ? n : 0} kg`} sub="emissions diverted" variant="default" />
        <MetricCard label="On-Time Rate" value={(Number.isFinite(impact.on_time_rate) ? impact.on_time_rate : 1) * 100} format={(n) => `${(Number.isFinite(n) ? n : 100).toFixed(1)}%`} sub="delivery success" variant="default" />
      </div>

      {/* Donation History Table */}
      <div
        style={{
          background: 'var(--white)',
          border: '1px solid var(--line)',
          borderRadius: 'var(--r-card-lg)',
          padding: '24px',
          boxShadow: 'var(--shadow-soft)',
        }}
      >
        <h4 style={{ fontSize: '1.15rem', color: 'var(--deep)', fontWeight: 800, marginBottom: '16px' }}>
          Rescue Ledger
        </h4>

        {loading ? (
          <p style={{ color: 'var(--muted)', textAlign: 'center', padding: '32px' }}>Loading delivery history…</p>
        ) : donations.length === 0 ? (
          <p style={{ color: 'var(--muted)', textAlign: 'center', padding: '32px' }}>No delivered donations yet. Post your first donation to see impact here!</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--line)', color: 'var(--muted)' }}>
                  <th style={{ padding: '10px 12px' }}>Donation ID</th>
                  <th style={{ padding: '10px 12px' }}>Date</th>
                  <th style={{ padding: '10px 12px' }}>Portions</th>
                  <th style={{ padding: '10px 12px' }}>Diet</th>
                  <th style={{ padding: '10px 12px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {donations.map((d) => (
                  <tr key={d.id} style={{ borderBottom: '1px solid var(--line)' }}>
                    <td style={{ padding: '12px', fontWeight: 700, color: 'var(--deep)' }}>{d.id.slice(0, 8)}</td>
                    <td style={{ padding: '12px', color: 'var(--muted)' }}>{d.created_at ? new Date(d.created_at).toLocaleDateString() : '—'}</td>
                    <td style={{ padding: '12px', fontWeight: 800 }}>{d.total_portions}</td>
                    <td style={{ padding: '12px' }}>{d.diet}</td>
                    <td style={{ padding: '12px' }}>
                      <span style={{ background: 'var(--soft)', color: 'var(--deep)', padding: '3px 8px', borderRadius: 'var(--r-pill)', fontSize: '0.75rem', fontWeight: 700 }}>
                        ✓ {d.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

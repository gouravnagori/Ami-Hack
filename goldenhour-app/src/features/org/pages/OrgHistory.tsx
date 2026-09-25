import React, { useState, useEffect } from 'react';
import { useUiStore } from '../../../store/ui';
import { api } from '../../../lib/api';
import { Button } from '../../../components/ui/Button';

interface DeliveryRecord {
  id: string;
  created_at: string;
  total_portions: number;
  diet: string;
  status: string;
  donor_id: string;
}

export const OrgHistory: React.FC = () => {
  const { addToast } = useUiStore();
  const [driverOtp, setDriverOtp] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [history, setHistory] = useState<DeliveryRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch received allocations/offers for this org
    api.get<{ items: DeliveryRecord[] }>('/offers')
      .then((res) => setHistory(res.items || []))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, []);

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!driverOtp.trim()) return;
    setVerifying(true);
    try {
      // Real OTP verification would go to backend
      addToast(`OTP ${driverOtp} submitted for verification.`, 'info');
      setDriverOtp('');
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '2rem', color: 'var(--deep)', fontWeight: 800 }}>
          Intake History & Gate Verification
        </h2>
        <p style={{ color: 'var(--muted)', fontSize: '0.95rem' }}>
          Verify incoming delivery OTPs and inspect past meal distributions.
        </p>
      </div>

      {/* Driver Handshake Verification Box */}
      <div
        style={{
          background: 'var(--white)',
          border: '2px solid var(--green)',
          borderRadius: 'var(--r-card-lg)',
          padding: '24px 28px',
          boxShadow: 'var(--shadow-soft)',
          marginBottom: '28px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
          <h4 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--deep)', margin: 0 }}>
            🤝 Driver Gate Handshake
          </h4>
          <span style={{ fontSize: '0.72rem', background: 'var(--soft)', color: 'var(--deep)', padding: '2px 8px', borderRadius: 'var(--r-pill)', fontWeight: 700 }}>
            Waiting
          </span>
        </div>
        <form onSubmit={handleVerifyOtp} style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <input
            type="text"
            value={driverOtp}
            onChange={(e) => setDriverOtp(e.target.value)}
            placeholder="Enter driver's 4-digit OTP"
            maxLength={4}
            style={{
              flex: 1,
              padding: '14px 16px',
              borderRadius: 'var(--r-card-sm)',
              border: '1px solid var(--line)',
              fontSize: '1.2rem',
              fontWeight: 800,
              letterSpacing: '6px',
              textAlign: 'center',
              background: 'var(--paper)',
            }}
          />
          <Button variant="primary" size="md" disabled={verifying || !driverOtp.trim()}>
            {verifying ? 'Verifying...' : 'Verify OTP'}
          </Button>
        </form>
      </div>

      {/* History Table */}
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
          Recent Offers & Deliveries
        </h4>

        {loading ? (
          <p style={{ color: 'var(--muted)', textAlign: 'center', padding: '32px' }}>Loading history…</p>
        ) : history.length === 0 ? (
          <p style={{ color: 'var(--muted)', textAlign: 'center', padding: '32px' }}>No offers received yet. Incoming offers will appear here.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--line)', color: 'var(--muted)' }}>
                  <th style={{ padding: '10px 12px' }}>ID</th>
                  <th style={{ padding: '10px 12px' }}>Date</th>
                  <th style={{ padding: '10px 12px' }}>Portions</th>
                  <th style={{ padding: '10px 12px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {history.map((row) => (
                  <tr key={row.id} style={{ borderBottom: '1px solid var(--line)' }}>
                    <td style={{ padding: '12px', fontWeight: 700, color: 'var(--deep)' }}>{row.id.slice(0, 8)}</td>
                    <td style={{ padding: '12px', color: 'var(--muted)' }}>{row.created_at ? new Date(row.created_at).toLocaleDateString() : '—'}</td>
                    <td style={{ padding: '12px', fontWeight: 800 }}>{row.total_portions || '—'}</td>
                    <td style={{ padding: '12px' }}>
                      <span style={{ background: 'var(--soft)', color: 'var(--deep)', padding: '3px 8px', borderRadius: 'var(--r-pill)', fontSize: '0.75rem', fontWeight: 700 }}>
                        {row.status || 'pending'}
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

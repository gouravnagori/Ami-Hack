import React, { useState } from 'react';
import { useUiStore } from '../../../store/ui';
import { Button } from '../../../components/ui/Button';

export const OrgHistory: React.FC = () => {
  const { addToast } = useUiStore();
  const [driverOtp, setDriverOtp] = useState('');
  const [verifying, setVerifying] = useState(false);

  const history = [
    { id: 'DEL-441', date: 'Today, 1:45 PM', donor: 'Spice Route Kitchen', portions: 45, driver: 'Rajesh K. (E-Rickshaw)', temp: '68°C (Pass)', status: 'Distributed' },
    { id: 'DEL-439', date: 'Yesterday, 8:20 PM', donor: 'Jaipur Marriott Banquet', portions: 120, driver: 'Vikram S. (Van)', temp: '71°C (Pass)', status: 'Distributed' },
    { id: 'DEL-435', date: '21 Sep 2026', donor: 'LMB Sweet Shop', portions: 35, driver: 'Amit S. (Scooter)', temp: 'Ambient (Pass)', status: 'Distributed' },
    { id: 'DEL-430', date: '19 Sep 2026', donor: 'Kanha Sweets Vaishali', portions: 60, driver: 'Rajesh K. (E-Rickshaw)', temp: '66°C (Pass)', status: 'Distributed' },
  ];

  const handleVerifyOtp = (e: React.FormEvent) => {
    e.preventDefault();
    if (!driverOtp.trim()) return;
    setVerifying(true);
    setTimeout(() => {
      setVerifying(false);
      setDriverOtp('');
      addToast(`OTP ${driverOtp} Verified! Delivery #DEL-442 confirmed & marked complete.`, 'success');
    }, 800);
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
          <div>
            <h4 style={{ fontSize: '1.2rem', color: 'var(--deep)', fontWeight: 800, margin: 0 }}>
              Driver Gate Handshake
            </h4>
            <div style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
              Ask the arriving driver for their 4-digit drop verification code
            </div>
          </div>
          <span style={{ background: 'var(--soft)', color: 'var(--deep)', padding: '4px 10px', borderRadius: 'var(--r-pill)', fontSize: '0.75rem', fontWeight: 800 }}>
            FSSAI COMPLIANT
          </span>
        </div>

        <form onSubmit={handleVerifyOtp} style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            type="text"
            maxLength={6}
            value={driverOtp}
            onChange={(e) => setDriverOtp(e.target.value)}
            placeholder="Enter 4-digit code (e.g. 4829)"
            style={{
              padding: '12px 16px',
              borderRadius: 'var(--r-card-sm)',
              border: '1px solid var(--line)',
              background: 'var(--paper)',
              fontSize: '1.1rem',
              fontWeight: 700,
              letterSpacing: '2px',
              minWidth: '220px',
              outline: 'none',
            }}
          />
          <Button type="submit" variant="primary" size="md" arrow disabled={verifying || !driverOtp}>
            {verifying ? 'Verifying...' : 'Verify Dropoff'}
          </Button>
        </form>
      </div>

      {/* Past Deliveries Table */}
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
          Completed Deliveries
        </h4>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--line)', color: 'var(--muted)' }}>
                <th style={{ padding: '10px 12px' }}>Intake ID</th>
                <th style={{ padding: '10px 12px' }}>Timestamp</th>
                <th style={{ padding: '10px 12px' }}>Donor Source</th>
                <th style={{ padding: '10px 12px' }}>Portions</th>
                <th style={{ padding: '10px 12px' }}>Driver</th>
                <th style={{ padding: '10px 12px' }}>Safety Check</th>
                <th style={{ padding: '10px 12px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {history.map((row) => (
                <tr key={row.id} style={{ borderBottom: '1px solid var(--line)' }}>
                  <td style={{ padding: '12px', fontWeight: 700, color: 'var(--deep)' }}>{row.id}</td>
                  <td style={{ padding: '12px', color: 'var(--muted)' }}>{row.date}</td>
                  <td style={{ padding: '12px', fontWeight: 600 }}>{row.donor}</td>
                  <td style={{ padding: '12px', fontWeight: 800 }}>{row.portions}</td>
                  <td style={{ padding: '12px', color: 'var(--muted)' }}>{row.driver}</td>
                  <td style={{ padding: '12px', color: 'var(--green-dark)', fontWeight: 700 }}>{row.temp}</td>
                  <td style={{ padding: '12px' }}>
                    <span style={{ background: 'var(--soft)', color: 'var(--deep)', padding: '3px 8px', borderRadius: 'var(--r-pill)', fontSize: '0.75rem', fontWeight: 700 }}>
                      ✓ {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

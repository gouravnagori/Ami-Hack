import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Toggle } from '../../../components/ui/Toggle';
import { Button } from '../../../components/ui/Button';
import { MetricCard } from '../../../components/ui/MetricCard';
import { api } from '../../../lib/api';

export const DriverHome: React.FC = () => {
  const navigate = useNavigate();
  const [online, setOnline] = useState(false);
  const [driverStatus, setDriverStatus] = useState<{ shift_hours: number; completed_today: number }>({ shift_hours: 0, completed_today: 0 });

  useEffect(() => {
    api.get<{ status: string; shift_hours: number; completed_today: number }>('/driver/status')
      .then((res) => {
        setOnline(res.status === 'available' || res.status === 'on_task');
        setDriverStatus({ shift_hours: res.shift_hours, completed_today: res.completed_today });
      })
      .catch(() => {});
  }, []);

  const handleToggleStatus = (checked: boolean) => {
    setOnline(checked);
    api.post('/driver/status', { status: checked ? 'available' : 'offline' }).catch(() => {});
  };

  return (
    <div>
      {/* Online / Duty Status Card */}
      <div
        style={{
          background: 'var(--white)',
          border: '1px solid var(--line)',
          borderRadius: 'var(--r-card-lg)',
          padding: '20px',
          boxShadow: 'var(--shadow-soft)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
        }}
      >
        <div>
          <h4 style={{ fontSize: '1.15rem', color: 'var(--deep)', fontWeight: 800, margin: '0 0 2px' }}>
            {online ? 'Ready for Rescues' : 'Offline / On Break'}
          </h4>
          <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
            {online ? 'Receiving priority orders in C-Scheme' : 'You are not visible to ops matching'}
          </span>
        </div>

        <Toggle checked={online} onChange={handleToggleStatus} />
      </div>

      {/* Today's Shift Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
        <MetricCard label="Shift Hours" value={driverStatus.shift_hours} format={(n) => `${n.toFixed(1)}h`} sub="today" variant="default" />
        <MetricCard label="Routes Completed" value={driverStatus.completed_today} sub="today" variant="blue" />
      </div>

      {/* Active Route CTA Banner */}
      <div
        style={{
          background: 'var(--deep)',
          color: 'var(--white)',
          borderRadius: 'var(--r-card-lg)',
          padding: '22px',
          boxShadow: 'var(--shadow)',
          marginBottom: '20px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '0.74rem', background: 'var(--green)', color: 'var(--deep)', padding: '3px 8px', borderRadius: 'var(--r-pill)', fontWeight: 800 }}>
            ASSIGNED RUN #JPR-101
          </span>
          <span style={{ fontSize: '0.82rem', color: 'var(--green)', fontWeight: 700 }}>
            ● In Progress
          </span>
        </div>

        <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: '6px 0' }}>
          Spice Route ➔ Asha Shelter
        </h3>
        <p style={{ fontSize: '0.84rem', color: 'var(--on-dark-muted)', margin: '0 0 16px' }}>
          2 stops • 5.2 km via JLN Marg • 45 hot veg meals
        </p>

        <Button
          variant="primary"
          size="lg"
          block
          arrow
          onClick={() => navigate('/driver/active')}
        >
          Open Turn-by-Turn Navigation
        </Button>
      </div>

      {/* Jaipur Corridor Hotspots */}
      <div
        style={{
          background: 'var(--white)',
          border: '1px solid var(--line)',
          borderRadius: 'var(--r-card-lg)',
          padding: '20px',
          boxShadow: 'var(--shadow-soft)',
        }}
      >
        <h5 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--deep)', margin: '0 0 12px' }}>
          🔥 Jaipur Surplus Corridors (High Demand)
        </h5>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.84rem' }}>
            <span>📍 C-Scheme & MI Road</span>
            <span style={{ color: 'var(--green-dark)', fontWeight: 700 }}>3 Active Kitchens</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.84rem' }}>
            <span>📍 Tonk Road Banquets</span>
            <span style={{ color: 'var(--green-dark)', fontWeight: 700 }}>2 Wedding Halls Free</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.84rem' }}>
            <span>📍 Malviya Nagar Shelters</span>
            <span style={{ color: 'var(--blue-text)', fontWeight: 700 }}>120 Bed Capacity Open</span>
          </div>
        </div>
      </div>
    </div>
  );
};

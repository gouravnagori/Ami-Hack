import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../../lib/api';
import type { Donation } from '../../../types/api';
import { MetricCard } from '../../../components/ui/MetricCard';
import { Button } from '../../../components/ui/Button';
import { CountdownRing } from '../../../components/domain/CountdownRing';
import { DietBadge } from '../../../components/domain/DietBadge';
import { StorageBadge } from '../../../components/domain/StorageBadge';
import { StatusStepper } from '../../../components/domain/StatusStepper';

export const DonorHome: React.FC = () => {
  const navigate = useNavigate();
  const [donations, setDonations] = useState<Donation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<{ items: Donation[] }>('/api/donations')
      .then((res) => setDonations(res.items))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      {/* Metrics Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '16px',
          marginBottom: '28px',
        }}
      >
        <MetricCard label="Portions Rescued This Month" value={1420} sub="from 28 donations" variant="default" />
        <MetricCard label="Active Posts in Flight" value={donations.length} sub="Jaipur Corridor" variant="blue" />
        <MetricCard label="CO2e Emissions Diverted" value={1240} format={(n) => `${n} kg`} sub="Zero waste tier" variant="default" />
        <MetricCard label="On-Time Delivery Success" value={98.5} format={(n) => `${n}%`} sub="Avg slack 42 mins" variant="default" />
      </div>

      {/* Quick Action Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, var(--white) 0%, #f4fbf0 100%)',
          border: '1px solid var(--green)',
          borderRadius: 'var(--r-card-lg)',
          padding: '24px 28px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          marginBottom: '32px',
          boxShadow: 'var(--shadow-soft)',
        }}
      >
        <div>
          <span style={{ background: 'var(--soft)', color: 'var(--deep)', padding: '3px 8px', borderRadius: 'var(--r-pill)', fontSize: '0.74rem', fontWeight: 800 }}>
            ⚡ NEW SURPLUS
          </span>
          <h3 style={{ fontSize: '1.4rem', color: 'var(--deep)', margin: '8px 0 4px', fontWeight: 800 }}>
            Have surplus food from today's lunch or event?
          </h3>
          <p style={{ color: 'var(--muted)', fontSize: '0.9rem', margin: 0 }}>
            Post in one sentence. We match with a nearby shelter and assign an e-rickshaw or bike in under 3 minutes.
          </p>
        </div>

        <Button variant="primary" size="lg" arrow onClick={() => navigate('/donor/new')}>
          Quick Post (AI)
        </Button>
      </div>

      {/* Active Donations Section */}
      <div style={{ marginBottom: '20px' }}>
        <h4 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--deep)', marginBottom: '14px' }}>
          Active Food Posts ({donations.length})
        </h4>

        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--muted)' }}>
            Loading active donations...
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {donations.map((donation) => {
              const allocation = donation.allocations[0];
              return (
                <div
                  key={donation.id}
                  onClick={() => navigate(`/donor/${donation.id}`)}
                  style={{
                    background: 'var(--white)',
                    border: '1px solid var(--line)',
                    borderRadius: 'var(--r-card-lg)',
                    padding: '22px 24px',
                    boxShadow: 'var(--shadow-soft)',
                    cursor: 'pointer',
                    transition: 'all 0.25s var(--ease)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', flexWrap: 'wrap' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '6px' }}>
                        <span style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--ink)' }}>
                          {donation.total_portions} Portions
                        </span>
                        <DietBadge diet={donation.diet} />
                        <StorageBadge storage={donation.storage} />
                        <span
                          style={{
                            fontSize: '0.74rem',
                            fontWeight: 700,
                            padding: '3px 8px',
                            borderRadius: 'var(--r-pill)',
                            background: donation.status === 'in_transit' ? 'var(--blue-tint)' : 'var(--soft)',
                            color: donation.status === 'in_transit' ? 'var(--blue-text)' : 'var(--deep)',
                          }}
                        >
                          {donation.status.toUpperCase()}
                        </span>
                      </div>

                      <div style={{ fontSize: '0.88rem', color: 'var(--muted)', margin: '4px 0' }}>
                        {donation.items.map((i) => i.name).join(' • ')}
                      </div>

                      <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                        📍 {donation.pickup.address}
                      </div>
                    </div>

                    {/* Countdown Ring */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '0.72rem', color: 'var(--muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                          Safe-Until Slack
                        </div>
                        <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--deep)' }}>
                          {donation.risk.toUpperCase()}
                        </div>
                      </div>
                      <CountdownRing
                        deadline={donation.safe_until}
                        size="md"
                        initialSeconds={7200}
                      />
                    </div>
                  </div>

                  {/* Stepper showing progress */}
                  <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--line)' }}>
                    <StatusStepper
                      currentStepIndex={
                        donation.status === 'posted'
                          ? 0
                          : donation.status === 'matching'
                          ? 1
                          : donation.status === 'in_transit'
                          ? 3
                          : donation.status === 'delivered'
                          ? 4
                          : 2
                      }
                    />
                  </div>

                  {/* Allocation summary footer */}
                  {allocation && (
                    <div
                      style={{
                        marginTop: '12px',
                        background: 'var(--paper)',
                        padding: '10px 14px',
                        borderRadius: 'var(--r-card-sm)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        fontSize: '0.82rem',
                        flexWrap: 'wrap',
                        gap: '8px',
                      }}
                    >
                      <span>
                        🏠 Matched with: <strong>{allocation.recipient.name}</strong>
                      </span>
                      {allocation.driver && (
                        <span>
                          🛵 Driver: <strong>{allocation.driver.name}</strong> ({allocation.driver.vehicle})
                        </span>
                      )}
                      {allocation.pickup_otp && (
                        <span style={{ background: 'var(--deep)', color: 'var(--white)', padding: '2px 8px', borderRadius: '4px', fontWeight: 700 }}>
                          Pickup OTP: {allocation.pickup_otp}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

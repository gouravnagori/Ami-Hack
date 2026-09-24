import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../../../lib/api';
import type { Donation } from '../../../types/api';
import { CountdownRing } from '../../../components/domain/CountdownRing';
import { DietBadge } from '../../../components/domain/DietBadge';
import { StorageBadge } from '../../../components/domain/StorageBadge';
import { StatusStepper } from '../../../components/domain/StatusStepper';
import { RouteMap } from '../../../components/domain/RouteMap';
import { Button } from '../../../components/ui/Button';

export const DonationDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [donation, setDonation] = useState<Donation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    api
      .get<Donation>(`/api/donations/${id}`)
      .then(setDonation)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '60px', color: 'var(--muted)' }}>Loading donation details...</div>;
  }

  if (!donation) {
    return (
      <div style={{ textAlign: 'center', padding: '60px' }}>
        <h3>Donation not found</h3>
        <Button variant="primary" size="md" onClick={() => navigate('/donor')} style={{ marginTop: '16px' }}>
          Back to Dashboard
        </Button>
      </div>
    );
  }

  const alloc = donation.allocations[0];

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto' }}>
      {/* Top Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <button
          type="button"
          onClick={() => navigate('/donor')}
          style={{ fontSize: '0.88rem', color: 'var(--muted)', fontWeight: 600 }}
        >
          ← Back to All Posts
        </button>
        <span
          style={{
            fontSize: '0.78rem',
            fontWeight: 800,
            textTransform: 'uppercase',
            padding: '4px 10px',
            borderRadius: 'var(--r-pill)',
            background: 'var(--soft)',
            color: 'var(--deep)',
          }}
        >
          ID: {donation.id}
        </span>
      </div>

      {/* Main Countdown & Overview Card */}
      <div
        style={{
          background: 'var(--white)',
          border: '1px solid var(--line)',
          borderRadius: 'var(--r-card-lg)',
          padding: '30px',
          boxShadow: 'var(--shadow)',
          marginBottom: '24px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '20px', flexWrap: 'wrap' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <h2 style={{ fontSize: '2rem', color: 'var(--ink)', fontWeight: 800, margin: 0 }}>
                {donation.total_portions} Portions
              </h2>
              <DietBadge diet={donation.diet} />
              <StorageBadge storage={donation.storage} />
            </div>

            <div style={{ fontSize: '1rem', color: 'var(--muted)', marginBottom: '8px' }}>
              {donation.items.map((i) => i.name).join(' • ')}
            </div>

            <div style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
              📍 Pickup: <strong>{donation.pickup.address}</strong>
            </div>
            {donation.notes && (
              <div style={{ fontSize: '0.82rem', color: 'var(--muted)', marginTop: '4px', fontStyle: 'italic' }}>
                Note: {donation.notes}
              </div>
            )}
          </div>

          {/* Large Countdown Ring */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
            <CountdownRing
              deadline={donation.safe_until}
              size="lg"
              initialSeconds={7200}
            />
            <span style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: '8px', fontWeight: 600 }}>
              Safe Spoilage Slack
            </span>
          </div>
        </div>

        {/* Progress Stepper */}
        <div style={{ marginTop: '28px', paddingTop: '20px', borderTop: '1px solid var(--line)' }}>
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
      </div>

      {/* Matched Details Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* Recipient Card */}
        {alloc ? (
          <div
            style={{
              background: 'var(--white)',
              border: '1px solid var(--line)',
              borderRadius: 'var(--r-card-lg)',
              padding: '24px',
              boxShadow: 'var(--shadow-soft)',
            }}
          >
            <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--blue-text)', textTransform: 'uppercase', marginBottom: '6px' }}>
              Matched Recipient
            </div>
            <h4 style={{ fontSize: '1.25rem', color: 'var(--deep)', fontWeight: 800, margin: '0 0 6px' }}>
              {alloc.recipient.name}
            </h4>
            <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '14px' }}>
              {alloc.recipient.geo.address}
            </div>
            <div style={{ fontSize: '0.82rem', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span>📦 Allocated: <strong>{alloc.portions} portions</strong></span>
              <span>🏷 Container Tag: <strong>#{alloc.container_label}</strong></span>
              <span>⏱ Expected Delivery: <strong>{alloc.predicted_delivery ? new Date(alloc.predicted_delivery).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '45 mins'}</strong></span>
            </div>
          </div>
        ) : null}

        {/* Driver & OTP Card */}
        {alloc && alloc.driver ? (
          <div
            style={{
              background: 'var(--deep)',
              color: 'var(--white)',
              borderRadius: 'var(--r-card-lg)',
              padding: '24px',
              boxShadow: 'var(--shadow-soft)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--green)', textTransform: 'uppercase', marginBottom: '6px' }}>
                Assigned Delivery Partner
              </div>
              <h4 style={{ fontSize: '1.25rem', color: 'var(--white)', fontWeight: 800, margin: '0 0 4px' }}>
                {alloc.driver.name}
              </h4>
              <div style={{ fontSize: '0.85rem', color: 'var(--on-dark-muted)' }}>
                Vehicle: {alloc.driver.vehicle.toUpperCase()} • {alloc.driver.phone_masked}
              </div>
            </div>

            {/* OTP Handshake Box */}
            <div
              style={{
                marginTop: '18px',
                background: 'rgba(255, 255, 255, 0.1)',
                padding: '12px 16px',
                borderRadius: 'var(--r-card-sm)',
                border: '1px dashed var(--green)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ fontSize: '0.7rem', color: 'var(--on-dark-muted)', textTransform: 'uppercase' }}>
                  Handover Verification OTP
                </div>
                <div style={{ fontSize: '1.4rem', fontWeight: 900, color: 'var(--green)', letterSpacing: '2px' }}>
                  {alloc.pickup_otp || '4829'}
                </div>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--on-dark-muted)', maxWidth: '120px', textAlign: 'right' }}>
                Give to driver upon container handoff
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {/* Live Route Map */}
      <div
        style={{
          background: 'var(--white)',
          border: '1px solid var(--line)',
          borderRadius: 'var(--r-card-lg)',
          padding: '24px',
          boxShadow: 'var(--shadow-soft)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h4 style={{ fontSize: '1.1rem', color: 'var(--deep)', fontWeight: 800, margin: 0 }}>
            Live Jaipur Corridor Route
          </h4>
          <span style={{ fontSize: '0.78rem', color: 'var(--green-dark)', fontWeight: 700 }}>
            ● Satellite & OSRM Telemetry
          </span>
        </div>

        <RouteMap
          markers={[
            { id: '1', type: 'donor', name: donation.pickup.address || 'Donor Pickup', geo: donation.pickup },
            { id: '2', type: 'recipient', name: alloc ? alloc.recipient.name : 'Recipient', geo: alloc ? alloc.recipient.geo : { lat: 26.8580, lng: 75.8150 } },
          ]}
          height="320px"
        />
      </div>
    </div>
  );
};

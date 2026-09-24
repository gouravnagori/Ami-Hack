import React, { useEffect, useState } from 'react';
import { api } from '../../../lib/api';
import { useUiStore } from '../../../store/ui';
import type { CapacitySnapshot, Offer } from '../../../types/api';
import { CapacityGauge } from '../../../components/domain/CapacityGauge';
import { OfferCard } from '../../../components/domain/OfferCard';
import { Toggle } from '../../../components/ui/Toggle';

export const OrgHome: React.FC = () => {
  const { addToast } = useUiStore();
  const [capacity, setCapacity] = useState<CapacitySnapshot | null>(null);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<CapacitySnapshot>('/api/capacity/current'),
      api.get<{ items: Offer[] }>('/api/offers'),
    ])
      .then(([capRes, offRes]) => {
        setCapacity(capRes);
        setOffers(offRes.items.filter((o) => o.kind === 'recipient'));
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const handleToggleIntake = async (checked: boolean) => {
    if (!capacity) return;
    try {
      const updated = await api.post<CapacitySnapshot>('/api/capacity', { is_open: checked });
      setCapacity(updated);
      addToast(checked ? 'Intake active: Accepting donation offers' : 'Intake paused: No new offers will arrive', 'info');
    } catch {
      addToast('Failed to toggle intake', 'error');
    }
  };

  const handleAcceptOffer = async (offerId: string) => {
    try {
      await api.post(`/api/offers/${offerId}/accept`);
      setOffers((prev) => prev.filter((o) => o.id !== offerId));
      addToast('Offer accepted! Driver dispatch locked.', 'success');
      // Update local committed count
      if (capacity) {
        setCapacity({
          ...capacity,
          available_now: Math.max(0, capacity.available_now - 45),
          committed_portions: capacity.committed_portions + 45,
        });
      }
    } catch {
      addToast('Failed to accept offer', 'error');
    }
  };

  const handleDeclineOffer = async (offerId: string, reason?: string) => {
    try {
      await api.post(`/api/offers/${offerId}/decline`, { reason });
      setOffers((prev) => prev.filter((o) => o.id !== offerId));
      addToast(`Offer declined (${reason || 'capacity'}). Rerouting to fallback shelter.`, 'info');
    } catch {
      addToast('Failed to decline offer', 'error');
    }
  };

  if (loading || !capacity) {
    return <div style={{ textAlign: 'center', padding: '60px', color: 'var(--muted)' }}>Loading shelter intake...</div>;
  }

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto' }}>
      {/* Top Controls Banner */}
      <div
        style={{
          background: 'var(--white)',
          border: '1px solid var(--line)',
          borderRadius: 'var(--r-card-lg)',
          padding: '24px 28px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '20px',
          boxShadow: 'var(--shadow-soft)',
          marginBottom: '28px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px', flexWrap: 'wrap' }}>
          <CapacityGauge
            available={capacity.available_now}
            max={capacity.max_portions}
            committed={capacity.committed_portions}
            size="sm"
          />

          <div>
            <h3 style={{ fontSize: '1.4rem', color: 'var(--deep)', fontWeight: 800, margin: '0 0 6px' }}>
              Shelter Meal Intake Status
            </h3>
            <p style={{ color: 'var(--muted)', fontSize: '0.88rem', margin: 0 }}>
              {capacity.is_open ? 'Accepting donations automatically' : 'Intake paused • Kitchen currently full'}
            </p>
            <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
              <span style={{ fontSize: '0.78rem', background: 'var(--soft)', color: 'var(--deep)', padding: '3px 8px', borderRadius: 'var(--r-pill)', fontWeight: 700 }}>
                🟢 Pure Veg
              </span>
              <span style={{ fontSize: '0.78rem', background: '#fff5f1', color: 'var(--red)', padding: '3px 8px', borderRadius: 'var(--r-pill)', fontWeight: 700 }}>
                ♨️ Hot Holding: 80 max
              </span>
            </div>
          </div>
        </div>

        {/* Global Pause Switch */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '0.9rem', fontWeight: 700, color: capacity.is_open ? 'var(--green-dark)' : 'var(--muted)' }}>
            {capacity.is_open ? 'INTAKE ACTIVE' : 'PAUSED'}
          </span>
          <Toggle
            checked={capacity.is_open}
            onChange={handleToggleIntake}
            label="Toggle intake"
          />
        </div>
      </div>

      {/* Main Grid: Pending Offers + Inbound Deliveries */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
        {/* Pending Offers Column */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h4 style={{ fontSize: '1.2rem', color: 'var(--deep)', fontWeight: 800, margin: 0 }}>
              Incoming Offers ({offers.length})
            </h4>
            <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
              Auto-expire in 60s
            </span>
          </div>

          {offers.length === 0 ? (
            <div
              style={{
                background: 'var(--white)',
                border: '1px dashed var(--line)',
                borderRadius: 'var(--r-card-lg)',
                padding: '40px 20px',
                textAlign: 'center',
                color: 'var(--muted)',
              }}
            >
              <div style={{ fontSize: '32px', marginBottom: '8px' }}>🍲</div>
              <strong style={{ display: 'block', color: 'var(--deep)', marginBottom: '4px' }}>No Pending Offers</strong>
              <span style={{ fontSize: '0.85rem' }}>Offers from nearby Jaipur kitchens will appear here with a live countdown.</span>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {offers.map((offer) => (
                <OfferCard
                  key={offer.id}
                  offer={offer}
                  onAccept={() => handleAcceptOffer(offer.id)}
                  onDecline={(reason) => handleDeclineOffer(offer.id, reason)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Incoming Deliveries in Flight Column */}
        <div>
          <h4 style={{ fontSize: '1.2rem', color: 'var(--deep)', fontWeight: 800, marginBottom: '16px' }}>
            En-Route Deliveries (1 Active)
          </h4>

          <div
            style={{
              background: 'var(--white)',
              border: '1px solid var(--line)',
              borderRadius: 'var(--r-card-lg)',
              padding: '20px',
              boxShadow: 'var(--shadow-soft)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: '0.72rem', background: 'var(--blue-tint)', color: 'var(--blue-text)', padding: '3px 8px', borderRadius: 'var(--r-pill)', fontWeight: 700 }}>
                  IN TRANSIT VIA JLN MARG
                </span>
                <h5 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--deep)', margin: '8px 0 4px' }}>
                  45 Veg Meals (Paneer & Rice)
                </h5>
                <div style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
                  From: Spice Route Kitchen (C-Scheme)
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--green-dark)' }}>
                  ETA 18m
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>
                  Remaining slack 42m
                </div>
              </div>
            </div>

            <div
              style={{
                marginTop: '16px',
                background: 'var(--paper)',
                padding: '10px 14px',
                borderRadius: 'var(--r-card-sm)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '0.8rem',
              }}
            >
              <span>🛵 Driver: <strong>Rajesh Kumar (E-Rickshaw)</strong></span>
              <span style={{ fontFamily: 'monospace', fontWeight: 700 }}>Tag #JPR-C1</span>
            </div>

            <div style={{ marginTop: '14px', fontSize: '0.78rem', color: 'var(--deep)', fontWeight: 600 }}>
              ✓ Volunteers notified • Thermal holding station prepared
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

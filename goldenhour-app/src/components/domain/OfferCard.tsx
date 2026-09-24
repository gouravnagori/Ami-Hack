import React, { useState } from 'react';
import type { Offer } from '../../types/api';
import { CountdownRing } from './CountdownRing';
import { DietBadge } from './DietBadge';
import { StorageBadge } from './StorageBadge';
import { Button } from '../ui/Button';
import { formatPortions, formatDistance } from '../../lib/format';

interface OfferCardProps {
  offer: Offer;
  onAccept: (portions?: number) => void;
  onDecline: (reason?: string) => void;
  isLoading?: boolean;
}

export const OfferCard: React.FC<OfferCardProps> = ({
  offer,
  onAccept,
  onDecline,
  isLoading = false,
}) => {
  const maxPortions = offer.max_acceptable_portions || offer.donation.total_portions;
  const [selectedPortions, setSelectedPortions] = useState<number>(offer.offered_portions || maxPortions);
  const [showDeclineReason, setShowDeclineReason] = useState(false);

  return (
    <div
      style={{
        background: 'var(--white)',
        border: '1px solid var(--line)',
        borderRadius: 'var(--r-card-lg)',
        padding: '20px',
        boxShadow: 'var(--shadow-soft)',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        transition: 'transform 0.25s var(--ease), box-shadow 0.25s var(--ease)',
      }}
    >
      {/* Top Header: Donor info + Countdown Ring */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '4px' }}>
            <h4 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--deep)' }}>
              {offer.donation.donor_name}
            </h4>
            <DietBadge diet={offer.donation.diet} />
            <StorageBadge storage={offer.donation.storage} />
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
            📍 {formatDistance(offer.donation.distance_m)} away • Safe until {new Date(offer.donation.safe_until).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>

        {/* Countdown Ring */}
        <div style={{ flexShrink: 0 }}>
          <CountdownRing
            deadline={offer.expires_at}
            size="sm"
            initialSeconds={60}
          />
        </div>
      </div>

      {/* Food Items & Portions */}
      <div
        style={{
          background: 'var(--paper)',
          padding: '12px 14px',
          borderRadius: 'var(--r-card-sm)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <div style={{ fontSize: '0.8rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Surplus Offered
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--ink)' }}>
            {formatPortions(offer.donation.total_portions)}
          </div>
          {offer.donation.items.length > 0 && (
            <div style={{ fontSize: '0.82rem', color: 'var(--muted)', marginTop: '2px' }}>
              {offer.donation.items.join(', ')}
            </div>
          )}
        </div>

        {offer.match_explanation && (
          <div style={{ textAlign: 'right' }}>
            <span
              style={{
                background: 'var(--soft)',
                color: 'var(--deep)',
                padding: '4px 8px',
                borderRadius: 'var(--r-pill)',
                fontSize: '0.78rem',
                fontWeight: 700,
              }}
            >
              ★ {Math.round(offer.match_explanation.score * 100)}% Match
            </span>
          </div>
        )}
      </div>

      {/* Recipient Portion Adjustment if Recipient Offer */}
      {offer.kind === 'recipient' && maxPortions > 10 && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.88rem' }}>
          <span style={{ color: 'var(--muted)' }}>Accept Portions:</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              type="button"
              onClick={() => setSelectedPortions(p => Math.max(5, p - 5))}
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                background: 'var(--paper)',
                border: '1px solid var(--line)',
                fontWeight: 700,
              }}
            >
              -
            </button>
            <span style={{ fontWeight: 700, minWidth: '40px', textAlign: 'center' }}>
              {selectedPortions}
            </span>
            <button
              type="button"
              onClick={() => setSelectedPortions(p => Math.min(maxPortions, p + 5))}
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                background: 'var(--paper)',
                border: '1px solid var(--line)',
                fontWeight: 700,
              }}
            >
              +
            </button>
          </div>
        </div>
      )}

      {/* Driver Route Preview if Driver Offer */}
      {offer.kind === 'driver' && offer.route_preview && (
        <div
          style={{
            borderLeft: '3px solid var(--green)',
            paddingLeft: '10px',
            fontSize: '0.82rem',
            color: 'var(--muted)',
            display: 'flex',
            gap: '12px',
          }}
        >
          <span>🚗 +{Math.round(offer.route_preview.added_detour_s / 60)}m detour</span>
          <span>📍 {offer.route_preview.stops.length} stops</span>
          <span>⚡ {Math.round(offer.route_preview.on_time_confidence * 100)}% on-time</span>
        </div>
      )}

      {/* Action Buttons */}
      {!showDeclineReason ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr', gap: '10px', marginTop: '4px' }}>
          <Button
            variant="outline"
            size="md"
            onClick={() => setShowDeclineReason(true)}
            disabled={isLoading}
          >
            Decline
          </Button>
          <Button
            variant="primary"
            size="md"
            arrow
            onClick={() => onAccept(selectedPortions)}
            disabled={isLoading}
          >
            Accept {selectedPortions}
          </Button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>Reason for decline:</div>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {['At Capacity', 'Closed Soon', 'Diet Mismatch', 'Vehicle Full'].map(reason => (
              <button
                key={reason}
                type="button"
                onClick={() => onDecline(reason)}
                style={{
                  background: 'var(--paper)',
                  border: '1px solid var(--line)',
                  borderRadius: 'var(--r-pill)',
                  padding: '5px 10px',
                  fontSize: '0.78rem',
                  color: 'var(--ink)',
                }}
              >
                {reason}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setShowDeclineReason(false)}
            style={{ fontSize: '0.78rem', color: 'var(--muted)', textDecoration: 'underline', marginTop: '4px' }}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
};

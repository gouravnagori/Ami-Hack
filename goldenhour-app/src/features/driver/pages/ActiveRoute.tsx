import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../../lib/api';
import { useUiStore } from '../../../store/ui';
import type { Route } from '../../../types/api';
import { RouteMap } from '../../../components/domain/RouteMap';
import { StopList } from '../../../components/domain/StopList';
import { Button } from '../../../components/ui/Button';

export const ActiveRoute: React.FC = () => {
  const navigate = useNavigate();
  const { addToast } = useUiStore();
  const [route, setRoute] = useState<Route | null>(null);
  const [activeStopIndex, setActiveStopIndex] = useState(0);
  const [otpInput, setOtpInput] = useState('');
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    api
      .get<Route>('/api/routes/active')
      .then(setRoute)
      .catch((err) => console.error(err));
  }, []);

  if (!route) {
    return <div style={{ textAlign: 'center', padding: '60px', color: 'var(--muted)' }}>Loading active navigation...</div>;
  }

  const currentStop = route.stops[activeStopIndex] || route.stops[0];
  const isPickup = currentStop.type === 'pickup';
  const isLastStop = activeStopIndex === route.stops.length - 1;

  const handleCompleteStop = async () => {
    if (currentStop.requires_otp && !otpInput.trim()) {
      addToast('Please enter the 4-digit verification OTP', 'warning');
      return;
    }

    setConfirming(true);
    try {
      await api.post(`/api/routes/${route.id}/stops/${currentStop.id}/done`, {
        otp: otpInput,
      });

      addToast(
        isPickup ? 'Pickup verified! Proceeding to recipient shelter.' : 'Dropoff verified! Route completed.',
        'success'
      );

      setOtpInput('');
      if (isLastStop) {
        navigate('/driver/done');
      } else {
        setActiveStopIndex((prev) => prev + 1);
      }
    } catch {
      addToast('Failed to verify stop', 'error');
    } finally {
      setConfirming(false);
    }
  };

  const handleReportIssue = () => {
    addToast('Traffic / Delay alert dispatched to Jaipur Ops Engine. Buffer extended by 10 mins.', 'info');
  };

  return (
    <div>
      {/* Route Map Header */}
      <div style={{ marginBottom: '16px', borderRadius: 'var(--r-card-lg)', overflow: 'hidden' }}>
        <RouteMap
          route={route}
          activeStop={currentStop}
          markers={[
            { id: '1', type: 'donor', name: route.stops[0].place.name, geo: route.stops[0].place },
            { id: '2', type: 'recipient', name: route.stops[1].place.name, geo: route.stops[1].place },
          ]}
          height="240px"
        />
      </div>

      {/* Active Stop Card */}
      <div
        style={{
          background: 'var(--white)',
          border: '2px solid var(--deep)',
          borderRadius: 'var(--r-card-lg)',
          padding: '20px',
          boxShadow: 'var(--shadow)',
          marginBottom: '18px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 800,
                textTransform: 'uppercase',
                background: isPickup ? 'var(--deep)' : 'var(--green-dark)',
                color: 'var(--white)',
                padding: '3px 8px',
                borderRadius: 'var(--r-pill)',
              }}
            >
              CURRENT STOP: {isPickup ? 'PICKUP' : 'DROPOFF'}
            </span>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--ink)', margin: '8px 0 2px' }}>
              {currentStop.place.name}
            </h3>
            <div style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
              {currentStop.place.address}
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--deep)' }}>
              {currentStop.portions} Portions
            </span>
            <div style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>
              Tag #{currentStop.container_label}
            </div>
          </div>
        </div>

        {/* OTP Input Field */}
        {currentStop.requires_otp && (
          <div style={{ marginTop: '16px', background: 'var(--paper)', padding: '14px', borderRadius: 'var(--r-card-sm)' }}>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--deep)', marginBottom: '6px' }}>
              {isPickup ? 'Ask Kitchen Chef for Pickup OTP:' : 'Ask Shelter Manager for Dropoff OTP:'}
            </label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                maxLength={6}
                value={otpInput}
                onChange={(e) => setOtpInput(e.target.value)}
                placeholder="4-digit code (e.g. 4829)"
                style={{
                  flex: 1,
                  padding: '10px 14px',
                  borderRadius: 'var(--r-card-sm)',
                  border: '1px solid var(--line)',
                  background: 'var(--white)',
                  fontSize: '1.1rem',
                  fontWeight: 800,
                  letterSpacing: '2px',
                  outline: 'none',
                }}
              />
              <button
                type="button"
                onClick={() => setOtpInput(isPickup ? '4829' : '7193')}
                style={{
                  fontSize: '0.75rem',
                  background: 'var(--soft)',
                  color: 'var(--deep)',
                  border: '1px solid var(--line)',
                  padding: '0 10px',
                  borderRadius: 'var(--r-card-sm)',
                  fontWeight: 700,
                }}
              >
                Auto-fill
              </button>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <Button
            variant="primary"
            size="lg"
            block
            arrow
            onClick={handleCompleteStop}
            disabled={confirming}
          >
            {confirming
              ? 'Verifying...'
              : isLastStop
              ? 'Confirm Dropoff & Finish'
              : 'Confirm Pickup & Navigate'}
          </Button>

          <button
            type="button"
            onClick={handleReportIssue}
            style={{
              padding: '8px',
              fontSize: '0.78rem',
              color: 'var(--muted)',
              textDecoration: 'underline',
              textAlign: 'center',
            }}
          >
            ⚠️ Report traffic delay or gate access issue
          </button>
        </div>
      </div>

      {/* Stop Sequence Overview */}
      <div style={{ marginBottom: '14px' }}>
        <h5 style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--deep)', marginBottom: '8px' }}>
          Route Manifest ({route.stops.length} stops)
        </h5>
        <StopList stops={route.stops} activeStopIndex={activeStopIndex} />
      </div>
    </div>
  );
};

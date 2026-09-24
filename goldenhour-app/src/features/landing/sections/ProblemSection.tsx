import React from 'react';
import { CountdownRing } from '../../../components/domain/CountdownRing';

export const ProblemSection: React.FC = () => {
  return (
    <section
      id="problem"
      style={{
        background: 'var(--deep)',
        color: 'var(--white)',
        padding: '90px 0',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div className="wrap">
        <div style={{ textAlign: 'center', maxWidth: '720px', margin: '0 auto 60px' }}>
          <div
            style={{
              color: 'var(--green)',
              fontSize: '0.75rem',
              fontWeight: 700,
              letterSpacing: '0.18em',
              marginBottom: '14px',
              textTransform: 'uppercase',
            }}
          >
            The Critical Countdown
          </div>
          <h2 style={{ color: 'var(--white)', fontSize: 'clamp(2.4rem, 4.5vw, 3.8rem)', lineHeight: 1.05 }}>
            Food rescue is not a logistics problem. It is a <em>clock problem</em>.
          </h2>
          <p style={{ color: 'var(--on-dark-muted)', fontSize: '1.1rem', marginTop: '20px', lineHeight: 1.6 }}>
            Prepared hot food enters bacterial growth temperature thresholds within 2 hours. If matching, dispatching, and transit take 2 hours and 1 minute, 100% of the food is wasted.
          </p>
        </div>

        {/* 3 Spoilage Clock Risk Cards */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '24px',
          }}
        >
          {/* Card 1: Safe Window */}
          <div
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(143, 211, 90, 0.3)',
              borderRadius: 'var(--r-card-lg)',
              padding: '28px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
            }}
          >
            <CountdownRing
              deadline={new Date(Date.now() + 45 * 60 * 1000).toISOString()}
              size="md"
              initialSeconds={3600}
            />
            <div style={{ marginTop: '20px' }}>
              <span
                style={{
                  background: 'var(--green)',
                  color: 'var(--deep)',
                  padding: '4px 10px',
                  borderRadius: 'var(--r-pill)',
                  fontSize: '0.75rem',
                  fontWeight: 800,
                }}
              >
                STAGE 1: GOLDEN WINDOW
              </span>
              <h4 style={{ fontSize: '1.3rem', margin: '14px 0 8px', color: 'var(--white)' }}>
                Safe Slack (&gt; 30%)
              </h4>
              <p style={{ fontSize: '0.88rem', color: 'var(--on-dark-muted)', lineHeight: 1.5 }}>
                Food freshly prepared. Matching engine selects optimal shelter with highest consumption rate and dispatches closest vehicle.
              </p>
            </div>
          </div>

          {/* Card 2: Tight Slack */}
          <div
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(240, 160, 131, 0.4)',
              borderRadius: 'var(--r-card-lg)',
              padding: '28px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
            }}
          >
            <CountdownRing
              deadline={new Date(Date.now() + 18 * 60 * 1000).toISOString()}
              size="md"
              initialSeconds={7200}
            />
            <div style={{ marginTop: '20px' }}>
              <span
                style={{
                  background: 'var(--peach)',
                  color: 'var(--deep)',
                  padding: '4px 10px',
                  borderRadius: 'var(--r-pill)',
                  fontSize: '0.75rem',
                  fontWeight: 800,
                }}
              >
                STAGE 2: TIGHT SLACK
              </span>
              <h4 style={{ fontSize: '1.3rem', margin: '14px 0 8px', color: 'var(--white)' }}>
                10% – 30% Buffer
              </h4>
              <p style={{ fontSize: '0.88rem', color: 'var(--on-dark-muted)', lineHeight: 1.5 }}>
                Traffic alerts activate dynamic rerouting. Driver route priority elevates. Recipient is notified to prepare thermal warming trays.
              </p>
            </div>
          </div>

          {/* Card 3: Critical */}
          <div
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(217, 107, 75, 0.5)',
              borderRadius: 'var(--r-card-lg)',
              padding: '28px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
            }}
          >
            <CountdownRing
              deadline={new Date(Date.now() + 4 * 60 * 1000).toISOString()}
              size="md"
              initialSeconds={3600}
            />
            <div style={{ marginTop: '20px' }}>
              <span
                style={{
                  background: 'var(--red)',
                  color: 'var(--white)',
                  padding: '4px 10px',
                  borderRadius: 'var(--r-pill)',
                  fontSize: '0.75rem',
                  fontWeight: 800,
                }}
              >
                STAGE 3: CRITICAL RESCUE
              </span>
              <h4 style={{ fontSize: '1.3rem', margin: '14px 0 8px', color: 'var(--white)' }}>
                &lt; 10% Slack Remaining
              </h4>
              <p style={{ fontSize: '0.88rem', color: 'var(--on-dark-muted)', lineHeight: 1.5 }}>
                Emergency failover triggered. If original shelter cannot accept immediately, nearest walk-in soup kitchen auto-assigned via SMS/IVR.
              </p>
            </div>
          </div>
        </div>

        {/* Jaipur Impact Summary Row */}
        <div
          style={{
            marginTop: '60px',
            padding: '30px',
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: '20px',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '24px',
            textAlign: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--green)' }}>97.8%</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--on-dark-muted)', marginTop: '4px' }}>
              On-Time Delivery Rate
            </div>
          </div>
          <div>
            <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--white)' }}>164s</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--on-dark-muted)', marginTop: '4px' }}>
              Median Donor-to-Match Time
            </div>
          </div>
          <div>
            <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--green)' }}>48,260+</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--on-dark-muted)', marginTop: '4px' }}>
              Jaipur Meals Rescued to Date
            </div>
          </div>
          <div>
            <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--white)' }}>0%</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--on-dark-muted)', marginTop: '4px' }}>
              Temperature Compliance Violations
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

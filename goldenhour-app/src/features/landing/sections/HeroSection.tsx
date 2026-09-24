import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../../components/ui/Button';
import { LiveBadge } from '../../../components/ui/LiveBadge';
import { MiniBars } from '../../../components/domain/MiniBars';
import { CountdownRing } from '../../../components/domain/CountdownRing';
import styles from './HeroSection.module.css';

type HeroRole = 'donor' | 'recipient' | 'driver';

export const HeroSection: React.FC = () => {
  const navigate = useNavigate();
  const [activeRole, setActiveRole] = useState<HeroRole>('donor');

  const roleHeadings = {
    donor: {
      eyebrow: 'JAIPUR FOOD RESCUE CORRIDOR',
      h1Lead: 'Turn surplus food into',
      h1Em: 'rescued meals',
      h1Tail: 'before the clock runs out.',
      p: 'Connect banquet halls, hotel kitchens, and catering surplus in Jaipur to shelters in minutes. AI parses your food list, reserves capacity, and dispatches verified drivers before food spoils.',
      cta1: 'Post Food Now',
      cta1Route: '/donor',
      cta2: 'Explore Live Ops',
      cta2Route: '/ops',
    },
    recipient: {
      eyebrow: 'AUTOMATED CAPACITY MATCHING',
      h1Lead: 'Get fresh, hot meals',
      h1Em: 'matched to your capacity',
      h1Tail: 'without chaos.',
      p: 'Shelters set portion capacity, diet filters (veg/egg), and intake windows. GoldenHour guarantees on-time driver arrival and temperature compliance before food reaches risk thresholds.',
      cta1: 'Manage Shelter Capacity',
      cta1Route: '/org',
      cta2: 'View Incoming Offers',
      cta2Route: '/org',
    },
    driver: {
      eyebrow: 'OPTIMIZED RESCUE ROUTING',
      h1Lead: 'Rescue food on your route with',
      h1Em: 'zero wasted detours',
      h1Tail: 'across Pink City.',
      p: 'Drivers receive turn-by-turn multi-stop routes with guaranteed slack windows, one-tap OTP drop verification, and live heat maps of surplus zones across C-Scheme, Tonk Road, and Mansarovar.',
      cta1: 'Start Driving',
      cta1Route: '/driver',
      cta2: 'View Active Routes',
      cta2Route: '/driver',
    },
  };

  const current = roleHeadings[activeRole];

  return (
    <section className={styles.hero}>
      {/* Background radial shapes matching reference HTML */}
      <div className={styles.heroOrbRight} />
      <div className={styles.heroOrbLeft} />

      <div className={`wrap ${styles.heroGrid}`}>
        {/* Left Column: Role Selector & Staggered Copy */}
        <div className={styles.heroCopy}>
          {/* Role Pill Switcher */}
          <div className={styles.roleTabs}>
            <button
              type="button"
              className={`${styles.roleTab} ${activeRole === 'donor' ? styles.activeTab : ''}`}
              onClick={() => setActiveRole('donor')}
            >
              🍲 For Donors
            </button>
            <button
              type="button"
              className={`${styles.roleTab} ${activeRole === 'recipient' ? styles.activeTab : ''}`}
              onClick={() => setActiveRole('recipient')}
            >
              🏠 For Shelters
            </button>
            <button
              type="button"
              className={`${styles.roleTab} ${activeRole === 'driver' ? styles.activeTab : ''}`}
              onClick={() => setActiveRole('driver')}
            >
              🛵 For Drivers
            </button>
          </div>

          <div className={styles.eyebrow}>{current.eyebrow}</div>

          <h1 className={styles.heroTitle}>
            {current.h1Lead} <em>{current.h1Em}</em> {current.h1Tail}
          </h1>

          <p className={styles.heroText}>{current.p}</p>

          <div className={styles.heroButtons}>
            <Button
              variant="primary"
              size="lg"
              arrow
              onClick={() => navigate(current.cta1Route)}
            >
              {current.cta1}
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={() => navigate(current.cta2Route)}
            >
              {current.cta2}
            </Button>
          </div>

          {/* Live Demand Card */}
          <div className={styles.demandCard}>
            <div className={styles.demandTop}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '18px' }}>📍</span>
                <div>
                  <strong>Asha Shelter • Malviya Nagar, Jaipur</strong>
                  <div style={{ fontSize: '0.74rem', color: 'var(--muted)' }}>5.2 km from C-Scheme via JLN Marg</div>
                </div>
              </div>
              <LiveBadge text="Live Corridor" />
            </div>

            <div className={styles.demandValues}>
              <div className={styles.demandVal}>
                <span className={styles.demandLabel}>Surplus Available</span>
                <span className={styles.demandNum}>65</span>
                <span className={styles.demandSub}>Portions hot veg</span>
              </div>

              <div className={styles.arrowRing}>
                <span>➔</span>
              </div>

              <div className={`${styles.demandVal} ${styles.blueVal}`}>
                <span className={styles.demandLabel}>Shelter Capacity</span>
                <span className={`${styles.demandNum} ${styles.blueNum}`}>90</span>
                <span className={styles.demandSub}>Slots open now</span>
              </div>
            </div>

            <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: 'var(--muted)' }}>
              <span>⏱ Estimated pickup in <strong>12 mins</strong></span>
              <span style={{ color: 'var(--deep)', fontWeight: 700 }}>96% Feasibility Score</span>
            </div>
          </div>

          {/* Trust Checkmarks */}
          <div className={styles.trustRow}>
            <span>FSSAI temperature standards</span>
            <span>OTP delivery proof</span>
            <span>Zero vehicle deadheads</span>
          </div>
        </div>

        {/* Right Column: Floating Interactive Cards */}
        <div className={styles.heroVisual}>
          <div className={styles.backShape} />
          <div className={styles.sceneGrid} />

          {/* Floating Live Dashboard Card */}
          <div className={styles.dashboard}>
            <div className={styles.dashHead}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '18px' }}>⚡</span>
                <div>
                  <strong style={{ fontSize: '0.92rem' }}>Jaipur Live Rescue Dispatch</strong>
                  <div style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>Active corridor #JPR-402</div>
                </div>
              </div>
              <LiveBadge text="Live" />
            </div>

            <div className={styles.dashGrid}>
              {/* Spoilage Clock Widget */}
              <div className={styles.dashCard}>
                <small>Golden Hour Clock</small>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '6px' }}>
                  <div>
                    <strong style={{ fontSize: '1.45rem', color: 'var(--deep)' }}>48:20</strong>
                    <em style={{ display: 'block', fontSize: '0.7rem', color: 'var(--green-dark)', fontWeight: 700 }}>Safe Slack</em>
                  </div>
                  <CountdownRing
                    deadline={new Date(Date.now() + 48 * 60 * 1000).toISOString()}
                    size="sm"
                    initialSeconds={3600}
                  />
                </div>
              </div>

              {/* Matched Driver Widget */}
              <div className={`${styles.dashCard} ${styles.blueCard}`}>
                <small>Assigned Driver</small>
                <strong style={{ fontSize: '1.25rem', color: 'var(--blue-text)', marginTop: '4px' }}>Rajesh K.</strong>
                <em style={{ display: 'block', fontSize: '0.72rem', color: 'var(--muted)' }}>E-Rickshaw • 4 mins away</em>
              </div>

              {/* Weekly Rescued Meals Mini Bar Graph */}
              <div className={`${styles.dashCard} ${styles.wideCard}`}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <small>Rescued Meals Today (Jaipur Hubs)</small>
                  <strong style={{ fontSize: '1rem', color: 'var(--deep)', margin: 0 }}>1,248 meals</strong>
                </div>
                <div style={{ marginTop: '10px' }}>
                  <MiniBars values={[30, 45, 60, 85, 110, 95, 130, 160, 140, 175, 190, 210]} activeIndex={11} height={48} />
                </div>
              </div>
            </div>

            {/* Bottom floating notification strip */}
            <div className={styles.dashFooter}>
              <span>🥘 <strong>Spice Route Kitchen:</strong> 40 hot meals transferred safely</span>
              <span style={{ color: 'var(--green-dark)', fontWeight: 700 }}>✓ Verified</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

import React from 'react';
import { MetricCard } from '../../../components/ui/MetricCard';
import { MiniBars } from '../../../components/domain/MiniBars';

export const ImpactSection: React.FC = () => {
  return (
    <section id="impact" style={{ padding: '90px 0', background: 'var(--analytics-bg)' }}>
      <div className="wrap">
        <div style={{ maxWidth: '640px', margin: '0 auto 60px', textAlign: 'center' }}>
          <div className="eyebrow">MEASURABLE ENVIRONMENTAL & SOCIAL IMPACT</div>
          <h2>Real Impact Across <em>Pink City</em></h2>
          <p style={{ color: 'var(--muted)', fontSize: '1.05rem', marginTop: '16px' }}>
            Every portion delivered on time is logged, verified with cryptographic OTPs, and audited for zero landfill decomposition.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '16px',
            marginBottom: '40px',
          }}
        >
          <MetricCard
            label="Meals Rescued"
            value={48260}
            sub="+1,248 today"
            variant="default"
          />
          <MetricCard
            label="Landfill Diverted (kg)"
            value={18450}
            sub="Fresh edible food preserved"
            variant="blue"
          />
          <MetricCard
            label="CO2e Emissions Avoided"
            value={42120}
            format={(n) => `${(n / 1000).toFixed(1)}k kg`}
            sub="Methane reduction equivalent"
            variant="default"
          />
          <MetricCard
            label="On-Time Delivery Rate"
            value={97.8}
            format={(n) => `${n.toFixed(1)}%`}
            sub="Within strict safe window"
            variant="default"
          />
        </div>

        {/* Weekly Chart Container */}
        <div
          style={{
            background: 'var(--white)',
            border: '1px solid var(--line)',
            borderRadius: 'var(--r-card-lg)',
            padding: '32px',
            boxShadow: 'var(--shadow-soft)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <div>
              <h4 style={{ fontSize: '1.2rem', color: 'var(--deep)', fontWeight: 800 }}>
                Weekly Rescue Volume (Jaipur Metro)
              </h4>
              <p style={{ fontSize: '0.85rem', color: 'var(--muted)', margin: '4px 0 0' }}>
                Peak rescue spikes occur on Friday and Saturday wedding banquets
              </p>
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--green-dark)', background: 'var(--soft)', padding: '4px 12px', borderRadius: 'var(--r-pill)' }}>
              ▲ 28% week-over-week
            </span>
          </div>

          <MiniBars
            values={[680, 820, 740, 950, 1240, 1580, 1390]}
            activeIndex={5}
            height={90}
          />

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', fontSize: '0.78rem', color: 'var(--muted)', fontWeight: 600 }}>
            <span>Mon</span>
            <span>Tue</span>
            <span>Wed</span>
            <span>Thu</span>
            <span>Fri (Surge)</span>
            <span>Sat (Wedding Peak)</span>
            <span>Sun</span>
          </div>
        </div>
      </div>
    </section>
  );
};

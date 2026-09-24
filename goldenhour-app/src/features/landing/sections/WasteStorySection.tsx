import React from 'react';

export const WasteStorySection: React.FC = () => {
  return (
    <section style={{ padding: '90px 0', background: 'var(--paper)' }}>
      <div className="wrap">
        <div style={{ maxWidth: '680px', margin: '0 auto 50px', textAlign: 'center' }}>
          <div className="eyebrow">THE SCIENCE OF SURPLUS</div>
          <h2>The Cost of <em>Every Minute</em></h2>
          <p style={{ color: 'var(--muted)', fontSize: '1.05rem', marginTop: '16px' }}>
            In traditional donation drives, coordinators spend 45 minutes on WhatsApp groups while food cools and bacterial multiplication accelerates. GoldenHour collapses matching to 2.7 minutes.
          </p>
        </div>

        {/* Timeline breakdown */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '20px',
          }}
        >
          {[
            {
              time: '0 min',
              title: 'Food Packaged',
              desc: 'Kitchen finishes catering. Temp > 65°C. Safe window begins.',
              badge: 'Fresh & Hot',
              color: 'var(--green)',
            },
            {
              time: '2.7 min',
              title: 'AI Match & Accept',
              desc: 'Natural language parse finds nearest shelter with open warm slots.',
              badge: 'Algorithm Locked',
              color: 'var(--green-dark)',
            },
            {
              time: '18 min',
              title: 'Driver Arrival',
              desc: 'Nearest delivery vehicle verifies containers with thermal seals.',
              badge: 'En-route',
              color: 'var(--deep)',
            },
            {
              time: '42 min',
              title: 'Hot Meal Served',
              desc: 'Delivered to Malviya Nagar shelter with 78 minutes of slack remaining.',
              badge: 'Success',
              color: 'var(--green)',
            },
          ].map((item, idx) => (
            <div
              key={idx}
              style={{
                background: 'var(--white)',
                border: '1px solid var(--line)',
                borderRadius: 'var(--r-card-lg)',
                padding: '24px',
                position: 'relative',
                boxShadow: 'var(--shadow-soft)',
              }}
            >
              <div
                style={{
                  fontSize: '1.6rem',
                  fontWeight: 800,
                  color: item.color,
                  letterSpacing: '-0.04em',
                }}
              >
                {item.time}
              </div>
              <div
                style={{
                  display: 'inline-block',
                  margin: '8px 0 12px',
                  background: 'var(--soft)',
                  color: 'var(--deep)',
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  padding: '3px 8px',
                  borderRadius: 'var(--r-pill)',
                }}
              >
                {item.badge}
              </div>
              <h4 style={{ fontSize: '1.1rem', color: 'var(--ink)', marginBottom: '8px' }}>
                {item.title}
              </h4>
              <p style={{ fontSize: '0.86rem', color: 'var(--muted)', lineHeight: 1.5 }}>
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

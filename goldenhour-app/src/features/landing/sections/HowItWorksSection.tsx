import React from 'react';

export const HowItWorksSection: React.FC = () => {
  const steps = [
    {
      num: '01',
      title: 'One-Sentence Quick Post',
      desc: 'Type or speak naturally: "50 veg meals ready at C-Scheme until 3 PM". Our NLP extracts portions, dietary class, and storage requirements instantly.',
      tag: 'Donor',
      icon: '💬',
    },
    {
      num: '02',
      title: 'Four-Vector Matching Engine',
      desc: 'Calculates real-time intake capacity of Jaipur shelters, route transit time under current traffic, dietary compatibility, and remaining spoilage slack.',
      tag: 'Engine',
      icon: '🧠',
    },
    {
      num: '03',
      title: 'Zero-Detour Dispatch',
      desc: 'Routes are assigned to local e-rickshaws, bikes, and vans already traversing the corridor, avoiding deadhead runs and ensuring under-30-minute pickup.',
      tag: 'Driver',
      icon: '🛵',
    },
    {
      num: '04',
      title: 'Verified OTP Handshake',
      desc: 'Pickup and delivery verified by digital codes with temperature compliance confirmations, updating live city surplus metrics automatically.',
      tag: 'Shelter',
      icon: '✅',
    },
  ];

  return (
    <section id="how-it-works" style={{ padding: '90px 0', background: 'var(--white)' }}>
      <div className="wrap">
        <div style={{ maxWidth: '640px', margin: '0 auto 60px', textAlign: 'center' }}>
          <div className="eyebrow">HOW GOLDENHOUR WORKS</div>
          <h2>From Kitchen Surplus to <em>Served Meal</em></h2>
          <p style={{ color: 'var(--muted)', fontSize: '1.05rem', marginTop: '16px' }}>
            Four synchronized steps operating under a single shared clock to prevent food waste before it begins.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '24px',
          }}
        >
          {steps.map((s) => (
            <div
              key={s.num}
              style={{
                background: 'var(--paper)',
                border: '1px solid var(--line)',
                borderRadius: 'var(--r-card-lg)',
                padding: '30px 24px',
                position: 'relative',
                transition: 'transform 0.3s var(--ease), box-shadow 0.3s var(--ease)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
                <span style={{ fontSize: '28px' }}>{s.icon}</span>
                <span
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 800,
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    color: 'var(--deep)',
                    background: 'var(--soft)',
                    padding: '4px 10px',
                    borderRadius: 'var(--r-pill)',
                  }}
                >
                  {s.tag}
                </span>
              </div>

              <div style={{ fontSize: '0.82rem', fontWeight: 800, color: 'var(--green-dark)', letterSpacing: '0.06em' }}>
                STEP {s.num}
              </div>

              <h4 style={{ fontSize: '1.25rem', color: 'var(--ink)', margin: '8px 0 12px', fontWeight: 700 }}>
                {s.title}
              </h4>

              <p style={{ fontSize: '0.9rem', color: 'var(--muted)', lineHeight: 1.6 }}>
                {s.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

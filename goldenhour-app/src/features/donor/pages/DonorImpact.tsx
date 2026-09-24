import React from 'react';
import { MetricCard } from '../../../components/ui/MetricCard';
import { Button } from '../../../components/ui/Button';
import { useUiStore } from '../../../store/ui';

export const DonorImpact: React.FC = () => {
  const { addToast } = useUiStore();

  const history = [
    { id: 'REC-0921', date: '22 Sep 2026', portions: 65, recipient: 'Asha Shelter Foundation', status: 'Delivered', co2: '58 kg' },
    { id: 'REC-0918', date: '19 Sep 2026', portions: 120, recipient: 'Akshaya Patra Jaipur', status: 'Delivered', co2: '105 kg' },
    { id: 'REC-0914', date: '15 Sep 2026', portions: 80, recipient: 'Pink City Seva Kutir', status: 'Delivered', co2: '72 kg' },
    { id: 'REC-0910', date: '11 Sep 2026', portions: 45, recipient: 'Robin Hood Army Depot', status: 'Delivered', co2: '41 kg' },
  ];

  const handleDownloadCertificate = () => {
    addToast('Generating Section 80G CSR Tax Exemption Certificate (PDF)...', 'info');
    setTimeout(() => {
      addToast('Certificate #GH-JPR-80G-2026 downloaded!', 'success');
    }, 1200);
  };

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h2 style={{ fontSize: '2rem', color: 'var(--deep)', fontWeight: 800 }}>
            Impact & CSR Tax Certificates
          </h2>
          <p style={{ color: 'var(--muted)', fontSize: '0.95rem' }}>
            Audited food rescue logs for Spice Route Kitchen (C-Scheme, Jaipur)
          </p>
        </div>

        <Button variant="primary" size="md" arrow onClick={handleDownloadCertificate}>
          Download 80G Tax Receipt
        </Button>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '32px' }}>
        <MetricCard label="Total Meals Rescued" value={1420} sub="All verified by shelters" variant="default" />
        <MetricCard label="Total Weight (kg)" value={580} sub="Prepared food saved" variant="blue" />
        <MetricCard label="CO2e Emissions Prevented" value={1240} format={(n) => `${n} kg`} sub="Zero landfill decay" variant="default" />
        <MetricCard label="CSR Compliance Score" value={100} format={(n) => `${n}%`} sub="FSSAI compliant" variant="default" />
      </div>

      {/* Donation History Table */}
      <div
        style={{
          background: 'var(--white)',
          border: '1px solid var(--line)',
          borderRadius: 'var(--r-card-lg)',
          padding: '24px',
          boxShadow: 'var(--shadow-soft)',
        }}
      >
        <h4 style={{ fontSize: '1.15rem', color: 'var(--deep)', fontWeight: 800, marginBottom: '16px' }}>
          Verified Rescue Ledger
        </h4>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--line)', color: 'var(--muted)' }}>
                <th style={{ padding: '10px 12px' }}>Receipt ID</th>
                <th style={{ padding: '10px 12px' }}>Date</th>
                <th style={{ padding: '10px 12px' }}>Portions</th>
                <th style={{ padding: '10px 12px' }}>Recipient Shelter</th>
                <th style={{ padding: '10px 12px' }}>CO2 Avoided</th>
                <th style={{ padding: '10px 12px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {history.map((row) => (
                <tr key={row.id} style={{ borderBottom: '1px solid var(--line)' }}>
                  <td style={{ padding: '12px', fontWeight: 700, color: 'var(--deep)' }}>{row.id}</td>
                  <td style={{ padding: '12px', color: 'var(--muted)' }}>{row.date}</td>
                  <td style={{ padding: '12px', fontWeight: 800 }}>{row.portions}</td>
                  <td style={{ padding: '12px' }}>{row.recipient}</td>
                  <td style={{ padding: '12px', color: 'var(--green-dark)', fontWeight: 600 }}>{row.co2}</td>
                  <td style={{ padding: '12px' }}>
                    <span style={{ background: 'var(--soft)', color: 'var(--deep)', padding: '3px 8px', borderRadius: 'var(--r-pill)', fontSize: '0.75rem', fontWeight: 700 }}>
                      ✓ {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

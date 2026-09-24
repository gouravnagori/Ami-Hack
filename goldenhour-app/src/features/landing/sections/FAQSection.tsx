import React from 'react';
import { FAQ } from '../../../components/ui/FAQ';

const FAQ_ITEMS = [
  {
    question: 'How do you ensure food safety and prevent food poisoning?',
    answer:
      'GoldenHour enforces dynamic spoilage deadlines based on preparation time and storage temperature (hot holding > 65°C, refrigerated < 5°C, ambient max 2 hours). If estimated driver transit exceeds the safe slack buffer, the platform rejects matching to that destination and defaults to immediate local pickup.',
  },
  {
    question: 'Can shelters decline donations if they lack capacity?',
    answer:
      'Yes! Shelters set real-time intake caps and have a 1-tap "Pause" switch. Offers expire in 60 seconds if not accepted, after which the algorithm automatically fails over to the next eligible shelter without wasting donor time.',
  },
  {
    question: 'What happens if a driver gets stuck in Jaipur traffic?',
    answer:
      'Our engine monitors active driver telemetry. If traffic causes the projected arrival time to eat through the safe slack buffer, an automated warning triggers, and the ops engine can hot-reassign the delivery to a closer volunteer or split the drop.',
  },
  {
    question: 'Do donors get tax exemptions and CSR verification?',
    answer:
      'Yes, registered restaurants, hotels, and banquet organizers receive instant digitally signed 80G tax receipts and ESG impact reports summarizing total kilograms rescued and CO2e avoided.',
  },
];

export const FAQSection: React.FC = () => {
  return (
    <section id="faq" style={{ padding: '90px 0', background: 'var(--white)' }}>
      <div className="wrap">
        <div style={{ maxWidth: '640px', margin: '0 auto 50px', textAlign: 'center' }}>
          <div className="eyebrow">COMMON QUESTIONS</div>
          <h2>Frequently Asked <em>Questions</em></h2>
          <p style={{ color: 'var(--muted)', fontSize: '1.05rem', marginTop: '16px' }}>
            Everything you need to know about our food rescue dispatch network.
          </p>
        </div>

        <div style={{ maxWidth: '780px', margin: '0 auto' }}>
          <FAQ items={FAQ_ITEMS} />
        </div>
      </div>
    </section>
  );
};

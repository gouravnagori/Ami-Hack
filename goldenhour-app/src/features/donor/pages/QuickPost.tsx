import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../../lib/api';
import { useUiStore } from '../../../store/ui';
import { Button } from '../../../components/ui/Button';
import type { DietType, StorageCondition, Donation, ParseResult } from '../../../types/api';

export const QuickPost: React.FC = () => {
  const navigate = useNavigate();
  const { addToast } = useUiStore();

  const [naturalText, setNaturalText] = useState(
    '50 veg meals of Paneer Butter Masala and Roti ready in 20 minutes at C-Scheme'
  );
  const [parsing, setParsing] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form states
  const [portions, setPortions] = useState(50);
  const [diet, setDiet] = useState<DietType>('veg');
  const [storage, setStorage] = useState<StorageCondition>('hot');
  const [safeHours, setSafeHours] = useState(2.5);
  const [notes] = useState('Packed in 3 insulated metal containers');
  const [photoAdded, setPhotoAdded] = useState(false);

  const handleAiParse = async () => {
    if (!naturalText.trim()) return;
    setParsing(true);
    try {
      const res = await api.post<ParseResult>('/api/donations/parse', { text: naturalText });
      if (res.draft.total_portions) setPortions(res.draft.total_portions);
      if (res.draft.diet) setDiet(res.draft.diet);
      if (res.draft.storage) setStorage(res.draft.storage);
      addToast('AI parsed your surplus details successfully!', 'success');
    } catch {
      addToast('AI parse failed, using manual values', 'warning');
    } finally {
      setParsing(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const now = new Date().toISOString();
      const safeUntil = new Date(Date.now() + safeHours * 3600 * 1000).toISOString();
      const newDonation = await api.post<Donation>('/api/donations', {
        total_portions: portions,
        diet,
        storage,
        category: 'cooked_meals',
        prepared_at: now,
        safe_until: safeUntil,
        pickup_window: {
          start: now,
          end: safeUntil,
        },
        pickup: {
          lat: 26.9085,
          lng: 75.8012,
          address: 'Spice Route Kitchen, C-Scheme, Jaipur',
        },
        notes,
        items: [{ name: naturalText.slice(0, 35) || 'Fresh Meal Surplus', portions }],
      });

      addToast('Surplus posted! Algorithmic matching initiated.', 'success');
      navigate(`/donor/${newDonation.id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to post donation';
      addToast(msg, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: '720px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '2rem', color: 'var(--deep)', fontWeight: 800 }}>
          Quick Post Food Surplus
        </h2>
        <p style={{ color: 'var(--muted)', fontSize: '0.95rem' }}>
          Describe what you have. Our AI parses the attributes and checks live Jaipur shelter capacity.
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Natural Language Prompt Box */}
        <div
          style={{
            background: 'var(--white)',
            border: '1px solid var(--line)',
            borderRadius: 'var(--r-card-lg)',
            padding: '24px',
            boxShadow: 'var(--shadow-soft)',
            marginBottom: '24px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <label style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--deep)' }}>
              1. Type or Paste Food Description
            </label>
            <span style={{ fontSize: '0.74rem', color: 'var(--muted)' }}>Powered by NLP</span>
          </div>

          <textarea
            rows={3}
            value={naturalText}
            onChange={(e) => setNaturalText(e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              borderRadius: 'var(--r-card-sm)',
              border: '1px solid var(--line)',
              background: 'var(--paper)',
              font: 'inherit',
              fontSize: '0.95rem',
              color: 'var(--ink)',
              resize: 'vertical',
              outline: 'none',
            }}
          />

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '12px' }}>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAiParse}
              disabled={parsing}
            >
              {parsing ? 'Parsing...' : '✨ Parse with AI'}
            </Button>
          </div>
        </div>

        {/* Parsed & Editable Attributes */}
        <div
          style={{
            background: 'var(--white)',
            border: '1px solid var(--line)',
            borderRadius: 'var(--r-card-lg)',
            padding: '24px',
            boxShadow: 'var(--shadow-soft)',
            marginBottom: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
          }}
        >
          <h4 style={{ fontSize: '1.1rem', color: 'var(--deep)', fontWeight: 800, margin: 0 }}>
            2. Verified Food Parameters
          </h4>

          {/* Portions Slider */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)' }}>Total Portions</span>
              <strong style={{ fontSize: '1.2rem', color: 'var(--deep)' }}>{portions} meals</strong>
            </div>
            <input
              type="range"
              min={10}
              max={300}
              step={5}
              value={portions}
              onChange={(e) => setPortions(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--green-dark)' }}
            />
          </div>

          {/* Dietary Type */}
          <div>
            <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '8px' }}>
              Dietary Category
            </span>
            <div style={{ display: 'flex', gap: '8px' }}>
              {(['veg', 'egg', 'non_veg'] as DietType[]).map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDiet(d)}
                  style={{
                    flex: 1,
                    padding: '10px',
                    borderRadius: 'var(--r-card-sm)',
                    border: diet === d ? '2px solid var(--deep)' : '1px solid var(--line)',
                    background: diet === d ? 'var(--soft)' : 'var(--paper)',
                    color: 'var(--deep)',
                    fontWeight: diet === d ? 700 : 500,
                    fontSize: '0.85rem',
                  }}
                >
                  {d === 'veg' ? '🟢 Pure Veg' : d === 'egg' ? '🟡 Contains Egg' : '🔴 Non-Veg'}
                </button>
              ))}
            </div>
          </div>

          {/* Storage Requirement */}
          <div>
            <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '8px' }}>
              Storage Condition Required
            </span>
            <div style={{ display: 'flex', gap: '8px' }}>
              {(['hot', 'ambient', 'cold'] as StorageCondition[]).map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setStorage(s)}
                  style={{
                    flex: 1,
                    padding: '10px',
                    borderRadius: 'var(--r-card-sm)',
                    border: storage === s ? '2px solid var(--deep)' : '1px solid var(--line)',
                    background: storage === s ? 'var(--soft)' : 'var(--paper)',
                    color: 'var(--deep)',
                    fontWeight: storage === s ? 700 : 500,
                    fontSize: '0.85rem',
                  }}
                >
                  {s === 'hot' ? '♨️ Keep Hot' : s === 'cold' ? '❄️ Cold' : '📦 Ambient'}
                </button>
              ))}
            </div>
          </div>

          {/* Safe Until Slider */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)' }}>Safe to Consume Until</span>
              <strong style={{ fontSize: '1.05rem', color: 'var(--deep)' }}>
                {safeHours} hours from now
              </strong>
            </div>
            <input
              type="range"
              min={1}
              max={6}
              step={0.5}
              value={safeHours}
              onChange={(e) => setSafeHours(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--green-dark)' }}
            />
          </div>

          {/* Photo attach simulation */}
          <div>
            <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '8px' }}>
              Visual Verification (Optional)
            </span>
            <button
              type="button"
              onClick={() => {
                setPhotoAdded(!photoAdded);
                addToast(photoAdded ? 'Photo removed' : 'Food photo attached (simulated)', 'info');
              }}
              style={{
                width: '100%',
                padding: '14px',
                border: '1px dashed var(--muted)',
                borderRadius: 'var(--r-card-sm)',
                background: photoAdded ? 'var(--soft)' : 'var(--paper)',
                color: 'var(--deep)',
                fontSize: '0.85rem',
                fontWeight: 600,
              }}
            >
              {photoAdded ? '✓ Thermal Container Photo Attached' : '📸 Snap Photo of Containers'}
            </button>
          </div>
        </div>

        {/* Live Feasibility Banner */}
        <div
          style={{
            background: 'var(--deep)',
            color: 'var(--white)',
            padding: '16px 20px',
            borderRadius: 'var(--r-card-sm)',
            marginBottom: '24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--green)', textTransform: 'uppercase', fontWeight: 700 }}>
              Live Corridor Feasibility
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, marginTop: '2px' }}>
              3 Shelters Open • Nearest: Asha Shelter (5.2 km away)
            </div>
          </div>
          <span style={{ background: 'var(--green)', color: 'var(--deep)', padding: '4px 10px', borderRadius: 'var(--r-pill)', fontSize: '0.8rem', fontWeight: 800 }}>
            96% Match
          </span>
        </div>

        {/* Submit */}
        <Button
          type="submit"
          variant="primary"
          size="lg"
          block
          arrow
          disabled={submitting}
        >
          {submitting ? 'Dispatching...' : 'Dispatch Food Rescue'}
        </Button>
      </form>
    </div>
  );
};

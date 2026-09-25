import React, { useState, useEffect } from 'react';
import { useSessionStore } from '../../store/session';
import { useUiStore } from '../../store/ui';
import { api } from '../../lib/api';
import { Button } from '../../components/ui/Button';
import type { User } from '../../types/api';
import { useNavigate } from 'react-router-dom';

export const ProfilePage: React.FC = () => {
  const { user, setSession, clearSession } = useSessionStore();
  const { addToast } = useUiStore();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);
  
  // Base details
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [city, setCity] = useState(user?.city || '');
  
  // Profile specific
  const [profileData, setProfileData] = useState<Record<string, any>>(user?.profile || {});

  useEffect(() => {
    if (!user) {
      navigate('/auth');
    }
  }, [user, navigate]);

  const handleProfileChange = (key: string, value: any) => {
    setProfileData(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const payload = {
        name,
        email: email || undefined,
        city: city || undefined,
        profile: Object.keys(profileData).length > 0 ? profileData : undefined,
      };
      const updatedUser = await api.put<User>('/auth/me', payload);
      setSession(updatedUser, { 
        access_token: useSessionStore.getState().accessToken!,
        refresh_token: useSessionStore.getState().refreshToken!
      });
      addToast('Profile updated successfully!', 'success');
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Update failed';
      addToast(errorMsg, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    clearSession();
    navigate('/');
  };

  if (!user) return null;

  return (
    <div style={{ padding: '40px 20px', maxWidth: '600px', margin: '0 auto', width: '100%' }}>
      <h1 style={{ fontSize: '2rem', color: 'var(--deep)', marginBottom: '8px' }}>Your Profile</h1>
      <p style={{ color: 'var(--muted)', marginBottom: '30px' }}>Manage your account settings and preferences.</p>

      <div style={{ background: 'var(--white)', padding: '24px', borderRadius: 'var(--r-card-lg)', boxShadow: 'var(--shadow)', border: '1px solid var(--line)' }}>
        <h3 style={{ margin: '0 0 16px', color: 'var(--deep)' }}>Basic Information</h3>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <label>
            <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '6px' }}>Full Name</span>
            <input type="text" value={name} onChange={e => setName(e.target.value)} style={inputStyle} />
          </label>
          <label>
            <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '6px' }}>Email Address</span>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} style={inputStyle} />
          </label>
          <label>
            <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '6px' }}>City</span>
            <input type="text" value={city} onChange={e => setCity(e.target.value)} style={inputStyle} />
          </label>
          <label>
            <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '6px' }}>Phone Number (Uneditable)</span>
            <input type="text" value={user.phone} disabled style={{...inputStyle, background: 'var(--paper)', cursor: 'not-allowed'}} />
          </label>
        </div>

        {user.role === 'donor' && (
          <div style={{ marginTop: '30px' }}>
            <h3 style={{ margin: '0 0 16px', color: 'var(--deep)' }}>Donor Details</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <label>
                <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '6px' }}>Pickup Address</span>
                <input type="text" value={profileData.pickup_address || ''} onChange={e => handleProfileChange('pickup_address', e.target.value)} style={inputStyle} />
              </label>
              <label>
                <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '6px' }}>Food Category</span>
                <input type="text" value={profileData.food_category || ''} onChange={e => handleProfileChange('food_category', e.target.value)} style={inputStyle} />
              </label>
              <label>
                <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '6px' }}>Contact Person</span>
                <input type="text" value={profileData.contact_person || ''} onChange={e => handleProfileChange('contact_person', e.target.value)} style={inputStyle} />
              </label>
            </div>
          </div>
        )}

        {user.role === 'recipient' && (
          <div style={{ marginTop: '30px' }}>
            <h3 style={{ margin: '0 0 16px', color: 'var(--deep)' }}>Shelter Details</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <label>
                <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '6px' }}>Max Capacity (Portions)</span>
                <input type="number" value={profileData.max_capacity_portions || ''} onChange={e => handleProfileChange('max_capacity_portions', parseInt(e.target.value, 10))} style={inputStyle} />
              </label>
              <label>
                <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '6px' }}>Food Restrictions</span>
                <input type="text" value={profileData.food_restrictions || ''} onChange={e => handleProfileChange('food_restrictions', e.target.value)} style={inputStyle} />
              </label>
            </div>
          </div>
        )}

        {user.role === 'driver' && (
          <div style={{ marginTop: '30px' }}>
            <h3 style={{ margin: '0 0 16px', color: 'var(--deep)' }}>Driver Details</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <label>
                <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '6px' }}>Vehicle Number</span>
                <input type="text" value={profileData.vehicle_number || ''} onChange={e => handleProfileChange('vehicle_number', e.target.value)} style={inputStyle} />
              </label>
              <label>
                <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '6px' }}>Operating Area</span>
                <input type="text" value={profileData.operating_area || ''} onChange={e => handleProfileChange('operating_area', e.target.value)} style={inputStyle} />
              </label>
            </div>
          </div>
        )}

        <div style={{ marginTop: '30px', display: 'flex', gap: '12px' }}>
          <Button variant="primary" onClick={handleSave} disabled={loading} style={{ flex: 1 }}>
            {loading ? 'Saving...' : 'Save Profile'}
          </Button>
          <Button variant="outline" onClick={handleLogout} style={{ flex: 1, borderColor: 'var(--red)', color: 'var(--red)' }}>
            Log Out
          </Button>
        </div>
      </div>
    </div>
  );
};

const inputStyle = {
  width: '100%',
  padding: '12px 14px',
  borderRadius: 'var(--r-card-sm)',
  border: '1px solid var(--line)',
  background: 'var(--paper)',
  fontSize: '0.95rem',
  color: 'var(--ink)',
  outline: 'none',
};

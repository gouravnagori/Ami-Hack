import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useSessionStore } from '../../store/session';
import { useUiStore } from '../../store/ui';
import { api } from '../../lib/api';
import { Button } from '../../components/ui/Button';
import type { Role, User } from '../../types/api';

export const ProfilePage: React.FC = () => {
  const { user, setSession, clearSession } = useSessionStore();
  const { addToast } = useUiStore();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);

  // Base details
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [city, setCity] = useState(user?.city || 'Jaipur');

  // Profile specific
  const [profileData, setProfileData] = useState<Record<string, any>>(user?.profile || {});

  // Fetch freshest user details if authenticated
  useEffect(() => {
    if (!user) return;

    setFetching(true);
    api.get<User>('/auth/me')
      .then((freshUser) => {
        setName(freshUser.name || '');
        setEmail(freshUser.email || '');
        setCity(freshUser.city || 'Jaipur');
        if (freshUser.profile) {
          setProfileData(freshUser.profile);
        }
        setSession(freshUser, {
          access_token: useSessionStore.getState().accessToken || '',
          refresh_token: useSessionStore.getState().refreshToken || '',
        });
      })
      .catch((err) => {
        console.error('Failed to sync profile', err);
      })
      .finally(() => {
        setFetching(false);
      });
  }, [user?.id]);

  const handleProfileChange = (key: string, value: any) => {
    setProfileData((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
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
        access_token: useSessionStore.getState().accessToken || '',
        refresh_token: useSessionStore.getState().refreshToken || '',
      });
      addToast('Profile updated successfully!', 'success');
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Profile update failed';
      addToast(errorMsg, 'error');
    } finally {
      setLoading(false);
    }
  };


  const getDashboardPath = () => {
    if (!user) return '/';
    if (user.role === 'donor') return '/donor';
    if (user.role === 'recipient') return '/org';
    if (user.role === 'driver') return '/driver';
    return '/ops';
  };

  const getRoleBadge = (role: Role) => {
    switch (role) {
      case 'donor':
        return { label: 'Donor Partner', icon: '🍲', color: '#1b5e20', bg: '#e8f5e9' };
      case 'recipient':
        return { label: 'Shelter Hub', icon: '🏠', color: '#0d47a1', bg: '#e3f2fd' };
      case 'driver':
        return { label: 'Rescue Driver', icon: '🛵', color: '#e65100', bg: '#fff3e0' };
      case 'admin':
        return { label: 'Ops Dispatcher', icon: '⚡', color: '#b71c1c', bg: '#ffebee' };
      default:
        return { label: 'Member', icon: '👤', color: 'var(--deep)', bg: 'var(--soft)' };
    }
  };

  // If user is NOT logged in, show an engaging guest prompt with direct 1-click options
  if (!user) {
    return (
      <div style={{ minHeight: '75vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 20px' }}>
        <div
          style={{
            maxWidth: '520px',
            width: '100%',
            background: 'var(--white)',
            border: '1px solid var(--line)',
            borderRadius: 'var(--r-card-lg)',
            boxShadow: 'var(--shadow)',
            padding: '36px 30px',
            textAlign: 'center',
          }}
        >
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              background: 'var(--soft)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '28px',
              marginBottom: '16px',
            }}
          >
            👤
          </div>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--deep)', margin: '0 0 8px' }}>
            GoldenHour Profile
          </h2>
          <p style={{ color: 'var(--muted)', fontSize: '0.95rem', lineHeight: 1.5, marginBottom: '24px' }}>
            Please sign in to access your profile, view role credentials, and update operating details.
          </p>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            <Button variant="primary" onClick={() => navigate('/auth')}>
              Sign In to Your Account
            </Button>
            <Button variant="outline" onClick={() => navigate('/auth?mode=register')}>
              Create New Account
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const roleMeta = getRoleBadge(user.role);

  return (
    <div style={{ padding: '36px 20px 60px', maxWidth: '720px', margin: '0 auto', width: '100%' }}>
      {/* Top Breadcrumb & Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem', color: 'var(--muted)' }}>
          <Link to="/" style={{ color: 'var(--muted)', textDecoration: 'none' }}>Home</Link>
          <span>/</span>
          <span style={{ color: 'var(--deep)', fontWeight: 600 }}>My Profile</span>
        </div>

        <Link
          to={getDashboardPath()}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.84rem',
            fontWeight: 700,
            color: 'var(--green-dark)',
            textDecoration: 'none',
            background: 'var(--soft)',
            padding: '6px 14px',
            borderRadius: 'var(--r-pill)',
          }}
        >
          <span>Go to {user.role.toUpperCase()} Dashboard →</span>
        </Link>
      </div>

      {/* Profile Header Hero Card */}
      <div
        style={{
          background: 'var(--white)',
          border: '1px solid var(--line)',
          borderRadius: 'var(--r-card-lg)',
          padding: '24px',
          boxShadow: 'var(--shadow)',
          marginBottom: '24px',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              background: roleMeta.bg,
              color: roleMeta.color,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '30px',
              border: `2px solid ${roleMeta.color}33`,
            }}
          >
            {roleMeta.icon}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--deep)', margin: 0 }}>
                {user.name}
              </h1>
              <span
                style={{
                  background: roleMeta.bg,
                  color: roleMeta.color,
                  fontSize: '0.74rem',
                  fontWeight: 800,
                  padding: '3px 8px',
                  borderRadius: 'var(--r-pill)',
                  textTransform: 'uppercase',
                }}
              >
                {roleMeta.label}
              </span>
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginTop: '4px' }}>
              📱 {user.phone} • 📍 {city || 'Jaipur Hub'}
            </div>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            clearSession();
            navigate('/');
          }}
          style={{ borderColor: 'var(--red)', color: 'var(--red)' }}
        >
          Sign Out
        </Button>
      </div>

      {/* Main Edit Form */}
      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Personal Details Section */}
        <div
          style={{
            background: 'var(--white)',
            border: '1px solid var(--line)',
            borderRadius: 'var(--r-card-lg)',
            padding: '24px',
            boxShadow: 'var(--shadow)',
          }}
        >
          <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--deep)', margin: '0 0 16px' }}>
            Personal & Account Details
          </h2>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
            <div>
              <label style={labelStyle}>Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                style={inputStyle}
              />
            </div>

            <div>
              <label style={labelStyle}>Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. name@example.com"
                style={inputStyle}
              />
            </div>

            <div>
              <label style={labelStyle}>Operating City / Hub</label>
              <input
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                style={inputStyle}
              />
            </div>

            <div>
              <label style={labelStyle}>Registered Phone (System Verified)</label>
              <input
                type="text"
                value={user.phone}
                disabled
                style={{ ...inputStyle, background: 'var(--paper)', cursor: 'not-allowed', color: 'var(--muted)' }}
              />
            </div>
          </div>
        </div>

        {/* Role-Specific Details Section */}
        {user.role === 'donor' && (
          <div
            style={{
              background: 'var(--white)',
              border: '1px solid var(--line)',
              borderRadius: 'var(--r-card-lg)',
              padding: '24px',
              boxShadow: 'var(--shadow)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <span style={{ fontSize: '1.2rem' }}>🍲</span>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--deep)', margin: 0 }}>
                Donor Organization Profile
              </h2>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={labelStyle}>Organization / Kitchen Name</label>
                <input
                  type="text"
                  value={profileData.org_name || ''}
                  onChange={(e) => handleProfileChange('org_name', e.target.value)}
                  placeholder="e.g. Spice Route Kitchen"
                  style={inputStyle}
                />
              </div>

              <div style={{ gridColumn: '1 / -1' }}>
                <label style={labelStyle}>Default Pickup Address</label>
                <input
                  type="text"
                  value={profileData.pickup_address || profileData.address || ''}
                  onChange={(e) => {
                    handleProfileChange('pickup_address', e.target.value);
                    handleProfileChange('address', e.target.value);
                  }}
                  placeholder="Street, area, landmarks in Jaipur"
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Establishment Type</label>
                <select
                  value={profileData.kind || profileData.food_category || 'restaurant'}
                  onChange={(e) => {
                    handleProfileChange('kind', e.target.value);
                    handleProfileChange('food_category', e.target.value);
                  }}
                  style={inputStyle}
                >
                  <option value="restaurant">Restaurant / Cafe</option>
                  <option value="caterer">Caterer / Banquet Hall</option>
                  <option value="hostel_mess">College / Hostel Mess</option>
                  <option value="event">Wedding / Event Venue</option>
                  <option value="grocer">Grocer / Bakery</option>
                </select>
              </div>

              <div>
                <label style={labelStyle}>Contact Person</label>
                <input
                  type="text"
                  value={profileData.contact_person || ''}
                  onChange={(e) => handleProfileChange('contact_person', e.target.value)}
                  placeholder="e.g. Chef / Manager name"
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>FSSAI Registration / License No.</label>
                <input
                  type="text"
                  value={profileData.fssai_no || ''}
                  onChange={(e) => handleProfileChange('fssai_no', e.target.value)}
                  placeholder="14-digit FSSAI Number"
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Typical Pickup Hours</label>
                <input
                  type="text"
                  value={profileData.operating_hours || ''}
                  onChange={(e) => handleProfileChange('operating_hours', e.target.value)}
                  placeholder="e.g. 21:00 - 23:30"
                  style={inputStyle}
                />
              </div>
            </div>
          </div>
        )}

        {user.role === 'recipient' && (
          <div
            style={{
              background: 'var(--white)',
              border: '1px solid var(--line)',
              borderRadius: 'var(--r-card-lg)',
              padding: '24px',
              boxShadow: 'var(--shadow)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <span style={{ fontSize: '1.2rem' }}>🏠</span>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--deep)', margin: 0 }}>
                Shelter & Intake Facility Details
              </h2>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={labelStyle}>Shelter / Foundation Name</label>
                <input
                  type="text"
                  value={profileData.name || ''}
                  onChange={(e) => handleProfileChange('name', e.target.value)}
                  placeholder="e.g. Asha Shelter Foundation"
                  style={inputStyle}
                />
              </div>

              <div style={{ gridColumn: '1 / -1' }}>
                <label style={labelStyle}>Facility Delivery Address</label>
                <input
                  type="text"
                  value={profileData.address || ''}
                  onChange={(e) => handleProfileChange('address', e.target.value)}
                  placeholder="Facility street address in Jaipur"
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Max Intake Capacity (Meals / Portions)</label>
                <input
                  type="number"
                  value={profileData.max_capacity_portions ?? 150}
                  onChange={(e) => handleProfileChange('max_capacity_portions', parseInt(e.target.value, 10) || 0)}
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Receiving Hours</label>
                <input
                  type="text"
                  value={profileData.receiving_hours || ''}
                  onChange={(e) => handleProfileChange('receiving_hours', e.target.value)}
                  placeholder="e.g. 10:00 - 23:00"
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Contact Person</label>
                <input
                  type="text"
                  value={profileData.contact_person || ''}
                  onChange={(e) => handleProfileChange('contact_person', e.target.value)}
                  placeholder="Manager / Coordinator name"
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Emergency Receiving Phone</label>
                <input
                  type="text"
                  value={profileData.contact_phone || ''}
                  onChange={(e) => handleProfileChange('contact_phone', e.target.value)}
                  placeholder="+91..."
                  style={inputStyle}
                />
              </div>

              <div style={{ gridColumn: '1 / -1' }}>
                <label style={labelStyle}>Dietary / Storage Restrictions</label>
                <input
                  type="text"
                  value={profileData.food_restrictions || ''}
                  onChange={(e) => handleProfileChange('food_restrictions', e.target.value)}
                  placeholder="e.g. Pure Veg only, requires hot holding"
                  style={inputStyle}
                />
              </div>
            </div>
          </div>
        )}

        {user.role === 'driver' && (
          <div
            style={{
              background: 'var(--white)',
              border: '1px solid var(--line)',
              borderRadius: 'var(--r-card-lg)',
              padding: '24px',
              boxShadow: 'var(--shadow)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <span style={{ fontSize: '1.2rem' }}>🛵</span>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--deep)', margin: 0 }}>
                Driver & Vehicle Telematics
              </h2>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
              <div>
                <label style={labelStyle}>Vehicle Type</label>
                <select
                  value={profileData.vehicle_type || 'scooter'}
                  onChange={(e) => handleProfileChange('vehicle_type', e.target.value)}
                  style={inputStyle}
                >
                  <option value="scooter">🛵 Two-Wheeler / Scooter</option>
                  <option value="e_rickshaw">🛺 E-Rickshaw Cargo</option>
                  <option value="van">🚐 Delivery Van</option>
                  <option value="bicycle">🚲 Bicycle</option>
                </select>
              </div>

              <div>
                <label style={labelStyle}>Vehicle Registration Number</label>
                <input
                  type="text"
                  value={profileData.vehicle_number || ''}
                  onChange={(e) => handleProfileChange('vehicle_number', e.target.value)}
                  placeholder="e.g. RJ-14-ER-9821"
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Primary Operating Area</label>
                <input
                  type="text"
                  value={profileData.operating_area || ''}
                  onChange={(e) => handleProfileChange('operating_area', e.target.value)}
                  placeholder="e.g. Malviya Nagar & C-Scheme"
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Max Capacity (Portions)</label>
                <input
                  type="number"
                  value={profileData.capacity_portions ?? 60}
                  onChange={(e) => handleProfileChange('capacity_portions', parseInt(e.target.value, 10) || 0)}
                  style={inputStyle}
                />
              </div>

              <div style={{ gridColumn: '1 / -1', marginTop: '6px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={Boolean(profileData.has_cold_box)}
                    onChange={(e) => handleProfileChange('has_cold_box', e.target.checked)}
                    style={{ width: '18px', height: '18px', accentColor: 'var(--green-dark)' }}
                  />
                  <span style={{ fontSize: '0.9rem', color: 'var(--deep)', fontWeight: 600 }}>
                    Equipped with Insulated Cold Box (Enables perishables & cold chain rescue)
                  </span>
                </label>
              </div>
            </div>
          </div>
        )}

        {/* Save Bar */}
        <div style={{ display: 'flex', gap: '14px', alignItems: 'center', justifyContent: 'flex-end', marginTop: '10px' }}>
          <Button
            type="submit"
            variant="primary"
            size="lg"
            disabled={loading || fetching}
          >
            {loading ? 'Saving Changes...' : 'Save Profile Changes'}
          </Button>
        </div>
      </form>
    </div>
  );
};

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: '0.84rem',
  fontWeight: 700,
  color: 'var(--deep)',
  marginBottom: '6px',
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '11px 14px',
  borderRadius: 'var(--r-card-sm)',
  border: '1px solid var(--line)',
  background: 'var(--paper)',
  fontSize: '0.92rem',
  color: 'var(--ink)',
  outline: 'none',
  fontFamily: 'inherit',
  transition: 'border-color 0.2s ease',
};

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { useSessionStore } from '../../store/session';
import { useUiStore } from '../../store/ui';
import { api } from '../../lib/api';
import { Button } from '../../components/ui/Button';
import type { Role, User } from '../../types/api';
import { RegistrationForm } from './RegistrationForm';

export const AuthPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const initialRole = (searchParams.get('role') as Role) || 'donor';

  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [role, setRole] = useState<Role>(initialRole);
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);

  const { setSession } = useSessionStore();
  const { addToast } = useUiStore();

  // If a 'role' param is present and comes from an AuthGuard redirect,
  // auto-trigger demo login immediately so UX is seamless
  useEffect(() => {
    const fromGuard = (location.state as { from?: string } | null)?.from;
    const roleParam = searchParams.get('role') as Role | null;
    if (roleParam && fromGuard) {
      // Auto-login with the hinted role
      handleLogin(roleParam);
    }
    // Only run on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLogin = async (selectedRole: Role) => {
    setLoading(true);
    try {
      // 1. Authenticate via /auth/demo
      const tokens = await api.post<{
        access_token: string;
        refresh_token: string;
        token_type: string;
        expires_in: number;
        user_id: string;
        role: Role;
      }>('/auth/demo', {
        role: selectedRole,
      });

      // Set tokens in session store so subsequent requests include Authorization header
      useSessionStore.getState().setTokens(tokens.access_token, tokens.refresh_token);

      // 2. Fetch authenticated user profile
      const user = await api.get<User>('/auth/me');

      setSession(user, {
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
      });
      addToast(`Welcome back, ${user.name}!`, 'success');

      // Navigate back to where the user was trying to go, or to their dashboard
      const from = (location.state as { from?: string } | null)?.from;
      if (from) {
        navigate(from, { replace: true });
      } else if (selectedRole === 'donor') navigate('/donor');
      else if (selectedRole === 'recipient') navigate('/org');
      else if (selectedRole === 'driver') navigate('/driver');
      else navigate('/ops');
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Sign in failed';
      addToast(errorMsg, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRegistrationSuccess = (selectedRole: Role) => {
    const from = (location.state as { from?: string } | null)?.from;
    if (from) {
      navigate(from, { replace: true });
    } else if (selectedRole === 'donor') navigate('/donor');
    else if (selectedRole === 'recipient') navigate('/org');
    else if (selectedRole === 'driver') navigate('/driver');
    else navigate('/ops');
  };

  return (
    <div
      style={{
        minHeight: '80vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '30px 20px',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '480px',
          background: 'var(--white)',
          border: '1px solid var(--line)',
          borderRadius: 'var(--r-card-lg)',
          boxShadow: 'var(--shadow)',
          padding: '36px 30px',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: 'var(--r-logo)',
              background: 'var(--green)',
              color: 'var(--deep)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '14px',
              fontSize: '22px',
            }}
          >
            ⏳
          </div>
          <h2 style={{ fontSize: '1.9rem', fontWeight: 800, color: 'var(--deep)', margin: '0 0 6px' }}>
            Enter GoldenHour
          </h2>
          <p style={{ color: 'var(--muted)', fontSize: '0.92rem' }}>
            Choose your role in the Jaipur food rescue network
          </p>
        </div>

        {/* Role Segmented Buttons */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '6px',
            background: 'var(--paper)',
            padding: '4px',
            borderRadius: 'var(--r-pill)',
            marginBottom: '24px',
          }}
        >
          {(['donor', 'recipient', 'driver', 'admin'] as Role[]).map((r) => {
            const isSelected = role === r;
            const labels: Record<Role, string> = {
              donor: 'Donor',
              recipient: 'Shelter',
              driver: 'Driver',
              admin: 'Ops',
            };
            return (
              <button
                key={r}
                type="button"
                onClick={() => setRole(r)}
                style={{
                  padding: '8px 4px',
                  borderRadius: 'var(--r-pill)',
                  fontSize: '0.82rem',
                  fontWeight: isSelected ? 700 : 500,
                  background: isSelected ? 'var(--deep)' : 'transparent',
                  color: isSelected ? 'var(--white)' : 'var(--muted)',
                  transition: 'all 0.2s var(--ease)',
                }}
              >
                {labels[r]}
              </button>
            );
          })}
        </div>

        {mode === 'login' ? (
          <>
            {/* Email or Phone field */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '6px' }}>
                Email or Registered Phone
              </label>
              <input
                type="text"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. contact@spiceroutejaipur.com"
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  borderRadius: 'var(--r-card-sm)',
                  border: '1px solid var(--line)',
                  background: 'var(--paper)',
                  fontSize: '0.95rem',
                  color: 'var(--ink)',
                  outline: 'none',
                }}
              />
            </div>

            {/* Login Button */}
            <Button
              variant="primary"
              size="lg"
              block
              arrow
              onClick={() => handleLogin(role)}
              disabled={loading}
            >
              {loading ? 'Entering...' : `Enter as ${role.toUpperCase()}`}
            </Button>
            
            <div style={{ marginTop: '16px', textAlign: 'center' }}>
              <span style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>New here? </span>
              <button 
                type="button" 
                onClick={() => setMode('register')}
                style={{ background: 'none', border: 'none', color: 'var(--green-dark)', fontWeight: 600, cursor: 'pointer', fontSize: '0.9rem' }}
              >
                Sign up instead
              </button>
            </div>

            {/* Quick Demo Logins Section */}
            <div style={{ marginTop: '28px', paddingTop: '20px', borderTop: '1px solid var(--line)' }}>
              <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.6px', color: 'var(--muted)', marginBottom: '12px', textAlign: 'center', fontWeight: 700 }}>
                Instant Hackathon Demo Logins (Jaipur)
              </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <button
              type="button"
              onClick={() => handleLogin('donor')}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                background: 'var(--paper)',
                borderRadius: 'var(--r-card-sm)',
                border: '1px solid var(--line)',
                fontSize: '0.86rem',
                textAlign: 'left',
              }}
            >
              <span>🍲 <strong>Spice Route Kitchen</strong> (Donor, C-Scheme)</span>
              <span style={{ color: 'var(--green-dark)', fontWeight: 700 }}>Launch →</span>
            </button>

            <button
              type="button"
              onClick={() => handleLogin('recipient')}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                background: 'var(--paper)',
                borderRadius: 'var(--r-card-sm)',
                border: '1px solid var(--line)',
                fontSize: '0.86rem',
                textAlign: 'left',
              }}
            >
              <span>🏠 <strong>Asha Shelter Foundation</strong> (Shelter, Malviya Nagar)</span>
              <span style={{ color: 'var(--blue-text)', fontWeight: 700 }}>Launch →</span>
            </button>

            <button
              type="button"
              onClick={() => handleLogin('driver')}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                background: 'var(--paper)',
                borderRadius: 'var(--r-card-sm)',
                border: '1px solid var(--line)',
                fontSize: '0.86rem',
                textAlign: 'left',
              }}
            >
              <span>🛵 <strong>Rajesh Kumar</strong> (Driver, E-Rickshaw)</span>
              <span style={{ color: 'var(--deep)', fontWeight: 700 }}>Launch →</span>
            </button>

            <button
              type="button"
              onClick={() => handleLogin('admin')}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                background: 'var(--paper)',
                borderRadius: 'var(--r-card-sm)',
                border: '1px solid var(--line)',
                fontSize: '0.86rem',
                textAlign: 'left',
              }}
            >
              <span>⚡ <strong>Jaipur Ops Live Console</strong> (Realtime Map)</span>
              <span style={{ color: 'var(--red)', fontWeight: 700 }}>Launch →</span>
            </button>
          </div>
        </div>
      </>
    ) : (
      <RegistrationForm 
        role={role} 
        onSuccess={handleRegistrationSuccess} 
        onCancel={() => setMode('login')} 
      />
    )}
      </div>
    </div>
  );
};

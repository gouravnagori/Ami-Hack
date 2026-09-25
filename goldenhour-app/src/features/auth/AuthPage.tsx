import React, { useState } from 'react';
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
  const initialMode = searchParams.get('mode') === 'register' ? 'register' : 'login';

  const [mode, setMode] = useState<'login' | 'register'>(initialMode);
  const [loginMethod, setLoginMethod] = useState<'password' | 'otp'>('password');
  const [role, setRole] = useState<Role>(initialRole);

  // Password Login Fields
  const [emailOrPhone, setEmailOrPhone] = useState('');
  const [password, setPassword] = useState('');

  // OTP Login Fields
  const [otpEmail, setOtpEmail] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [sendingOtp, setSendingOtp] = useState(false);

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);

  const { setSession } = useSessionStore();
  const { addToast } = useUiStore();

  const getFriendlyLoginError = (err: unknown): { title: string; message: string } => {
    const raw = err instanceof Error ? err.message : String(err || '');
    const lower = raw.toLowerCase();

    if (
      lower.includes('credential') ||
      lower.includes('unauthenticated') ||
      lower.includes('401') ||
      lower.includes('verify your phone') ||
      lower.includes('invalid')
    ) {
      return {
        title: 'Incorrect Credentials',
        message:
          "We could not find an account with those details or the password was incorrect. If you don't have an account yet, please click 'Create Account' above.",
      };
    }

    if (lower.includes('expired') || lower.includes('not requested')) {
      return {
        title: 'Code Expired',
        message: 'Your verification code has expired. Please click "Resend Code" to receive a new one.',
      };
    }

    if (lower.includes('no account found') || lower.includes('404')) {
      return {
        title: 'Account Not Found',
        message: "No account exists with this email address yet. Please click 'Create Account' to register.",
      };
    }

    if (lower.includes('suspended') || lower.includes('inactive')) {
      return {
        title: 'Account Inactive',
        message: 'Your account is currently inactive. Please contact the GoldenHour Operations team for assistance.',
      };
    }

    if (lower.includes('failed to fetch') || lower.includes('network') || lower.includes('connection')) {
      return {
        title: 'Cannot Reach Server',
        message:
          'Unable to reach the GoldenHour backend server. Please verify all services are running and try again.',
      };
    }

    return {
      title: 'Sign In Failed',
      message: raw || 'An unexpected issue occurred while signing in. Please check your credentials and try again.',
    };
  };

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setInfoMessage(null);

    const identifier = emailOrPhone.trim();
    if (!identifier) {
      setErrorMessage('Please enter your registered email address or mobile phone number.');
      return;
    }
    if (!password) {
      setErrorMessage('Please enter your account password.');
      return;
    }

    setLoading(true);
    try {
      const tokens = await api.post<{
        access_token: string;
        refresh_token: string;
        token_type: string;
        expires_in: number;
        user_id: string;
        role: Role;
      }>('/auth/login', {
        phone_or_email: identifier,
        password: password,
      });

      useSessionStore.getState().setTokens(tokens.access_token, tokens.refresh_token);
      const user = await api.get<User>('/auth/me');

      setSession(user, {
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
      });

      addToast(`Welcome back, ${user.name}!`, 'success');
      redirectAfterAuth(user.role);
    } catch (err: unknown) {
      const parsed = getFriendlyLoginError(err);
      setErrorMessage(parsed.message);
      addToast(parsed.title, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSendLoginOtp = async () => {
    setErrorMessage(null);
    setInfoMessage(null);

    const cleanEmail = otpEmail.trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes('@') || !cleanEmail.includes('.')) {
      setErrorMessage('Please enter a valid email address to receive your login code.');
      return;
    }

    setSendingOtp(true);
    try {
      await api.post<{ success: boolean; message: string }>('/auth/send-otp', {
        email: cleanEmail,
        purpose: 'login',
      });

      setOtpSent(true);
      setInfoMessage(`We've sent a 6-digit login code to ${cleanEmail}. Please check your inbox.`);
      addToast('Login code sent to your email!', 'success');
    } catch (err: unknown) {
      const parsed = getFriendlyLoginError(err);
      setErrorMessage(parsed.message);
      addToast(parsed.title, 'error');
    } finally {
      setSendingOtp(false);
    }
  };

  const handleOtpLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const cleanEmail = otpEmail.trim().toLowerCase();
    const cleanOtp = otpCode.trim();

    if (!cleanEmail) {
      setErrorMessage('Please enter your registered email address.');
      return;
    }
    if (!cleanOtp || cleanOtp.length < 4) {
      setErrorMessage('Please enter the 6-digit code received in your email.');
      return;
    }

    setLoading(true);
    try {
      const tokens = await api.post<{
        access_token: string;
        refresh_token: string;
        token_type: string;
        expires_in: number;
        user_id: string;
        role: Role;
      }>('/auth/login-otp', {
        email: cleanEmail,
        otp: cleanOtp,
      });

      useSessionStore.getState().setTokens(tokens.access_token, tokens.refresh_token);
      const user = await api.get<User>('/auth/me');

      setSession(user, {
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
      });

      addToast(`Welcome back, ${user.name}!`, 'success');
      redirectAfterAuth(user.role);
    } catch (err: unknown) {
      const parsed = getFriendlyLoginError(err);
      setErrorMessage(parsed.message);
      addToast(parsed.title, 'error');
    } finally {
      setLoading(false);
    }
  };

  const redirectAfterAuth = (userRole: Role) => {
    const from = (location.state as { from?: string } | null)?.from;
    if (from) {
      navigate(from, { replace: true });
    } else if (userRole === 'donor') navigate('/donor');
    else if (userRole === 'recipient') navigate('/org');
    else if (userRole === 'driver') navigate('/driver');
    else navigate('/ops');
  };

  const handleRegistrationSuccess = (selectedRole: Role) => {
    redirectAfterAuth(selectedRole);
  };

  const roleLabelMap: Record<Role, string> = {
    donor: 'Food Donor',
    recipient: 'Shelter Hub',
    driver: 'Rescue Driver',
    admin: 'Ops Team',
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
          maxWidth: '520px',
          background: 'var(--white)',
          border: '1px solid var(--line)',
          borderRadius: 'var(--r-card-lg)',
          boxShadow: 'var(--shadow)',
          padding: '32px 28px',
        }}
      >
        {/* Header Branding */}
        <div style={{ textAlign: 'center', marginBottom: '22px' }}>
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
              marginBottom: '10px',
              fontSize: '22px',
            }}
          >
            ⏳
          </div>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--deep)', margin: '0 0 6px' }}>
            GoldenHour Portal
          </h2>
          <p style={{ color: 'var(--muted)', fontSize: '0.9rem', margin: 0 }}>
            Hyper-local surplus food rescue & redistribution network
          </p>
        </div>

        {/* Tab Toggle: Sign In vs Create Account */}
        <div
          style={{
            display: 'flex',
            background: 'var(--paper)',
            borderRadius: 'var(--r-pill)',
            padding: '4px',
            marginBottom: '20px',
          }}
        >
          <button
            type="button"
            onClick={() => {
              setMode('login');
              setErrorMessage(null);
              setInfoMessage(null);
            }}
            style={{
              flex: 1,
              padding: '9px 16px',
              borderRadius: 'var(--r-pill)',
              fontSize: '0.9rem',
              fontWeight: mode === 'login' ? 700 : 500,
              background: mode === 'login' ? 'var(--deep)' : 'transparent',
              color: mode === 'login' ? 'var(--white)' : 'var(--muted)',
              border: 'none',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('register');
              setErrorMessage(null);
              setInfoMessage(null);
            }}
            style={{
              flex: 1,
              padding: '9px 16px',
              borderRadius: 'var(--r-pill)',
              fontSize: '0.9rem',
              fontWeight: mode === 'register' ? 700 : 500,
              background: mode === 'register' ? 'var(--deep)' : 'transparent',
              color: mode === 'register' ? 'var(--white)' : 'var(--muted)',
              border: 'none',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            Create Account
          </button>
        </div>

        {/* Role Segmented Buttons */}
        <div style={{ marginBottom: '20px' }}>
          <label
            style={{
              display: 'block',
              fontSize: '0.8rem',
              fontWeight: 700,
              color: 'var(--muted)',
              marginBottom: '6px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            Select Your Role
          </label>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '6px',
              background: 'var(--paper)',
              padding: '4px',
              borderRadius: 'var(--r-pill)',
            }}
          >
            {(['donor', 'recipient', 'driver', 'admin'] as Role[]).map((r) => {
              const isSelected = role === r;
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
                    background: isSelected ? 'var(--green-dark)' : 'transparent',
                    color: isSelected ? 'var(--white)' : 'var(--muted)',
                    border: 'none',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                >
                  {roleLabelMap[r]}
                </button>
              );
            })}
          </div>
        </div>

        {/* Info Banner */}
        {infoMessage && (
          <div
            style={{
              background: '#f0fdf4',
              border: '1px solid #bbf7d0',
              borderRadius: 'var(--r-card-sm)',
              padding: '12px 14px',
              marginBottom: '16px',
              display: 'flex',
              gap: '10px',
              alignItems: 'center',
            }}
          >
            <span style={{ fontSize: '18px' }}>📬</span>
            <div style={{ color: '#166534', fontSize: '0.86rem', lineHeight: 1.4 }}>
              {infoMessage}
            </div>
          </div>
        )}

        {/* Friendly Error Banner for Non-Technical Users */}
        {errorMessage && (
          <div
            style={{
              background: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: 'var(--r-card-sm)',
              padding: '14px 16px',
              marginBottom: '20px',
              display: 'flex',
              gap: '12px',
              alignItems: 'flex-start',
            }}
          >
            <span style={{ fontSize: '20px', lineHeight: 1 }}>⚠️</span>
            <div style={{ flex: 1 }}>
              <strong style={{ color: '#991b1b', fontSize: '0.9rem', display: 'block', marginBottom: '4px' }}>
                Unable to Sign In
              </strong>
              <div style={{ color: '#b91c1c', fontSize: '0.85rem', lineHeight: 1.45 }}>
                {errorMessage}
              </div>
              <button
                type="button"
                onClick={() => {
                  setMode('register');
                  setErrorMessage(null);
                  setInfoMessage(null);
                }}
                style={{
                  marginTop: '10px',
                  background: 'none',
                  border: 'none',
                  padding: 0,
                  color: '#991b1b',
                  fontWeight: 700,
                  fontSize: '0.84rem',
                  cursor: 'pointer',
                  textDecoration: 'underline',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                New user? Click here to create your account →
              </button>
            </div>
          </div>
        )}

        {mode === 'login' ? (
          <div>
            {/* Login Method Toggle: Password vs Email OTP */}
            <div
              style={{
                display: 'flex',
                gap: '8px',
                marginBottom: '18px',
                borderBottom: '1px solid var(--line)',
                paddingBottom: '12px',
              }}
            >
              <button
                type="button"
                onClick={() => {
                  setLoginMethod('password');
                  setErrorMessage(null);
                  setInfoMessage(null);
                }}
                style={{
                  flex: 1,
                  padding: '7px 12px',
                  borderRadius: 'var(--r-card-sm)',
                  border: loginMethod === 'password' ? '1px solid var(--deep)' : '1px solid var(--line)',
                  background: loginMethod === 'password' ? 'var(--deep)' : 'var(--paper)',
                  color: loginMethod === 'password' ? 'var(--white)' : 'var(--muted)',
                  fontSize: '0.84rem',
                  fontWeight: loginMethod === 'password' ? 700 : 500,
                  cursor: 'pointer',
                }}
              >
                🔑 Password Login
              </button>
              <button
                type="button"
                onClick={() => {
                  setLoginMethod('otp');
                  setErrorMessage(null);
                  setInfoMessage(null);
                }}
                style={{
                  flex: 1,
                  padding: '7px 12px',
                  borderRadius: 'var(--r-card-sm)',
                  border: loginMethod === 'otp' ? '1px solid var(--deep)' : '1px solid var(--line)',
                  background: loginMethod === 'otp' ? 'var(--deep)' : 'var(--paper)',
                  color: loginMethod === 'otp' ? 'var(--white)' : 'var(--muted)',
                  fontSize: '0.84rem',
                  fontWeight: loginMethod === 'otp' ? 700 : 500,
                  cursor: 'pointer',
                }}
              >
                ✉️ Email OTP Login
              </button>
            </div>

            {loginMethod === 'password' ? (
              <form onSubmit={handlePasswordLogin}>
                {/* Email or Phone field */}
                <div style={{ marginBottom: '14px' }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '6px' }}>
                    Email Address or Registered Phone Number *
                  </label>
                  <input
                    type="text"
                    required
                    value={emailOrPhone}
                    onChange={(e) => {
                      setEmailOrPhone(e.target.value);
                      if (errorMessage) setErrorMessage(null);
                    }}
                    placeholder="e.g. sajalgoyal2007@gmail.com or 9829012345"
                    style={inputStyle}
                  />
                </div>

                {/* Password field */}
                <div style={{ marginBottom: '20px' }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '6px' }}>
                    Password *
                  </label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (errorMessage) setErrorMessage(null);
                    }}
                    placeholder="Enter your account password"
                    style={inputStyle}
                  />
                </div>

                {/* Login Button */}
                <Button variant="primary" size="lg" block arrow type="submit" disabled={loading}>
                  {loading ? 'Verifying Account...' : `Sign In as ${roleLabelMap[role]}`}
                </Button>
              </form>
            ) : (
              <form onSubmit={handleOtpLogin}>
                {/* OTP Email Input */}
                <div style={{ marginBottom: '14px' }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '6px' }}>
                    Registered Email Address *
                  </label>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <input
                      type="email"
                      required
                      value={otpEmail}
                      onChange={(e) => {
                        setOtpEmail(e.target.value);
                        if (errorMessage) setErrorMessage(null);
                      }}
                      placeholder="e.g. sajalgoyal2007@gmail.com"
                      style={{ ...inputStyle, flex: 1 }}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      disabled={sendingOtp || !otpEmail.includes('@')}
                      onClick={handleSendLoginOtp}
                      style={{ whiteSpace: 'nowrap', padding: '0 16px' }}
                    >
                      {sendingOtp ? 'Sending...' : otpSent ? 'Resend' : 'Send Code'}
                    </Button>
                  </div>
                  <span style={{ display: 'block', fontSize: '0.74rem', color: 'var(--muted)', marginTop: '4px' }}>
                    We will send a 6-digit login code to your email inbox.
                  </span>
                </div>

                {/* 6-digit OTP Code Input */}
                {otpSent && (
                  <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--deep)', marginBottom: '6px' }}>
                      Enter 6-Digit Email Verification Code *
                    </label>
                    <input
                      type="text"
                      maxLength={6}
                      required
                      value={otpCode}
                      onChange={(e) => {
                        setOtpCode(e.target.value.replace(/\D/g, ''));
                        if (errorMessage) setErrorMessage(null);
                      }}
                      placeholder="Enter 6-digit code"
                      style={{
                        ...inputStyle,
                        letterSpacing: '6px',
                        fontSize: '1.2rem',
                        fontWeight: 700,
                        textAlign: 'center',
                      }}
                    />
                  </div>
                )}

                {/* Submit OTP */}
                <Button
                  variant="primary"
                  size="lg"
                  block
                  arrow
                  type="submit"
                  disabled={loading || !otpSent || otpCode.length < 6}
                >
                  {loading ? 'Verifying Code...' : 'Verify Code & Sign In'}
                </Button>
              </form>
            )}

            {/* Switch to Register */}
            <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '0.88rem', color: 'var(--muted)' }}>
              Don't have an account yet?{' '}
              <button
                type="button"
                onClick={() => {
                  setMode('register');
                  setErrorMessage(null);
                  setInfoMessage(null);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--green-dark)',
                  fontWeight: 700,
                  cursor: 'pointer',
                  fontSize: '0.88rem',
                }}
              >
                Create Account & Register Now →
              </button>
            </div>
          </div>
        ) : (
          <RegistrationForm
            role={role}
            onSuccess={handleRegistrationSuccess}
            onCancel={() => {
              setMode('login');
              setErrorMessage(null);
              setInfoMessage(null);
            }}
          />
        )}
      </div>
    </div>
  );
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '12px 14px',
  borderRadius: 'var(--r-card-sm)',
  border: '1px solid var(--line)',
  background: 'var(--paper)',
  fontSize: '0.95rem',
  color: 'var(--ink)',
  outline: 'none',
  boxSizing: 'border-box',
};

import React, { useState } from 'react';
import { useSessionStore } from '../../store/session';
import { useUiStore } from '../../store/ui';
import { api } from '../../lib/api';
import { Button } from '../../components/ui/Button';
import type { Role, User } from '../../types/api';

interface RegistrationFormProps {
  role: Role;
  onSuccess: (role: Role) => void;
  onCancel: () => void;
}

export const RegistrationForm: React.FC<RegistrationFormProps> = ({ role, onSuccess, onCancel }) => {
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);
  const [showSignInAction, setShowSignInAction] = useState(false);
  const { addToast } = useUiStore();

  // Basic Account Credentials
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [city, setCity] = useState('Jaipur');

  // Email Verification OTP State
  const [otpCode, setOtpCode] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [sendingOtp, setSendingOtp] = useState(false);

  // Role Specific Fields
  // Donor
  const [donorOrgName, setDonorOrgName] = useState('');
  const [donorAddress, setDonorAddress] = useState('');
  const [donorFoodCategory, setDonorFoodCategory] = useState('restaurant');

  // Recipient / Shelter
  const [shelterName, setShelterName] = useState('');
  const [shelterAddress, setShelterAddress] = useState('');
  const [recipientCapacity, setRecipientCapacity] = useState('150');
  const [recipientRestrictions, setRecipientRestrictions] = useState('None (All meals welcome)');

  // Driver
  const [driverVehicleType, setDriverVehicleType] = useState('scooter');
  const [driverVehicleNumber, setDriverVehicleNumber] = useState('');
  const [driverCapacity, setDriverCapacity] = useState('60');
  const [driverColdBox, setDriverColdBox] = useState(false);
  const [driverArea, setDriverArea] = useState('');

  // Ops / Admin
  const [opsDepartment, setOpsDepartment] = useState('Central Jaipur Dispatch');

  const getFriendlyRegistrationError = (
    err: unknown
  ): { title: string; message: string; showSignIn: boolean } => {
    const raw = err instanceof Error ? err.message : String(err || '');
    const lower = raw.toLowerCase();

    if (
      lower.includes('already exists') ||
      lower.includes('already taken') ||
      lower.includes('conflict') ||
      lower.includes('409')
    ) {
      return {
        title: 'Account Already Exists',
        message:
          'An account with this email address or phone number has already been registered. Please sign in with your password instead.',
        showSignIn: true,
      };
    }

    if (lower.includes('verification code') || lower.includes('otp')) {
      return {
        title: 'Email Verification Notice',
        message: raw || 'Please enter the 6-digit verification code sent to your email inbox.',
        showSignIn: false,
      };
    }

    if (lower.includes('password') && (lower.includes('short') || lower.includes('least') || lower.includes('length'))) {
      return {
        title: 'Password Too Short',
        message: 'Please choose a password with at least 6 characters for your security.',
        showSignIn: false,
      };
    }

    if (lower.includes('phone') && (lower.includes('invalid') || lower.includes('digits') || lower.includes('format'))) {
      return {
        title: 'Invalid Phone Number',
        message: 'Please enter a complete 10-digit mobile number so we can coordinate food rescues.',
        showSignIn: false,
      };
    }

    if (lower.includes('email') && (lower.includes('invalid') || lower.includes('format'))) {
      return {
        title: 'Invalid Email Address',
        message: 'Please enter a valid email address (e.g. name@example.com) to receive updates.',
        showSignIn: false,
      };
    }

    if (lower.includes('failed to fetch') || lower.includes('network') || lower.includes('connection')) {
      return {
        title: 'Server Connection Issue',
        message: 'Unable to reach the GoldenHour service. Please verify that the backend is running and try again.',
        showSignIn: false,
      };
    }

    return {
      title: 'Registration Notice',
      message: raw || 'Please verify that all required information is filled out properly and try again.',
      showSignIn: false,
    };
  };

  const handleSendVerificationOtp = async () => {
    setErrorMessage(null);
    setInfoMessage(null);

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes('@') || !cleanEmail.includes('.')) {
      setErrorMessage('Please enter a valid email address first to receive your verification code.');
      return;
    }

    setSendingOtp(true);
    try {
      await api.post<{ success: boolean; message: string }>('/auth/send-otp', {
        email: cleanEmail,
        purpose: 'register',
        name: name.trim() || 'Partner',
      });

      setOtpSent(true);
      setInfoMessage(`Verification code sent to ${cleanEmail}. Please enter the 6-digit code below.`);
      addToast('Verification code sent to your email!', 'success');
    } catch (err: unknown) {
      const parsed = getFriendlyRegistrationError(err);
      setErrorMessage(parsed.message);
      setShowSignInAction(parsed.showSignIn);
      addToast(parsed.title, 'error');
    } finally {
      setSendingOtp(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setShowSignInAction(false);

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes('@') || !cleanEmail.includes('.')) {
      setErrorMessage('Please enter a valid email address (e.g. name@gmail.com).');
      return;
    }

    const cleanPhone = phone.trim();
    if (cleanPhone.replace(/\D/g, '').length < 10) {
      setErrorMessage('Please enter a complete 10-digit mobile phone number.');
      return;
    }

    if (password.length < 6) {
      setErrorMessage('Password must be at least 6 characters long.');
      return;
    }

    // Require email verification code
    if (!otpSent) {
      setErrorMessage('Please click "Send Verification Code" to verify your email address.');
      return;
    }
    if (!otpCode || otpCode.trim().length < 6) {
      setErrorMessage('Please enter the 6-digit verification code sent to your email.');
      return;
    }

    setLoading(true);
    try {
      let profile: Record<string, any> = {};

      if (role === 'donor') {
        profile = {
          org_name: donorOrgName.trim() || name.trim(),
          pickup_address: donorAddress.trim(),
          address: donorAddress.trim(),
          food_category: donorFoodCategory,
          contact_person: name.trim(),
        };
      } else if (role === 'recipient') {
        profile = {
          name: shelterName.trim() || name.trim(),
          address: shelterAddress.trim(),
          max_capacity_portions: parseInt(recipientCapacity, 10) || 150,
          food_restrictions: recipientRestrictions.trim(),
          contact_person: name.trim(),
          contact_phone: cleanPhone,
        };
      } else if (role === 'driver') {
        profile = {
          vehicle_type: driverVehicleType,
          vehicle_number: driverVehicleNumber.trim() || 'Pending Registration',
          capacity_portions: parseInt(driverCapacity, 10) || 60,
          has_cold_box: driverColdBox,
          operating_area: driverArea.trim() || 'Jaipur Central',
        };
      } else if (role === 'admin') {
        profile = {
          department: opsDepartment.trim(),
          operator_title: 'Dispatcher',
        };
      }

      const payload = {
        role,
        name: name.trim(),
        phone: cleanPhone,
        email: cleanEmail,
        password,
        city: city.trim() || 'Jaipur',
        profile,
        otp: otpCode.trim(),
      };

      const tokens = await api.post<{
        access_token: string;
        refresh_token: string;
        token_type: string;
        expires_in: number;
        user_id: string;
        role: Role;
      }>('/auth/register', payload);

      // Store tokens
      useSessionStore.getState().setTokens(tokens.access_token, tokens.refresh_token);

      // Fetch user profile from /auth/me
      const user = await api.get<User>('/auth/me');

      useSessionStore.getState().setSession(user, {
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
      });

      addToast(`Account created & email verified! Welcome to GoldenHour, ${user.name}`, 'success');
      onSuccess(role);
    } catch (err: unknown) {
      const parsed = getFriendlyRegistrationError(err);
      setErrorMessage(parsed.message);
      setShowSignInAction(parsed.showSignIn);
      addToast(parsed.title, 'error');
    } finally {
      setLoading(false);
    }
  };

  const roleLabelMap: Record<Role, string> = {
    donor: 'Food Donor (Restaurant / Kitchen)',
    recipient: 'Shelter / NGO (Food Recipient)',
    driver: 'Rescue Driver (Logistics Partner)',
    admin: 'Operations Team (Control Room)',
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div style={{ borderBottom: '1px solid var(--line)', paddingBottom: '10px', marginBottom: '4px' }}>
        <h3 style={{ margin: '0 0 4px', color: 'var(--deep)', fontSize: '1.2rem', fontWeight: 800 }}>
          Create {roleLabelMap[role]} Account
        </h3>
        <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--muted)' }}>
          Please fill out your verified details. All information is kept safe and used for live coordination.
        </p>
      </div>

      {/* Info Banner */}
      {infoMessage && (
        <div
          style={{
            background: '#f0fdf4',
            border: '1px solid #bbf7d0',
            borderRadius: 'var(--r-card-sm)',
            padding: '12px 14px',
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

      {/* Friendly Error Banner */}
      {errorMessage && (
        <div
          style={{
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: 'var(--r-card-sm)',
            padding: '14px 16px',
            marginBottom: '4px',
            display: 'flex',
            gap: '12px',
            alignItems: 'flex-start',
          }}
        >
          <span style={{ fontSize: '20px', lineHeight: 1 }}>⚠️</span>
          <div style={{ flex: 1 }}>
            <strong style={{ color: '#991b1b', fontSize: '0.9rem', display: 'block', marginBottom: '4px' }}>
              Registration Notice
            </strong>
            <div style={{ color: '#b91c1c', fontSize: '0.85rem', lineHeight: 1.45 }}>
              {errorMessage}
            </div>
            {showSignInAction && (
              <button
                type="button"
                onClick={onCancel}
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
                Go to Sign In page →
              </button>
            )}
          </div>
        </div>
      )}

      {/* Account Info Section */}
      <div>
        <label style={labelStyle}>Full Name *</label>
        <input
          type="text"
          placeholder="e.g. Ramesh Sharma"
          required
          value={name}
          onChange={(e) => {
            setName(e.target.value);
            if (errorMessage) setErrorMessage(null);
          }}
          style={inputStyle}
        />
      </div>

      {/* Email Field with Verification Button */}
      <div>
        <label style={labelStyle}>Email Address (Requires Verification) *</label>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            type="email"
            placeholder="e.g. ramesh@example.com"
            required
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              setOtpSent(false);
              setOtpCode('');
              if (errorMessage) setErrorMessage(null);
            }}
            style={{ ...inputStyle, flex: 1 }}
          />
          <Button
            type="button"
            variant="outline"
            disabled={sendingOtp || !email.includes('@')}
            onClick={handleSendVerificationOtp}
            style={{ whiteSpace: 'nowrap', padding: '0 16px' }}
          >
            {sendingOtp ? 'Sending...' : otpSent ? 'Resend Code' : 'Send Code'}
          </Button>
        </div>
        <span style={subHintStyle}>
          {otpSent ? '✓ Verification code sent! Check your email.' : 'Click "Send Code" to verify your email inbox.'}
        </span>
      </div>

      {/* 6-Digit Email Verification Code Input */}
      {otpSent && (
        <div style={{ background: '#f0fdf4', padding: '12px 14px', borderRadius: 'var(--r-card-sm)', border: '1px solid #bbf7d0' }}>
          <label style={{ ...labelStyle, color: '#166534' }}>
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
              background: '#ffffff',
            }}
          />
        </div>
      )}

      {/* Phone Number */}
      <div>
        <label style={labelStyle}>Mobile Phone Number *</label>
        <input
          type="tel"
          placeholder="e.g. 9829012345"
          required
          value={phone}
          onChange={(e) => {
            setPhone(e.target.value);
            if (errorMessage) setErrorMessage(null);
          }}
          style={inputStyle}
        />
        <span style={subHintStyle}>Used for pickup coordination & delivery notifications</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        <div>
          <label style={labelStyle}>Password (min 6 characters) *</label>
          <input
            type="password"
            placeholder="Create secure password"
            required
            minLength={6}
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (errorMessage) setErrorMessage(null);
            }}
            style={inputStyle}
          />
        </div>
        <div>
          <label style={labelStyle}>City *</label>
          <input
            type="text"
            placeholder="e.g. Jaipur"
            required
            value={city}
            onChange={(e) => setCity(e.target.value)}
            style={inputStyle}
          />
        </div>
      </div>

      {/* Role-Specific Fields */}
      {role === 'donor' && (
        <div style={roleBoxStyle}>
          <div style={roleTitleStyle}>🍲 Donor Business & Kitchen Details</div>
          <div style={{ marginBottom: '10px' }}>
            <label style={labelStyle}>Establishment / Restaurant Name *</label>
            <input
              type="text"
              placeholder="e.g. Royal Haveli Kitchen & Sweets"
              required
              value={donorOrgName}
              onChange={(e) => setDonorOrgName(e.target.value)}
              style={inputStyle}
            />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label style={labelStyle}>Pickup Address *</label>
            <input
              type="text"
              placeholder="e.g. 24, MI Road, C-Scheme, Jaipur"
              required
              value={donorAddress}
              onChange={(e) => setDonorAddress(e.target.value)}
              style={inputStyle}
            />
          </div>
          <div>
            <label style={labelStyle}>Type of Establishment</label>
            <select
              value={donorFoodCategory}
              onChange={(e) => setDonorFoodCategory(e.target.value)}
              style={inputStyle}
            >
              <option value="restaurant">Restaurant / Dining</option>
              <option value="caterer">Banquet / Event Caterer</option>
              <option value="bakery">Bakery / Confectionery</option>
              <option value="hotel">Hotel / Kitchen</option>
              <option value="grocery">Grocery / Fresh Produce</option>
              <option value="corporate">Corporate / Institutional Canteen</option>
            </select>
          </div>
        </div>
      )}

      {role === 'recipient' && (
        <div style={roleBoxStyle}>
          <div style={roleTitleStyle}>🏠 Shelter / NGO Facility Details</div>
          <div style={{ marginBottom: '10px' }}>
            <label style={labelStyle}>Shelter / NGO Name *</label>
            <input
              type="text"
              placeholder="e.g. Apna Ghar Shelter Home"
              required
              value={shelterName}
              onChange={(e) => setShelterName(e.target.value)}
              style={inputStyle}
            />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label style={labelStyle}>Facility Delivery Address *</label>
            <input
              type="text"
              placeholder="e.g. Plot 12, Sector 5, Malviya Nagar, Jaipur"
              required
              value={shelterAddress}
              onChange={(e) => setShelterAddress(e.target.value)}
              style={inputStyle}
            />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div>
              <label style={labelStyle}>Meal Intake Capacity (Portions) *</label>
              <input
                type="number"
                min="10"
                max="5000"
                required
                value={recipientCapacity}
                onChange={(e) => setRecipientCapacity(e.target.value)}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Food Restrictions / Preference</label>
              <input
                type="text"
                placeholder="e.g. Vegetarian only, All meals"
                value={recipientRestrictions}
                onChange={(e) => setRecipientRestrictions(e.target.value)}
                style={inputStyle}
              />
            </div>
          </div>
        </div>
      )}

      {role === 'driver' && (
        <div style={roleBoxStyle}>
          <div style={roleTitleStyle}>🛵 Vehicle & Area Details</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
            <div>
              <label style={labelStyle}>Vehicle Type *</label>
              <select
                value={driverVehicleType}
                onChange={(e) => setDriverVehicleType(e.target.value)}
                style={inputStyle}
              >
                <option value="scooter">Two Wheeler / Scooter</option>
                <option value="e_rickshaw">E-Rickshaw</option>
                <option value="van">Delivery Van / Auto</option>
                <option value="bicycle">Bicycle</option>
              </select>
            </div>
            <div>
              <label style={labelStyle}>Vehicle Registration Number *</label>
              <input
                type="text"
                placeholder="e.g. RJ-14-ER-4521"
                required
                value={driverVehicleNumber}
                onChange={(e) => setDriverVehicleNumber(e.target.value)}
                style={inputStyle}
              />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
            <div>
              <label style={labelStyle}>Carrying Capacity (Meals)</label>
              <input
                type="number"
                min="10"
                max="500"
                value={driverCapacity}
                onChange={(e) => setDriverCapacity(e.target.value)}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Operating Area / Sector *</label>
              <input
                type="text"
                placeholder="e.g. Malviya Nagar & C-Scheme"
                required
                value={driverArea}
                onChange={(e) => setDriverArea(e.target.value)}
                style={inputStyle}
              />
            </div>
          </div>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', marginTop: '6px' }}>
            <input
              type="checkbox"
              checked={driverColdBox}
              onChange={(e) => setDriverColdBox(e.target.checked)}
              style={{ width: '16px', height: '16px', accentColor: 'var(--green-dark)' }}
            />
            <span style={{ fontSize: '0.84rem', color: 'var(--deep)', fontWeight: 600 }}>
              Equipped with Insulated Cold Box (Enables cold perishables)
            </span>
          </label>
        </div>
      )}

      {role === 'admin' && (
        <div style={roleBoxStyle}>
          <div style={roleTitleStyle}>⚡ Ops Unit Details</div>
          <div>
            <label style={labelStyle}>Dispatch Control Unit</label>
            <input
              type="text"
              value={opsDepartment}
              onChange={(e) => setOpsDepartment(e.target.value)}
              style={inputStyle}
            />
          </div>
        </div>
      )}

      {/* Buttons */}
      <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
        <Button variant="outline" type="button" onClick={onCancel} style={{ flex: 1 }}>
          Already have an account? Sign In
        </Button>
        <Button variant="primary" type="submit" disabled={loading} style={{ flex: 1.3 }}>
          {loading ? 'Creating Your Account...' : 'Verify Email & Create Account'}
        </Button>
      </div>
    </form>
  );
};

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: '0.82rem',
  fontWeight: 700,
  color: 'var(--deep)',
  marginBottom: '4px',
};

const subHintStyle: React.CSSProperties = {
  display: 'block',
  fontSize: '0.74rem',
  color: 'var(--muted)',
  marginTop: '4px',
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '10px 12px',
  borderRadius: 'var(--r-card-sm)',
  border: '1px solid var(--line)',
  background: 'var(--paper)',
  fontSize: '0.9rem',
  color: 'var(--ink)',
  outline: 'none',
  fontFamily: 'inherit',
  boxSizing: 'border-box',
};

const roleBoxStyle: React.CSSProperties = {
  background: '#f8faf7',
  border: '1px solid #d4ebd4',
  borderRadius: 'var(--r-card-sm)',
  padding: '14px',
  marginTop: '4px',
};

const roleTitleStyle: React.CSSProperties = {
  fontSize: '0.86rem',
  fontWeight: 700,
  color: 'var(--deep)',
  marginBottom: '10px',
};

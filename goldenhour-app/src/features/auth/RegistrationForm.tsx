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
  const { addToast } = useUiStore();

  // Common Fields
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [city, setCity] = useState('Jaipur');

  // Role specific fields
  // Donor
  const [donorAddress, setDonorAddress] = useState('');
  const [donorFoodCategory, setDonorFoodCategory] = useState('restaurant');

  // Recipient
  const [recipientCapacity, setRecipientCapacity] = useState('150');
  const [recipientRestrictions, setRecipientRestrictions] = useState('');

  // Driver
  const [driverVehicle, setDriverVehicle] = useState('scooter');
  const [driverArea, setDriverArea] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      let profile: Record<string, any> = {};
      if (role === 'donor') {
        profile = {
          pickup_address: donorAddress,
          food_category: donorFoodCategory,
        };
      } else if (role === 'recipient') {
        profile = {
          max_capacity_portions: parseInt(recipientCapacity, 10) || 150,
          food_restrictions: recipientRestrictions,
        };
      } else if (role === 'driver') {
        profile = {
          vehicle_number: driverVehicle,
          operating_area: driverArea,
        };
      }

      const payload = {
        role,
        name,
        phone,
        email: email || undefined,
        password,
        city,
        profile,
      };

      const tokens = await api.post<{
        access_token: string;
        refresh_token: string;
        token_type: string;
        expires_in: number;
        user_id: string;
        role: Role;
      }>('/auth/register', payload);

      useSessionStore.getState().setTokens(tokens.access_token, tokens.refresh_token);

      const user = await api.get<User>('/auth/me');

      useSessionStore.getState().setSession(user, {
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
      });

      addToast(`Registration successful! Welcome, ${user.name}`, 'success');
      onSuccess(role);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Registration failed';
      addToast(errorMsg, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <h3 style={{ margin: '0 0 10px', color: 'var(--deep)' }}>Register as {role.toUpperCase()}</h3>
      
      <input type="text" placeholder="Full Name *" required value={name} onChange={e => setName(e.target.value)} style={inputStyle} />
      <input type="tel" placeholder="Phone Number *" required value={phone} onChange={e => setPhone(e.target.value)} style={inputStyle} />
      <input type="email" placeholder="Email (Optional)" value={email} onChange={e => setEmail(e.target.value)} style={inputStyle} />
      <input type="password" placeholder="Password *" required value={password} onChange={e => setPassword(e.target.value)} style={inputStyle} />
      <input type="text" placeholder="City" value={city} onChange={e => setCity(e.target.value)} style={inputStyle} />

      {role === 'donor' && (
        <>
          <input type="text" placeholder="Pickup Address" required value={donorAddress} onChange={e => setDonorAddress(e.target.value)} style={inputStyle} />
          <input type="text" placeholder="Food Category (e.g. restaurant, caterer)" value={donorFoodCategory} onChange={e => setDonorFoodCategory(e.target.value)} style={inputStyle} />
        </>
      )}

      {role === 'recipient' && (
        <>
          <input type="number" placeholder="Max Capacity (Portions)" required value={recipientCapacity} onChange={e => setRecipientCapacity(e.target.value)} style={inputStyle} />
          <input type="text" placeholder="Food Restrictions (e.g. None)" value={recipientRestrictions} onChange={e => setRecipientRestrictions(e.target.value)} style={inputStyle} />
        </>
      )}

      {role === 'driver' && (
        <>
          <select value={driverVehicle} onChange={e => setDriverVehicle(e.target.value)} style={inputStyle}>
            <option value="bicycle">Bicycle</option>
            <option value="scooter">Scooter</option>
            <option value="e_rickshaw">E-Rickshaw</option>
            <option value="van">Van</option>
          </select>
          <input type="text" placeholder="Operating Area" value={driverArea} onChange={e => setDriverArea(e.target.value)} style={inputStyle} />
        </>
      )}

      <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
        <Button variant="outline" type="button" onClick={onCancel} style={{ flex: 1 }}>Back to Login</Button>
        <Button variant="primary" type="submit" disabled={loading} style={{ flex: 1 }}>{loading ? 'Registering...' : 'Register'}</Button>
      </div>
    </form>
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

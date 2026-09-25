import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useSessionStore } from '../../store/session';

export const DriverLayout: React.FC = () => {
  const location = useLocation();
  const { user } = useSessionStore();

  const navItems = [
    { path: '/driver', label: 'Shift Home', icon: '🛵' },
    { path: '/driver/active', label: 'Active Route', icon: '📍' },
    { path: '/driver/offers', label: 'Offers', icon: '⚡' },
    { path: '/profile', label: 'Profile', icon: '👤' },
  ];

  return (
    <div
      style={{
        minHeight: 'calc(100vh - var(--header-h))',
        background: '#f2f5f1',
        display: 'flex',
        flexDirection: 'column',
        paddingBottom: '80px', // thumb zone clearance
      }}
    >
      {/* Top Driver Pill */}
      <div
        style={{
          background: 'var(--deep)',
          color: 'var(--white)',
          padding: '12px 18px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '18px' }}>🛵</span>
          <div>
            <strong style={{ fontSize: '0.95rem' }}>{user?.name || 'Rescue Driver'}</strong>
            <div style={{ fontSize: '0.72rem', color: 'var(--green)' }}>
              {user?.profile?.vehicle_type || 'Vehicle'} • {user?.profile?.vehicle_number || user?.profile?.operating_area || user?.city || 'Jaipur Active'}
            </div>
          </div>
        </div>

        <span
          style={{
            background: 'rgba(143, 211, 90, 0.2)',
            color: 'var(--green)',
            padding: '4px 10px',
            borderRadius: 'var(--r-pill)',
            fontSize: '0.75rem',
            fontWeight: 800,
          }}
        >
          ● ONLINE
        </span>
      </div>

      {/* Main Screen Outlet */}
      <div style={{ flex: 1, padding: '20px 16px', maxWidth: '640px', margin: '0 auto', width: '100%' }}>
        <Outlet />
      </div>

      {/* Bottom Thumb-Zone Navigation Bar */}
      <nav
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          height: '68px',
          background: 'var(--white)',
          borderTop: '1px solid var(--line)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-around',
          zIndex: 80,
          boxShadow: '0 -4px 16px rgba(23, 61, 42, 0.08)',
        }}
      >
        {navItems.map((item) => {
          const active = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '3px',
                color: active ? 'var(--deep)' : 'var(--muted)',
                fontWeight: active ? 800 : 500,
                fontSize: '0.78rem',
                minWidth: '70px',
                minHeight: '48px',
                justifyContent: 'center',
              }}
            >
              <span style={{ fontSize: '20px' }}>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
};

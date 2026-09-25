import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useSessionStore } from '../../store/session';

export const OrgLayout: React.FC = () => {
  const location = useLocation();
  const { user } = useSessionStore();

  const navItems = [
    { path: '/org', label: 'Intake Dashboard', icon: '🏠' },
    { path: '/org/capacity', label: 'Capacity Manager', icon: '⚙️' },
    { path: '/org/history', label: 'Receipts & History', icon: '📋' },
    { path: '/profile', label: 'Profile', icon: '👤' },
  ];

  return (
    <div style={{ minHeight: 'calc(100vh - var(--header-h))', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      {/* Shelter Header */}
      <div
        style={{
          background: 'var(--white)',
          borderBottom: '1px solid var(--line)',
          padding: '12px 0',
        }}
      >
        <div className="wrap" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '20px' }}>🏠</span>
            <div>
              <strong style={{ fontSize: '1rem', color: 'var(--deep)' }}>
                {user?.profile?.name || user?.name || 'Asha Shelter Foundation'}
              </strong>
              <div style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>
                {user?.profile?.address || user?.city || user?.email || 'Capacity Hub'}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            {navItems.map((item) => {
              const active = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  style={{
                    padding: '6px 14px',
                    borderRadius: 'var(--r-pill)',
                    fontSize: '0.84rem',
                    fontWeight: active ? 700 : 500,
                    background: active ? 'var(--deep)' : 'transparent',
                    color: active ? 'var(--white)' : 'var(--muted)',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <span style={{ marginRight: '6px' }}>{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="wrap" style={{ flex: 1, padding: '30px 0 60px' }}>
        <Outlet />
      </div>
    </div>
  );
};

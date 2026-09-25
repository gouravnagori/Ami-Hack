import React from 'react';
import { createBrowserRouter } from 'react-router-dom';

// Layouts & Shared
import { Header } from './components/layout/Header';
import { ToastContainer } from './components/ui/Toast';

// Pages
import { LandingPage } from './features/landing/LandingPage';
import { AuthPage } from './features/auth/AuthPage';
import { ProfilePage } from './features/auth/ProfilePage';

// Donor
import { DonorLayout } from './features/donor/DonorLayout';
import { DonorHome } from './features/donor/pages/DonorHome';
import { QuickPost } from './features/donor/pages/QuickPost';
import { DonationDetail } from './features/donor/pages/DonationDetail';
import { DonorImpact } from './features/donor/pages/DonorImpact';

// Recipient / Org
import { OrgLayout } from './features/org/OrgLayout';
import { OrgHome } from './features/org/pages/OrgHome';
import { CapacityManager } from './features/org/pages/CapacityManager';
import { OrgHistory } from './features/org/pages/OrgHistory';

// Driver
import { DriverLayout } from './features/driver/DriverLayout';
import { DriverHome } from './features/driver/pages/DriverHome';
import { OfferSheet } from './features/driver/pages/OfferSheet';
import { ActiveRoute } from './features/driver/pages/ActiveRoute';
import { DoneScreen } from './features/driver/pages/DoneScreen';

// Ops
import { OpsConsole } from './features/ops/OpsConsole';

// Auth Guard
import { AuthGuard } from './components/auth/AuthGuard';

// Root shell component that wraps all routes with global Header and Toasts
const RootShell: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
    <Header />
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
      {children}
    </div>
    <ToastContainer />
  </div>
);

export const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <RootShell>
        <LandingPage />
      </RootShell>
    ),
  },
  {
    path: '/auth',
    element: (
      <RootShell>
        <AuthPage />
      </RootShell>
    ),
  },
  {
    path: '/profile',
    element: (
      <RootShell>
        <AuthGuard>
          <ProfilePage />
        </AuthGuard>
      </RootShell>
    ),
  },
  {
    path: '/donor',
    element: (
      <RootShell>
        <AuthGuard requiredRole="donor">
          <DonorLayout />
        </AuthGuard>
      </RootShell>
    ),
    children: [
      { index: true, element: <DonorHome /> },
      { path: 'new', element: <QuickPost /> },
      { path: ':id', element: <DonationDetail /> },
      { path: 'impact', element: <DonorImpact /> },
    ],
  },
  {
    path: '/org',
    element: (
      <RootShell>
        <AuthGuard requiredRole="recipient">
          <OrgLayout />
        </AuthGuard>
      </RootShell>
    ),
    children: [
      { index: true, element: <OrgHome /> },
      { path: 'capacity', element: <CapacityManager /> },
      { path: 'history', element: <OrgHistory /> },
    ],
  },
  {
    path: '/driver',
    element: (
      <RootShell>
        <AuthGuard requiredRole="driver">
          <DriverLayout />
        </AuthGuard>
      </RootShell>
    ),
    children: [
      { index: true, element: <DriverHome /> },
      { path: 'offers', element: <OfferSheet /> },
      { path: 'active', element: <ActiveRoute /> },
      { path: 'done', element: <DoneScreen /> },
    ],
  },
  {
    path: '/ops',
    element: (
      <RootShell>
        <AuthGuard requiredRole="admin">
          <OpsConsole />
        </AuthGuard>
      </RootShell>
    ),
  },
]);

import React from 'react';

interface PhoneFrameProps {
  children: React.ReactNode;
  width?: string;
  maxHeight?: string;
  className?: string;
}

export const PhoneFrame: React.FC<PhoneFrameProps> = ({
  children,
  width = '380px',
  maxHeight = '720px',
  className = '',
}) => {
  return (
    <div
      className={`phone-frame ${className}`}
      style={{
        width,
        maxWidth: '100%',
        maxHeight,
        background: 'var(--paper)',
        borderRadius: '40px',
        border: '10px solid #242c26',
        boxShadow: '0 25px 60px -10px rgba(23, 61, 42, 0.28), 0 0 0 1px rgba(255,255,255,0.1)',
        position: 'relative',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Dynamic Notch / Island */}
      <div
        style={{
          position: 'absolute',
          top: '10px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '90px',
          height: '18px',
          background: '#242c26',
          borderRadius: '20px',
          zIndex: 30,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* Camera dot */}
        <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#111', marginLeft: 'auto', marginRight: '10px' }} />
      </div>

      {/* Screen Content */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          paddingTop: '28px',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {children}
      </div>

      {/* Home indicator bar at bottom */}
      <div
        style={{
          height: '18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'transparent',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            width: '120px',
            height: '4px',
            background: 'var(--muted)',
            opacity: 0.4,
            borderRadius: '99px',
          }}
        />
      </div>
    </div>
  );
};

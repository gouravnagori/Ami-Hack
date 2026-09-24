import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './PathBox.module.css';

interface PathBoxProps {
  onClose?: () => void;
}

const paths = [
  { label: 'I have surplus food', icon: '🍱', role: 'donor' },
  { label: 'We feed people', icon: '🏠', role: 'recipient' },
  { label: 'I can drive', icon: '🚗', role: 'driver' },
];

export const PathBox: React.FC<PathBoxProps> = ({ onClose }) => {
  const navigate = useNavigate();
  const [visible, setVisible] = useState(true);

  const handleClick = (role: string) => {
    navigate(`/auth?role=${role}`);
  };

  const handleClose = () => {
    setVisible(false);
    onClose?.();
  };

  if (!visible) return null;

  return (
    <div className={styles.box}>
      <div className={styles.heading}>
        <strong>What brings you here?</strong>
        <button className={styles.close} onClick={handleClose} aria-label="Close">×</button>
      </div>
      <div className={styles.paths}>
        {paths.map((p) => (
          <button key={p.role} className={styles.path} onClick={() => handleClick(p.role)}>
            <div>
              <span className={styles.pathIcon}>{p.icon}</span>
              <strong>{p.label}</strong>
            </div>
            <span className="arrow" style={{ color: 'var(--muted)' }}>→</span>
          </button>
        ))}
      </div>
    </div>
  );
};

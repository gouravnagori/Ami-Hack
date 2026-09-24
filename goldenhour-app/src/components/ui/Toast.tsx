import React from 'react';
import { useUiStore } from '../../store/ui';
import styles from './Toast.module.css';

const ICONS: Record<string, string> = {
  success: '✓',
  error: '✕',
  warning: '⚠',
  info: 'ℹ',
};

export const Toast: React.FC<{
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  onClose: () => void;
}> = ({ message, type, onClose }) => (
  <div className={`${styles.toast} ${styles[type]}`} role="alert">
    <span className={styles.icon}>{ICONS[type]}</span>
    <span className={styles.message}>{message}</span>
    <button className={styles.close} onClick={onClose} aria-label="Dismiss">×</button>
  </div>
);

export const ToastContainer: React.FC = () => {
  const toasts = useUiStore((s) => s.toasts);
  const removeToast = useUiStore((s) => s.removeToast);

  if (toasts.length === 0) return null;

  return (
    <div className={styles.container} aria-live="polite">
      {toasts.map((t) => (
        <Toast key={t.id} message={t.message} type={t.type} onClose={() => removeToast(t.id)} />
      ))}
    </div>
  );
};

import React from 'react';
import styles from './Toggle.module.css';

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
}

export const Toggle: React.FC<ToggleProps> = ({ checked, onChange, label, disabled }) => {
  return (
    <label className={styles.wrapper}>
      <button
        role="switch"
        aria-checked={checked}
        aria-label={label}
        className={`${styles.toggle} ${checked ? '' : styles.off}`}
        onClick={() => !disabled && onChange(!checked)}
        disabled={disabled}
        type="button"
      />
      {label && <span className={styles.label}>{label}</span>}
    </label>
  );
};

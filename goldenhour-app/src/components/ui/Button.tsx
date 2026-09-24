import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'outline' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  block?: boolean;
  arrow?: boolean;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  block = false,
  arrow = false,
  children,
  className = '',
  ...props
}) => {
  const variantClass =
    variant === 'primary' ? 'btn-primary' :
    variant === 'outline' ? 'btn-outline' :
    'btn-danger';

  const sizeClass =
    size === 'sm' ? 'btn-sm' :
    size === 'lg' ? 'btn-lg' : '';

  return (
    <button
      className={`btn ${variantClass} ${sizeClass} ${block ? 'btn-block' : ''} ${className}`}
      {...props}
    >
      {children}
      {arrow && <span className="arrow">→</span>}
    </button>
  );
};

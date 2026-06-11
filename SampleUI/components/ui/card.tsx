import React from 'react';

export function Card({
  children,
  className = '',
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`rounded-lg ${className}`} {...props}>
      {children}
    </div>
  );
}

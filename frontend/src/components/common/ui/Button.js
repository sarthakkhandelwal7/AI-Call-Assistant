import React from 'react';
import { cva } from 'class-variance-authority';

export const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'md',
  isLoading = false,
  className = '',
  ...props 
}) => {
  const buttonStyles = cva(
    'inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none',
    {
      variants: {
        variant: {
          primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
          secondary: 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-gray-500',
          danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
          ghost: 'bg-transparent hover:bg-gray-100 text-gray-700',
        },
        size: {
          sm: 'px-3 py-1.5 text-sm',
          md: 'px-4 py-2 text-sm',
          lg: 'px-6 py-3 text-base'
        }
      }
    }
  );

  return (
    <button 
      className={`${buttonStyles({ variant, size })} ${className}`}
      disabled={isLoading}
      {...props}
    >
      {isLoading ? (
        <svg className="animate-spin h-4 w-4 mr-2" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      ) : null}
      {children}
    </button>
  );
};
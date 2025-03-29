import React from 'react';

export const Input = React.forwardRef(({ label, error, ...props }, ref) => (
  <div>
    {label && (
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
    )}
    <input
      ref={ref}
      className={`block w-full rounded-md shadow-sm text-sm
        ${error 
          ? 'border-red-300 focus:ring-red-500 focus:border-red-500' 
          : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
        }`}
      {...props}
    />
    {error && (
      <p className="mt-1 text-sm text-red-600">{error}</p>
    )}
  </div>
));
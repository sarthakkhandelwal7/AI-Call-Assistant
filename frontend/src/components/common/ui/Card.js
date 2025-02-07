import React from 'react';

export const Card = ({ 
  title, 
  children, 
  headerActions,
  variant = 'default',
  className = '' 
}) => {
  const cardStyles = {
    default: 'bg-white',
    elevated: 'bg-white shadow-lg',
    bordered: 'bg-white border border-gray-200',
  };

  return (
    <div className={`${cardStyles[variant]} rounded-lg overflow-hidden ${className}`}>
      {title && (
        <div className="border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <h3 className="text-lg font-medium text-gray-900">{title}</h3>
          {headerActions}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
};

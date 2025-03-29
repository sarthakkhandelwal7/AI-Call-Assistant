import React from 'react';

export const TabGroup = ({ tabs, activeTab, onChange, variant = 'default' }) => {
  const styles = {
    default: {
      nav: 'border-b border-gray-200',
      tab: (isActive) => `
        ${isActive 
          ? 'border-blue-500 text-blue-600' 
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
        } flex items-center px-4 py-2 border-b-2 font-medium text-sm
      `
    },
    pills: {
      nav: 'flex space-x-2',
      tab: (isActive) => `
        ${isActive
          ? 'bg-blue-100 text-blue-700'
          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
        } px-3 py-1.5 rounded-full font-medium text-sm
      `
    }
  };

  return (
    <nav className={styles[variant].nav}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={styles[variant].tab(activeTab === tab.id)}
        >
          {tab.icon && <span className="mr-2">{tab.icon}</span>}
          {tab.label}
        </button>
      ))}
    </nav>
  );
};
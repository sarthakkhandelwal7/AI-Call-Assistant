import React from 'react';
import Navbar from './Navbar';

const Layout = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="pt-16 px-4 max-w-7xl mx-auto">
        {children}
      </main>
      <footer className="mt-auto py-6 bg-white border-t">
        <div className="max-w-7xl mx-auto px-4">
          <p className="text-center text-sm text-gray-500">
            © {new Date().getFullYear()} AI Secretary. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
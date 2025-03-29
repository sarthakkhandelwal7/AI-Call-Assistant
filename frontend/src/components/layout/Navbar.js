import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Menu, X, Phone, Settings, LogOut } from 'lucide-react';
import { useGoogleLogin } from '@react-oauth/google';

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { user, login, logout } = useAuth();
  const location = useLocation();

  const googleLogin = useGoogleLogin({
    onSuccess: login,
    flow: 'auth-code',
    scope: 
      'https://www.googleapis.com/auth/userinfo.profile ' + 
      'https://www.googleapis.com/auth/userinfo.email ' +
      'https://www.googleapis.com/auth/calendar.events ' +
      'https://www.googleapis.com/auth/calendar.readonly',
    access_type: 'offline',
    prompt: 'consent'
  });

  const navigation = [
    { name: 'Home', href: '/' },
    { name: 'Features', href: '/#features' },
    ...(user ? [{ name: 'Dashboard', href: '/profile' }] : []),
  ];

  return (
    <nav className="bg-white shadow-lg fixed w-full z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <Link to="/" className="flex items-center">
              <Phone className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">AI Secretary</span>
            </Link>
          </div>

          {/* Desktop menu */}
          <div className="hidden md:flex md:items-center md:space-x-4">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname === item.href
                    ? 'text-blue-600 bg-blue-50'
                    : 'text-gray-700 hover:text-blue-600 hover:bg-blue-50'
                }`}
              >
                {item.name}
              </Link>
            ))}
            {user ? (
              <div className="flex items-center ml-4">
                <div className="border-l border-gray-200 pl-4 flex items-center space-x-4">
                  {user.profile_picture && (
                    <img
                      src={user.profile_picture}
                      alt={user.full_name}
                      className="h-8 w-8 rounded-full"
                    />
                  )}
                  <span className="text-sm font-medium text-gray-700">{user.full_name}</span>
                  <button
                    onClick={logout}
                    className="inline-flex items-center px-3 py-2 border border-red-300 rounded-md shadow-sm text-sm font-medium text-red-700 bg-white hover:bg-red-50"
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Logout
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => googleLogin()}
                className="ml-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                Sign in with Google
              </button>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="flex items-center md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
            >
              {isOpen ? (
                <X className="block h-6 w-6" />
              ) : (
                <Menu className="block h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`block px-3 py-2 rounded-md text-base font-medium ${
                  location.pathname === item.href
                    ? 'text-blue-600 bg-blue-50'
                    : 'text-gray-700 hover:text-blue-600 hover:bg-blue-50'
                }`}
                onClick={() => setIsOpen(false)}
              >
                {item.name}
              </Link>
            ))}
            {user ? (
              <div className="pt-4 pb-3 border-t border-gray-200">
                <div className="flex items-center px-3">
                  {user.profile_picture && (
                    <img
                      src={user.profile_picture}
                      alt={user.full_name}
                      className="h-10 w-10 rounded-full"
                    />
                  )}
                  <div className="ml-3">
                    <div className="text-base font-medium text-gray-800">{user.full_name}</div>
                    <div className="text-sm font-medium text-gray-500">{user.email}</div>
                  </div>
                </div>
                <div className="mt-3 px-2">
                  <button
                    onClick={() => {
                      logout();
                      setIsOpen(false);
                    }}
                    className="w-full flex items-center px-3 py-2 rounded-md text-base font-medium text-red-700 hover:text-red-900 hover:bg-red-50"
                  >
                    <LogOut className="h-5 w-5 mr-2" />
                    Logout
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => {
                  googleLogin();
                  setIsOpen(false);
                }}
                className="mt-4 w-full flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                Sign in with Google
              </button>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
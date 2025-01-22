import React from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import { useAuth } from './contexts/AuthContext';

function App() {
  const { user, login, logout } = useAuth();

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

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-lg">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex justify-between items-center py-4">
            {user ? (
              <div className="flex items-center space-x-4">
                {user.profile_picture && (
                  <img 
                    src={user.profile_picture} 
                    alt={user.full_name}
                    className="w-8 h-8 rounded-full"
                  />
                )}
                <span>{user.full_name}</span>
                <button
                  onClick={logout}
                  className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                >
                  Logout
                </button>
              </div>
            ) : (
              <button
                onClick={() => googleLogin()}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
              >
                Sign in with Google
              </button>
            )}
          </div>
        </div>
      </nav>

      {user && (
        <main className="max-w-6xl mx-auto mt-8 px-4">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold mb-4">Welcome, {user.full_name}!</h2>
            <div className="space-y-2">
              <div><strong>Email:</strong> {user.email}</div>
              <div>
                <strong>Calendar Connected:</strong>{' '}
                {user.calendar_connected ? (
                  <span className="text-green-500">Yes</span>
                ) : (
                  <span className="text-red-500">No</span>
                )}
              </div>
            </div>
          </div>
        </main>
      )}
    </div>
  );
}

export default App;
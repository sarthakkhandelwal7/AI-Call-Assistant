import React from 'react';
import { Calendar } from 'lucide-react';
import { Button } from '../common/ui/Button';
import { useAuth } from '../../contexts/AuthContext';

export const ProfileHeader = () => {
  const { user, logout } = useAuth();

  return (
    <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
      <div className="flex items-center space-x-4">
        {user?.profile_picture ? (
          <img
            src={user.profile_picture}
            alt={user.full_name}
            className="h-12 w-12 rounded-full border-2 border-blue-500"
          />
        ) : (
          <div className="h-12 w-12 rounded-full bg-blue-500 flex items-center justify-center text-white text-xl font-bold">
            {user?.full_name?.[0]}
          </div>
        )}
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{user?.full_name}</h2>
          <div className="flex items-center mt-1">
            <Calendar className="h-4 w-4 text-gray-400 mr-1" />
            <span className="text-sm text-gray-500">
              {user?.calendar_connected ? 'Calendar Connected' : 'Calendar Not Connected'}
            </span>
          </div>
        </div>
      </div>
      <Button variant="danger" onClick={logout}>
        Logout
      </Button>
    </div>
  );
};
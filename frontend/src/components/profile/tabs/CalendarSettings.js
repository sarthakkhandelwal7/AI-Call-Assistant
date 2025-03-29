import React from 'react';
import { Calendar, Check, X as XIcon } from 'lucide-react';
import { Card } from '../../common/ui/Card';
import { Button } from '../../common/ui/Button';
import { useAuth } from '../../../contexts/AuthContext';

export const CalendarSettings = () => {
  const { user } = useAuth();

  const StatusBadge = () => (
    <span className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${
      user?.calendar_connected 
        ? 'bg-green-100 text-green-800' 
        : 'bg-red-100 text-red-800'
    }`}>
      {user?.calendar_connected ? (
        <>
          <Check className="w-4 h-4 mr-1" />
          Connected
        </>
      ) : (
        <>
          <XIcon className="w-4 h-4 mr-1" />
          Not Connected
        </>
      )}
    </span>
  );

  return (
    <Card
      title="Calendar Connection"
      headerActions={<StatusBadge />}
    >
      <p className="text-sm text-gray-500 mb-4">
        Connect your Google Calendar to enable smart scheduling features.
      </p>
      {!user?.calendar_connected && (
        <Button>
          <Calendar className="w-4 h-4 mr-2" />
          Connect Calendar
        </Button>
      )}
    </Card>
  );
};
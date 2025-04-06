// src/components/profile/tabs/ProfileInfo.js
import React from 'react';
import { User, Mail, Clock, Globe, Phone } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import { Card } from '../../common/ui';

export const ProfileInfo = () => {
  const { user, updateUserProfile } = useAuth();
  
  const handleTimezoneChange = async (e) => {
    try {
      await updateUserProfile({ timezone: e.target.value });
    } catch (err) {
      console.error('Failed to update timezone:', err);
    }
  };

  const handlePhoneChange = async (e) => {
    try {
      await updateUserProfile({ user_number: e.target.value });
    } catch (err) {
      console.error('Failed to update phone number:', err);
    }
  };
  
  const timezones = [
    'UTC', 'America/New_York', 'America/Los_Angeles', 'Europe/London', 
    'Asia/Tokyo', 'Australia/Sydney', 'Pacific/Auckland'
  ];

  return (
    <div className="space-y-6">
      <Card>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          <div>
            <label className="flex items-center text-sm font-medium text-gray-700">
              <User className="w-4 h-4 mr-2" />
              Full Name
            </label>
            <input
              type="text"
              value={user?.full_name || ''}
              readOnly
              className="input-field"
            />
          </div>
          <div>
            <label className="flex items-center text-sm font-medium text-gray-700">
              <Mail className="w-4 h-4 mr-2" />
              Email
            </label>
            <input
              type="email"
              value={user?.email || ''}
              readOnly
              className="input-field"
            />
          </div>
          
          <div>
            <label className="flex items-center text-sm font-medium text-gray-700">
              <Globe className="w-4 h-4 mr-2" />
              Timezone
            </label>
            <select 
              value={user?.timezone || 'UTC'}
              onChange={handleTimezoneChange}
              className="input-field"
            >
              {timezones.map(tz => (
                <option key={tz} value={tz}>{tz}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="flex items-center text-sm font-medium text-gray-700">
              <Phone className="w-4 h-4 mr-2" />
              Your Phone Number
            </label>
            <input
              type="tel"
              value={user?.user_number || ''}
              placeholder="+1234567890"
              onChange={handlePhoneChange}
              className="input-field"
            />
          </div>

          <div>
            <label className="flex items-center text-sm font-medium text-gray-700">
              <Phone className="w-4 h-4 mr-2" />
              Twilio Number
            </label>
            <input
              type="tel"
              value={user?.twilio_number || ''}
              readOnly
              className="input-field bg-gray-50"
              placeholder="Not assigned yet"
            />
          </div>
        </div>
      </Card>
    </div>
  );
};
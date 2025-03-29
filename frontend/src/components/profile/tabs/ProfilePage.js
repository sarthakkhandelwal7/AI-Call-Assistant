import React, { useState } from 'react';
import { Shield, Calendar, Phone, Bell } from 'lucide-react';
import { Card } from '../../common/ui';
import { TabGroup } from '../../common/ui';
import { ProfileHeader } from '../ProfileHeader';
import { ProfileInfo } from './ProfileInfo';
import { CalendarSettings } from './CalendarSettings';
import { CallSettings } from './CallSettings';
import { NotificationSettings } from './NotificationSettings';

const TABS = [
  { id: 'profile', label: 'Profile', icon: <Shield className="w-5 h-5" /> },
  { id: 'calendar', label: 'Calendar', icon: <Calendar className="w-5 h-5" /> },
  { id: 'calls', label: 'Call Settings', icon: <Phone className="w-5 h-5" /> },
  { id: 'notifications', label: 'Notifications', icon: <Bell className="w-5 h-5" /> }
];

const TAB_COMPONENTS = {
  profile: ProfileInfo,
  calendar: CalendarSettings,
  calls: CallSettings,
  notifications: NotificationSettings
};

const ProfilePage = () => {
  const [activeTab, setActiveTab] = useState('profile');
  const TabComponent = TAB_COMPONENTS[activeTab];

  return (
    <div className="space-y-6 py-8">
      <Card className="overflow-hidden">
        <ProfileHeader />
        <div className="border-t border-gray-200">
          <TabGroup 
            tabs={TABS}
            activeTab={activeTab}
            onChange={setActiveTab}
          />
        </div>
        <div className="p-6">
          <TabComponent />
        </div>
      </Card>
    </div>
  );
};

export default ProfilePage;
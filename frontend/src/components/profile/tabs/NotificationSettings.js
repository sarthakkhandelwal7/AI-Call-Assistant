import React from 'react';
import { Card } from '../../common/ui/Card';

export const NotificationSettings = () => {
  return (
    <Card title="Notification Preferences">
      <div className="space-y-4">
        <div className="flex items-start">
          <div className="flex items-center h-5">
            <input
              id="sms_notifications"
              type="checkbox"
              className="h-4 w-4 text-blue-600 border-gray-300 rounded"
            />
          </div>
          <div className="ml-3">
            <label htmlFor="sms_notifications" className="font-medium text-gray-700">SMS Notifications</label>
            <p className="text-sm text-gray-500">Get SMS alerts for important calls and messages</p>
          </div>
        </div>
        <div className="flex items-start">
          <div className="flex items-center h-5">
            <input
              id="email_notifications"
              type="checkbox"
              className="h-4 w-4 text-blue-600 border-gray-300 rounded"
            />
          </div>
          <div className="ml-3">
            <label htmlFor="email_notifications" className="font-medium text-gray-700">Email Notifications</label>
            <p className="text-sm text-gray-500">Receive email summaries of calls and meetings</p>
          </div>
        </div>
      </div>
    </Card>
  );
};
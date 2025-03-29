import React from 'react';
import { Card } from '../../common/ui/Card';

export const CallSettings = () => {
  return (
    <Card title="Call Settings">
      <div className="space-y-4">
        <div className="flex items-start">
          <div className="flex items-center h-5">
            <input
              id="screen_all"
              type="checkbox"
              className="h-4 w-4 text-blue-600 border-gray-300 rounded"
            />
          </div>
          <div className="ml-3">
            <label htmlFor="screen_all" className="font-medium text-gray-700">Screen all calls</label>
            <p className="text-sm text-gray-500">Let Alex screen all incoming calls before forwarding</p>
          </div>
        </div>
        <div className="flex items-start">
          <div className="flex items-center h-5">
            <input
              id="auto_schedule"
              type="checkbox"
              className="h-4 w-4 text-blue-600 border-gray-300 rounded"
            />
          </div>
          <div className="ml-3">
            <label htmlFor="auto_schedule" className="font-medium text-gray-700">Auto-schedule when busy</label>
            <p className="text-sm text-gray-500">Automatically offer scheduling when you're in a meeting</p>
          </div>
        </div>
      </div>
    </Card>
  );
};
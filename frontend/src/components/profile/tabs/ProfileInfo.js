// src/components/profile/tabs/ProfileInfo.js
import React, { useState, useEffect } from 'react';
import { Globe, Phone, PlusCircle, AlertTriangle, Check } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import { Card, Button, Input } from '../../common/ui';
import { TwilioNumberPurchase } from './TwilioNumberPurchase';
import { phoneNumberAPI, verificationAPI } from '../../../services/api';

export const ProfileInfo = () => {
  const { user, updateUserProfile } = useAuth();
  
  // --- State for Edit Mode ---
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({ 
      full_name: '', 
      calendar_url: '' 
  });
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);
  const [profileUpdateError, setProfileUpdateError] = useState(null);
  const [profileUpdateSuccess, setProfileUpdateSuccess] = useState(false);
  // -------------------------

  // Assistant Number State
  const [showAssistantNumberPurchase, setShowAssistantNumberPurchase] = useState(false);
  const [twilioNumber, setTwilioNumber] = useState('');
  const [twilioNumberError, setTwilioNumberError] = useState(null);
  
  // User Phone Verification State
  const [userPhoneNumberInput, setUserPhoneNumberInput] = useState(user?.user_number || '');
  const [otpCode, setOtpCode] = useState('');
  const [verificationStatus, setVerificationStatus] = useState('idle'); 
  const [isSendingOtp, setIsSendingOtp] = useState(false);
  const [isCheckingOtp, setIsCheckingOtp] = useState(false);
  const [verificationError, setVerificationError] = useState(null);
  
  // Initialize form data and inputs when user data loads or changes
  useEffect(() => {
    if (user) {
      setFormData({ 
          full_name: user.full_name || '', 
          calendar_url: user.calendar_url || '' 
      });
      setUserPhoneNumberInput(user.user_number || '');
      if(user.user_number) {
        setVerificationStatus('idle'); 
      }
      checkTwilioNumber(); 
    }
  }, [user]);

  // Check Assistant Number
  const checkTwilioNumber = async () => {
    try {
      setTwilioNumberError(null);
      const data = await phoneNumberAPI.getRegisteredTwilioNumber();
      setTwilioNumber(data.number || '');
    } catch (err) {
      console.error('Error checking Twilio number:', err);
      setTwilioNumberError(err.message);
    }
  };
  
  // Handle Timezone Change (remains direct update for simplicity)
  const handleTimezoneChange = async (e) => {
    try {
      await updateUserProfile({ timezone: e.target.value });
    } catch (err) {
      console.error('Failed to update timezone:', err);
    }
  };

  // --- Edit Mode Handlers ---
  const handleEditClick = () => {
    setFormData({ // Initialize form with current user data
        full_name: user?.full_name || '', 
        calendar_url: user?.calendar_url || '' 
    });
    setEditMode(true);
    setProfileUpdateSuccess(false); // Clear success message
    setProfileUpdateError(null); // Clear previous errors
  };

  const handleCancelClick = () => {
    setEditMode(false);
    // Reset form data from state (in case useEffect hasn't run)
    setFormData({ 
        full_name: user?.full_name || '', 
        calendar_url: user?.calendar_url || '' 
    });
    setProfileUpdateError(null); // Clear errors on cancel
  };

  const handleFormChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setIsUpdatingProfile(true);
    setProfileUpdateError(null);
    setProfileUpdateSuccess(false);
    let changesMade = false; // Flag to track if any valid changes were made
    try {
      const updatesToSend = {}; 

      const currentFullName = formData.full_name.trim();
      const originalFullName = (user?.full_name || '').trim();
      const currentCalendarUrl = formData.calendar_url.trim();
      const originalCalendarUrl = (user?.calendar_url || '').trim();

      // Check if full_name changed
      if (currentFullName !== originalFullName) {
          updatesToSend.full_name = currentFullName; 
          changesMade = true;
      }
      
      // Check if calendar_url changed 
      if (currentCalendarUrl !== originalCalendarUrl) {
          let isValidUrl = true;
          if (currentCalendarUrl) { // Only validate if not empty
              try {
                  new URL(currentCalendarUrl);
              } catch (urlError) {
                  console.error("URL Validation Error:", urlError);
                  isValidUrl = false;
                  // Set specific error and prevent saving this field
                  setProfileUpdateError('Invalid Calendar URL format. Please enter a full URL (e.g., https://...).');
              }
          }

          // Only add to updates if the URL is valid (or empty)
          if (isValidUrl) {
              updatesToSend.calendar_url = currentCalendarUrl;
              changesMade = true; // Mark change as made only if URL is valid/empty
          }
          // If URL is invalid, we set the error above and DON'T add it to updatesToSend
          // The component will stay in edit mode due to the error state
      }

      console.log("Updates to send:", updatesToSend);

      // Only call API if there are valid updates AND no URL validation error occurred
      if (Object.keys(updatesToSend).length > 0 && !profileUpdateError) { 
          await updateUserProfile(updatesToSend);
          setProfileUpdateSuccess(true); 
          setEditMode(false); // Exit edit mode only on successful save
      } else if (!changesMade) { // Check if no valid changes were identified
          console.log("No valid changes detected, exiting edit mode.");
          setEditMode(false); // Exit edit mode if no changes were made
      }
      // If profileUpdateError is set (e.g., invalid URL), stay in edit mode

    } catch (err) { // Catch errors from updateUserProfile API call
      console.error('Failed to update profile (API Error):', err);
      setProfileUpdateError(err.message || 'Failed to save profile changes.');
      // Stay in edit mode on API error
    } finally {
      setIsUpdatingProfile(false);
    }
  };
  // -----------------------

  // --- Verification Logic (remains the same) ---
  const handleSendOtp = async () => {
    if (!userPhoneNumberInput) {
      setVerificationError('Please enter a phone number.');
      return;
    }
    if (!/^\+[1-9]\d{1,14}$/.test(userPhoneNumberInput)) {
        setVerificationError('Please enter phone number in E.164 format (e.g., +12223334444).');
        return;
    }
    setIsSendingOtp(true);
    setVerificationError(null);
    setVerificationStatus('sending');
    try {
      await verificationAPI.sendOtp(userPhoneNumberInput);
      setVerificationStatus('otpSent');
    } catch (err) {
      setVerificationError(err.message || 'Failed to send OTP.');
      setVerificationStatus('error');
    } finally {
      setIsSendingOtp(false);
    }
  };

  const handleCheckOtp = async () => {
    if (!otpCode) {
      setVerificationError('Please enter the verification code.');
      return;
    }
    setIsCheckingOtp(true);
    setVerificationError(null);
    setVerificationStatus('verifying');
    try {
      const result = await verificationAPI.checkOtp(userPhoneNumberInput, otpCode);
      if (result.verified) {
        await updateUserProfile({ user_number: userPhoneNumberInput });
        setVerificationStatus('verified'); 
        setOtpCode(''); 
      } else {
        throw new Error('Verification failed.'); 
      }
    } catch (err) {
      setVerificationError(err.message || 'Verification failed.');
      setVerificationStatus('error');
    } finally {
      setIsCheckingOtp(false);
    }
  };
  // ------------------------
  
  // Handle Assistant Number Purchase Success
  const handleAssistantPurchaseSuccess = async (purchasedNumber) => {
    setTwilioNumber(purchasedNumber);
    setShowAssistantNumberPurchase(false);
    await updateUserProfile({}); 
  };
  
  const timezones = [
    'UTC', 'America/New_York', 'America/Los_Angeles', 'Europe/London', 
    'Asia/Tokyo', 'Australia/Sydney', 'Pacific/Auckland'
  ];

  const isUserNumberVerified = !!user?.user_number;

  return (
    <div className="space-y-6">
      {/* Assistant Number Purchase Section */} 
      {showAssistantNumberPurchase ? (
        <TwilioNumberPurchase 
          onPurchaseSuccess={handleAssistantPurchaseSuccess}
          onCancel={() => setShowAssistantNumberPurchase(false)}
        />
      ) : (
        /* Profile Display/Edit Card */
      <Card>
            {/* Edit Mode Form */} 
            {editMode ? (
                <form onSubmit={handleProfileSubmit} className="p-5">
                     <h2 className="text-xl font-semibold mb-4">Edit Profile</h2>
                     {profileUpdateError && (
                         <div className="mb-4 text-red-600 bg-red-100 p-3 rounded-md text-sm">{profileUpdateError}</div>
                     )}
                    {/* Full Name Input */} 
                    <div className="mb-4">
                         <Input
                            label="Full Name"
                            name="full_name"
                            value={formData.full_name}
                            onChange={handleFormChange}
                            required
            />
          </div>
                    {/* Email (Readonly) */} 
                    <div className="mb-4">
                         <Input
                            label="Email"
                            name="email"
              type="email"
              value={user?.email || ''}
              readOnly
                            disabled
                         />
                    </div>
                    {/* Calendar Link Input */} 
                    <div className="mb-6">
                         <Input
                            label="Calendar Booking Link"
                            name="calendar_url"
                            type="url"
                            value={formData.calendar_url}
                            onChange={handleFormChange}
                            placeholder="https://your-calendar-link.com"
            />
          </div>
                    {/* Action Buttons */} 
                    <div className="flex items-center gap-3">
                        <Button type="submit" isLoading={isUpdatingProfile} disabled={isUpdatingProfile}>
                           {isUpdatingProfile ? 'Saving...' : 'Save Changes'}
                        </Button>
                        <Button type="button" variant="outline" onClick={handleCancelClick} disabled={isUpdatingProfile}>
                            Cancel
                        </Button>
                    </div>
                </form>
            ) : (
                /* View Mode Display */
                <div className="p-5">
                     <div className="flex justify-between items-center mb-4">
                         <h2 className="text-xl font-semibold">Your Profile</h2>
                         <Button variant="outline" onClick={handleEditClick}>Edit Profile</Button>
                     </div>
                     {profileUpdateSuccess && (
                         <div className="mb-4 text-green-600 bg-green-100 p-3 rounded-md text-sm">Profile updated successfully!</div>
                     )}
                     <div className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
                        {/* Display Fields */} 
                        <div>
                            <h3 className="text-sm font-medium text-gray-500">Full Name</h3>
                            <p>{user?.full_name || '-'}</p>
                        </div>
                        <div>
                            <h3 className="text-sm font-medium text-gray-500">Email</h3>
                            <p>{user?.email || '-'}</p>
                        </div>
                        <div>
                            <h3 className="text-sm font-medium text-gray-500">Calendar Booking Link</h3>
                            <p>{user?.calendar_url ? (
                                <a href={user.calendar_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{user.calendar_url}</a>
                            ) : '-'}</p>
                        </div>
                        {/* Timezone (still direct update) */} 
          <div>
            <label className="flex items-center text-sm font-medium text-gray-700">
              <Globe className="w-4 h-4 mr-2" />
              Timezone
            </label>
            <select 
              value={user?.timezone || 'UTC'}
              onChange={handleTimezoneChange}
                                className="input-field w-full mt-1"
            >
              {timezones.map(tz => (
                <option key={tz} value={tz}>{tz}</option>
              ))}
            </select>
          </div>
                     </div>
                </div>
            )}

            {/* Phone Verification & Assistant Number Sections (Outside Edit Mode) */}
            {!editMode && (
                <div className="border-t border-gray-200 p-5 space-y-6">
                    {/* User Phone Number Section */}
                    <div >
            <label className="flex items-center text-sm font-medium text-gray-700">
              <Phone className="w-4 h-4 mr-2" />
                            Your Phone Number (for Call Forwarding/SMS)
            </label>
                        <div className="mt-1 flex items-start gap-3">
                            <Input
              type="tel"
                            value={userPhoneNumberInput}
              placeholder="+1234567890"
                            onChange={(e) => setUserPhoneNumberInput(e.target.value)}
                            className={`input-field flex-1 ${isUserNumberVerified ? 'bg-gray-50' : ''}`}
                            readOnly={isUserNumberVerified || verificationStatus === 'otpSent' || verificationStatus === 'verifying'}
                            />
                            {!isUserNumberVerified && verificationStatus !== 'otpSent' && (
                            <Button
                                onClick={handleSendOtp}
                                isLoading={isSendingOtp}
                                disabled={isSendingOtp || !userPhoneNumberInput || verificationStatus === 'otpSent'}
                                className="shrink-0 mt-1"
                                >
                                {isSendingOtp ? 'Sending...' : 'Send Code'}
                                </Button>
                            )}
                        </div>
                        <p className="mt-1 text-xs text-gray-500">
                            Enter in E.164 format (e.g., +12223334444).
                        </p>
                        {isUserNumberVerified && (
                            <p className="mt-1 text-sm text-green-600 flex items-center gap-1"><Check className="w-4 h-4"/> Verified</p>
                        )}
          </div>

                    {/* OTP Input Section */} 
                    {verificationStatus === 'otpSent' && (
                        <div className="border-t pt-4 border-dashed">
                            <label className="flex items-center text-sm font-medium text-gray-700">
                                Verification Code
                            </label>
                            <p className="mt-1 mb-2 text-sm text-gray-600">
                                Enter the code sent to {userPhoneNumberInput}.
                            </p>
                            <div className="flex items-start gap-3">
                                <Input
                                type="text"
                                value={otpCode}
                                onChange={(e) => setOtpCode(e.target.value)}
                                placeholder="Enter 6-digit code"
                                className="input-field flex-1"
                                maxLength={10} 
                                />
                                <Button
                                onClick={handleCheckOtp}
                                isLoading={isCheckingOtp}
                                disabled={isCheckingOtp || !otpCode}
                                className="shrink-0 mt-1"
                                >
                                {isCheckingOtp ? 'Verifying...' : 'Verify Code'}
                                </Button>
                            </div>
                        </div>
                    )}
                    
                    {/* Verification Error Display */} 
                    {(verificationStatus === 'error' || verificationStatus === 'otpSent') && verificationError && (
                        <div className="text-red-600 text-sm flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4" />
                            {verificationError}
                        </div>
                    )}

                    {/* Assistant Phone Number */} 
                    <div className="border-t pt-4">
            <label className="flex items-center text-sm font-medium text-gray-700">
              <Phone className="w-4 h-4 mr-2" />
                            Assistant Phone Number
            </label>
                        <div className="mt-1 flex items-center gap-3">
            <input
              type="tel"
                            value={twilioNumber || ''}
              readOnly
                            className="input-field bg-gray-50 flex-1"
              placeholder="Not assigned yet"
            />
                            {!twilioNumber && (
                            <Button
                                onClick={() => setShowAssistantNumberPurchase(true)}
                                className="flex items-center gap-1 shrink-0"
                            >
                                <PlusCircle className="w-4 h-4" />
                                Get Assistant Number
                            </Button>
                            )}
                        </div>
                        {twilioNumberError && (
                            <p className="mt-2 text-red-500 text-sm">{twilioNumberError}</p>
                        )}
          </div>
        </div>
            )}
      </Card>
      )}
    </div>
  );
};
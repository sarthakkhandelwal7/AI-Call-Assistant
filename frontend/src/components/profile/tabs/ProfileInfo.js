// src/components/profile/tabs/ProfileInfo.js
import React from 'react';
import { User, Mail, Clock, Globe, Phone } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import { Card } from '../../common/ui';

export const ProfileInfo = () => {
  const { user, updateUserProfile, getCsrfToken } = useAuth();
  
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
  
  // Handle Timezone Change (PUT - Needs CSRF)
  const handleTimezoneChange = async (e) => {
    const csrfToken = getCsrfToken();
    if (!csrfToken) {
        console.error("CSRF Token missing for timezone change");
        // Handle error appropriately, maybe show a message
        return; 
    }
    try {
      // Pass csrfToken to updateUserProfile
      await updateUserProfile({ timezone: e.target.value }, csrfToken);
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
    let changesMade = false;

    const csrfToken = getCsrfToken(); // Get CSRF token
    if (!csrfToken) {
        setProfileUpdateError("Security token missing. Please log in again.");
        setIsUpdatingProfile(false);
        return;
    }

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
          // Pass updatesToSend AND csrfToken
          await updateUserProfile(updatesToSend, csrfToken); 
          setProfileUpdateSuccess(true); 
          setEditMode(false); 
      } else if (!changesMade) {
          console.log("No valid changes detected, exiting edit mode.");
          setEditMode(false);
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

    const csrfToken = getCsrfToken(); // Get CSRF token
    if (!csrfToken) {
        setVerificationError("Security token missing. Please log in again.");
        return; 
    }

    setIsSendingOtp(true);
    setVerificationError(null);
    setVerificationStatus('sending');
    try {
      // Pass phone number AND csrfToken
      await verificationAPI.sendOtp(userPhoneNumberInput, csrfToken);
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

    const csrfToken = getCsrfToken(); // Get CSRF token
    if (!csrfToken) {
        setVerificationError("Security token missing. Please log in again.");
        return; 
    }

    setIsCheckingOtp(true);
    setVerificationError(null);
    setVerificationStatus('verifying');
    try {
      // Pass phone number, code, AND csrfToken
      const result = await verificationAPI.checkOtp(userPhoneNumberInput, otpCode, csrfToken);
      if (result.verified) {
        console.log("[handleCheckOtp] Check OTP successful. Preparing to call updateUserProfile.");
        console.log("[handleCheckOtp] CSRF Token being passed to updateUserProfile:", csrfToken);
        await updateUserProfile({ user_number: userPhoneNumberInput }, csrfToken);
        console.log("[handleCheckOtp] updateUserProfile call completed.");
        setVerificationStatus('verified'); 
        setOtpCode(''); 
      } else {
        throw new Error('Verification failed.'); 
      }
    } catch (err) {
      console.error("[handleCheckOtp] Error during checkOtp or updateUserProfile:", err);
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
    // updateUserProfile called here to refresh user state after purchase
    // This call itself might need a CSRF token if it updates profile
    // Let's assume updateUserProfile handles its own CSRF internally for now, 
    // but if TwilioNumberPurchase directly calls buyNumber, it needs the token.
    // const csrfToken = getCsrfToken();
    // await updateUserProfile({}, csrfToken); // Refresh user data
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
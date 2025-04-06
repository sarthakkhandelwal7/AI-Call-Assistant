const API_BASE_URL = 'http://localhost:8000';

const makeRequest = async (url, options = {}) => {
  try {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      credentials: 'include',
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `Request failed with status ${response.status}`);
    }

    if (response.status === 204) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};

// Auth API
export const authAPI = {
  getUserInfo: () => makeRequest('/auth/get-user-info'),
  logout: () => makeRequest('/auth/logout', { method: 'POST' }),
  googleLogin: (code) => makeRequest('/auth/google-login', {
    method: 'POST',
    body: JSON.stringify({ code }),
  }),
};

// User API section
export const userAPI = {
  updateProfile: (data) => makeRequest('/user/update-profile', {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
};

// Phone Number API
export const phoneNumberAPI = {
  getRegisteredTwilioNumber: () => makeRequest('/phone-number/get-registered-twilio-number'),
  getAvailableNumbers: (areaCode = 'US') => makeRequest(`/phone-number/available-numbers?area_code=${areaCode}`),
  buyNumber: (number) => makeRequest('/phone-number/buy-number', {
    method: 'POST',
    body: JSON.stringify({ number }),
  }),
};

// Verification API
export const verificationAPI = {
  sendOtp: (phoneNumber) => makeRequest('/verify/send-otp', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phoneNumber }),
  }),
  checkOtp: (phoneNumber, code) => makeRequest('/verify/check-otp', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phoneNumber, code }),
  }),
};

// Call API
export const callAPI = {
  getCallStatus: () => makeRequest('/calls/status'),
};

export default {
  auth: authAPI,
  user: userAPI,
  phoneNumber: phoneNumberAPI,
  verification: verificationAPI,
  call: callAPI,
}; 
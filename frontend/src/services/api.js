const API_BASE_URL = process.env.REACT_APP_API_URL;

// We will get the CSRF token from AuthContext when needed

const makeRequest = async (url, options = {}, csrfToken = null) => {
  try {
    // Prepare headers, ensuring Content-Type is set
    const requestHeaders = {
      'Content-Type': 'application/json',
      ...options.headers, // Include any headers passed in options
    };

    // Add CSRF token header if provided
    if (csrfToken) {
      requestHeaders['X-CSRF-Token'] = csrfToken;
    }

    // Construct final fetch options
    const fetchOptions = {
      ...options, // Spread original options (like method, body)
      credentials: 'include', // Always include credentials
      headers: requestHeaders, // Use the merged headers object
    };
    
    console.log(`[makeRequest] Sending ${fetchOptions.method || 'GET'} to ${url}`);
    // console.log("[makeRequest] Options:", fetchOptions); // Uncomment for deep debugging

    const response = await fetch(`${API_BASE_URL}${url}`, fetchOptions);

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
  // GET doesn't strictly need CSRF header based on current middleware
  getUserInfo: () => makeRequest('/auth/get-user-info'),
  
  // POST needs CSRF header
  logout: (csrfToken) => makeRequest('/auth/logout', { method: 'POST' }, csrfToken),
  
  // POST needs CSRF header (though login sets it, doesn't use existing one)
  googleLogin: (code) => makeRequest('/auth/google-login', {
    method: 'POST',
    body: JSON.stringify({ code }),
    // No CSRF header needed here as we are establishing the session
  }),
};

// User API section
export const userAPI = {
  // PUT needs CSRF header
  updateProfile: (data, csrfToken) => makeRequest('/user/update-profile', {
    method: 'PUT',
    body: JSON.stringify(data)
  }, csrfToken),
};

// Phone Number API
export const phoneNumberAPI = {
  // GET doesn't strictly need CSRF header
  getRegisteredTwilioNumber: () => makeRequest('/phone-number/get-registered-twilio-number'),
  getAvailableNumbers: (areaCode = 'US') => makeRequest(`/phone-number/available-numbers?area_code=${areaCode}`),
  
  // POST needs CSRF header
  buyNumber: (number, csrfToken) => makeRequest('/phone-number/buy-number', {
    method: 'POST',
    body: JSON.stringify({ number }),
  }, csrfToken),
};

// Verification API
export const verificationAPI = {
  // POST needs CSRF header
  sendOtp: (phoneNumber, csrfToken) => makeRequest('/verify/send-otp', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phoneNumber }),
  }, csrfToken),
  // POST needs CSRF header
  checkOtp: (phoneNumber, code, csrfToken) => makeRequest('/verify/check-otp', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phoneNumber, code }),
  }, csrfToken),
};

// Call API
export const callAPI = {
   // GET doesn't strictly need CSRF header
  getCallStatus: () => makeRequest('/calls/status'),
};

export default {
  auth: authAPI,
  user: userAPI,
  phoneNumber: phoneNumberAPI,
  verification: verificationAPI,
  call: callAPI,
}; 
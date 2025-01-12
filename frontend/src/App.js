import React from 'react';
import { useGoogleLogin } from '@react-oauth/google';

function App() {
  const login = useGoogleLogin({
    onSuccess: async (codeResponse) => {
      console.log('Google Auth Response:', codeResponse);
      try {
        const response = await fetch('http://localhost:8000/auth/google', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            code: codeResponse.code,
            redirect_uri: window.location.origin
          }),
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          console.error('Backend error:', errorData);
        } else {
          console.log('Successfully authenticated with Google Calendar');
        }
      } catch (error) {
        console.error('Error during authentication:', error);
      }
    },
    flow: 'auth-code',
    scope: 'https://www.googleapis.com/auth/calendar.events',
    access_type: 'offline',
    prompt: 'consent'
  });

  return (
    <div className="App">
      <div>
        <h1>Sign in with Google to enable Calendar access</h1>
        <button onClick={() => login()}>Sign in with Google</button>
      </div>
    </div>
  );
}

export default App;
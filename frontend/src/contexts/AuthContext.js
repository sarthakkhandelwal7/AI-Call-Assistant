import React, { createContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const getCsrfToken = () => document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf_token='))
        ?.split('=')[1];

    const makeAuthenticatedRequest = async (url, options = {}) => {
        const csrfToken = getCsrfToken();
        
        const headers = {
            ...options.headers,
            'X-CSRF-Token': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
        };

        return fetch(url, {
            ...options,
            credentials: 'include',
            headers
        });
    };

    const checkAuth = async () => {
        try {
            const response = await makeAuthenticatedRequest(
                'http://localhost:8000/auth/get-user-info'
            );

            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
            } else if (response.status === 401) {
                await refreshToken();
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const refreshToken = async () => {
        try {
            const response = await makeAuthenticatedRequest(
                'http://localhost:8000/auth/refresh',
                { method: 'POST' }
            );

            if (response.ok) {
                await checkAuth();
            } else {
                throw new Error('Failed to refresh token');
            }
        } catch (err) {
            setError(err.message);
            logout();
        }
    };

    const login = async (googleResponse) => {
        try {
            console.log('Full Google Response:', googleResponse);
            
            const response = await fetch('http://localhost:8000/auth/google-login', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    code: googleResponse.code  // Ensure this is a string
                })
            });
    
            console.log('Login Response Status:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Login Error:', errorText);
                throw new Error(errorText || 'Login failed');
            }
    
            const responseData = await response.json();
            console.log('Login Response Data:', responseData);
    
            await checkAuth();
        } catch (err) {
            console.error('Login Catch Error:', err);
            setError(err.message);
        }
    };

    const logout = async () => {
        try {
            await makeAuthenticatedRequest(
                'http://localhost:8000/auth/logout',
                { method: 'POST' }
            );
        } catch (err) {
            console.error('Logout error:', err);
        } finally {
            setUser(null);
        }
    };

    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    return (
        <AuthContext.Provider value={{
            user,
            loading,
            error,
            login,
            logout
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = React.useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
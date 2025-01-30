import React, { createContext, useState, useEffect, useCallback } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const getCsrfToken = useCallback(() => document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf_token='))
        ?.split('=')[1], []);

    const makeAuthenticatedRequest = useCallback(async (url, options = {}) => {
        try {
            const headers = {
                ...options.headers,
                'Content-Type': 'application/json',
            };
    
            const response = await fetch(url, {
                ...options,
                credentials: 'include',
                headers
            });
    
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || 'Request failed');
            }
    
            return response;
        } catch (error) {
            console.error('Request Error:', error);
            throw error;
        }
    }, []);

    const updateUserProfile = useCallback(async (updates) => {
        try {
            const response = await makeAuthenticatedRequest(
                'http://localhost:8000/auth/update-profile',
                {
                    method: 'POST',
                    body: JSON.stringify(updates)
                }
            );
            
            const updatedUser = await response.json();
            setUser(updatedUser);
            return updatedUser;
        } catch (err) {
            console.error('Update profile error:', err);
            throw err;
        }
    }, [makeAuthenticatedRequest]);

    const checkAuth = useCallback(async () => {
        try {
            const response = await makeAuthenticatedRequest(
                'http://localhost:8000/auth/get-user-info'
            );
    
            const userData = await response.json();
            setUser(userData);
        } catch (err) {
            console.error('Check Auth Error:', err);
            setUser(null);
        } finally {
            setLoading(false);
        }
    }, [makeAuthenticatedRequest]);

    const login = useCallback(async (googleResponse) => {
        try {
            const response = await fetch('http://localhost:8000/auth/google-login', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    code: googleResponse.code
                })
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || 'Login failed');
            }
    
            await checkAuth();
        } catch (err) {
            console.error('Login Error:', err);
            setError(err.message);
        }
    }, [checkAuth]);

    const logout = useCallback(async () => {
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
    }, [makeAuthenticatedRequest]);

    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    return (
        <AuthContext.Provider value={{
            user,
            loading,
            error,
            login,
            logout,
            updateUserProfile
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
import React, { createContext, useState, useEffect, useCallback } from 'react';
import { authAPI } from '../services/api';
import { userAPI } from '../services/api';

const AuthContext = createContext(null);

// Helper to store/retrieve CSRF token from session storage
const CSRF_TOKEN_KEY = 'csrfToken';
const storeCsrfToken = (token) => sessionStorage.setItem(CSRF_TOKEN_KEY, token);
const getStoredCsrfToken = () => sessionStorage.getItem(CSRF_TOKEN_KEY);
const removeCsrfToken = () => sessionStorage.removeItem(CSRF_TOKEN_KEY);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    // CSRF token is not directly part of state, managed via sessionStorage

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

    const fetchUser = useCallback(async () => {
        const token = localStorage.getItem('authToken');
        console.log("AuthContext: fetchUser called");
        if (getStoredCsrfToken()) {
             try {
                const data = await authAPI.getUserInfo();
                console.log("AuthContext: User data fetched:", data);
                setUser(data);
                setIsAuthenticated(true);
            } catch (error) {
                console.error('AuthContext: Failed to fetch user:', error);
                removeCsrfToken();
                setIsAuthenticated(false);
                setUser(null);
            } finally {
                setLoading(false);
            }
        } else {
            console.log("AuthContext: No CSRF token found, assuming not logged in");
            setLoading(false);
            setIsAuthenticated(false);
            setUser(null);
        }
    }, []);

    const updateUserProfile = useCallback(async (updates, csrfToken) => {
        try {
            const updatedUser = await userAPI.updateProfile(updates, csrfToken);
            setUser(updatedUser);
            return updatedUser;
        } catch (err) {
            console.error('Update profile error:', err);
            throw err;
        }
    }, [setUser]);

    const loginWithGoogle = async (code) => {
        setLoading(true);
        setError(null);
        console.log("AuthContext: loginWithGoogle called with code:", code);
        try {
            const data = await authAPI.googleLogin(code);
            console.log("AuthContext: Google login successful, data:", data);
            
            if (data.csrf_token) {
                storeCsrfToken(data.csrf_token);
                console.log("AuthContext: CSRF token stored");
                await fetchUser(); 
            } else {
                console.error("AuthContext: CSRF token missing from login response!");
                throw new Error('Login failed: Missing security token.');
            }

        } catch (error) {
            console.error('AuthContext: Google login error:', error);
            setError(error.message || 'Google login failed. Please try again.');
            removeCsrfToken();
            setUser(null);
            setIsAuthenticated(false);
        } finally {
            setLoading(false);
        }
    };

    const logout = async () => {
        setLoading(true);
        const csrfToken = getStoredCsrfToken();
        try {
            await authAPI.logout(csrfToken); 
            console.log("AuthContext: Logout successful on backend");
        } catch (error) {
            console.error('AuthContext: Failed to logout on backend:', error);
        } finally {
            removeCsrfToken();
            setUser(null);
            setIsAuthenticated(false);
            setLoading(false);
            console.log("AuthContext: Client-side logout complete");
        }
    };

    useEffect(() => {
        fetchUser();
    }, [fetchUser]);

    return (
        <AuthContext.Provider value={{
            user,
            loading,
            error,
            login: loginWithGoogle,
            logout,
            updateUserProfile,
            isAuthenticated,
            getCsrfToken: getStoredCsrfToken 
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
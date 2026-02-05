import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // ✅ Refined guest creation to handle retries properly
    const createGuestSession = useCallback(async () => {
        try {
            console.log("🆕 Creating new guest session...");
            // Remove old token first to force fresh start
            localStorage.removeItem('auth_token');
            setUser(null);

            const response = await api.post('/auth/guest');
            const { access_token } = response.data;
            if (access_token) {
                localStorage.setItem('auth_token', access_token);
                // Fetch user immediately after setting token
                await fetchUser();
            }
        } catch (error) {
            console.error("Failed to create guest session:", error);
            setLoading(false);
        }
    }, []);

    const fetchUser = useCallback(async () => {
        try {
            const token = localStorage.getItem('auth_token');
            if (!token) throw new Error("No token");

            const response = await api.get('/auth/me');
            setUser(response.data);
        } catch (error) {
            console.error("Error fetching user:", error);

            // Critical Fix: If fetching user fails (401), we MUST clear token and retry guest session ONE time.
            const token = localStorage.getItem('auth_token');
            if (token) {
                console.warn("Invalid token detected, refreshing guest session...");
                localStorage.removeItem('auth_token');
                // Avoid infinite loop: delay slightly or check logic
                setTimeout(() => createGuestSession(), 500);
            } else {
                createGuestSession();
            }
        } finally {
            setLoading(false);
        }
    }, [createGuestSession]);

    // Initial Load
    useEffect(() => {
        const token = localStorage.getItem('auth_token');
        if (token) {
            fetchUser();
        } else {
            createGuestSession();
        }
    }, [createGuestSession, fetchUser]);

    // Interceptor Logic Hook (optional, but good for global auth state)

    const login = async (email, password) => {
        try {
            const response = await api.post('/auth/login', null, {
                params: { email, password }
            });
            const { access_token } = response.data;
            localStorage.setItem('auth_token', access_token);
            await fetchUser();
            return true;
        } catch (error) {
            console.error("Login failed:", error);
            throw error;
        }
    };

    const logout = () => {
        localStorage.removeItem('auth_token');
        setUser(null);
        createGuestSession();
    };

    const register = async (userData) => {
        try {
            await api.post('/auth/register', userData);
            return true;
        } catch (error) {
            throw error;
        }
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, register, loading, createGuestSession }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);

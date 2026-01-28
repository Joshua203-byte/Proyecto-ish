import { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    // Default to a guest user immediately
    const [user, setUser] = useState({
        id: "guest-user-123",
        email: "guest@gpu-cloud.local",
        full_name: "Guest User",
        is_active: true,
        credits: 0 // Will be fetched from backend if needed, or managed locally for guest
    });
    const [loading, setLoading] = useState(false);

    // Initial load - just to potentially fetch fresh credits or status
    useEffect(() => {
        // Here we could fetch guest credits if we had a guest API
        console.log("🔐 AuthProvider: Guest session active.");
    }, []);

    const login = async () => {
        // No-op or auto-success
        return true;
    };

    const logout = () => {
        // No-op in guest mode
        console.log("Logout ignored in guest mode");
    };

    const register = async () => {
        // No-op
        return true;
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, register, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);

import { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [debugInfo, setDebugInfo] = useState("Initializing...");

    useEffect(() => {
        const loadUser = async () => {
            console.log("🔐 AuthProvider: Starting loadUser...");
            setDebugInfo("Checking local token...");

            const token = localStorage.getItem('auth_token');
            if (token) {
                console.log("🔐 AuthProvider: Found token, fetching user profile...");
                setDebugInfo("Fetching profile from backend...");

                // Add a local timeout to prevent hanging forever
                const timeoutPromise = new Promise((_, reject) =>
                    setTimeout(() => reject(new Error("Timeout: Backend took too long")), 5000)
                );

                try {
                    const profilePromise = api.get('/auth/me');
                    const { data } = await Promise.race([profilePromise, timeoutPromise]);

                    console.log("🔐 AuthContext: User loaded successfully");
                    setUser(data);
                } catch (err) {
                    console.error("🔐 AuthContext: Failed to load user", err);
                    // Only clear token if we AREN'T on the login page
                    // to prevent clearing toasts or causing loops
                    if (window.location.pathname !== '/login') {
                        localStorage.removeItem('auth_token');
                    }
                }
            } else {
                console.log("🔐 AuthProvider: No token found, continuing as guest");
                setDebugInfo("No session found.");
            }

            console.log("🔐 AuthProvider: Loading complete.");
            setLoading(false);
        };

        loadUser();
    }, []);

    const login = async (email, password) => {
        try {
            const { data } = await api.post('/auth/login', null, {
                params: { email, password }
            });
            localStorage.setItem('auth_token', data.access_token);
            const userResp = await api.get('/auth/me');
            setUser(userResp.data);
            return true;
        } catch (error) {
            console.error("Login Error:", error);
            throw error;
        }
    };

    const logout = () => {
        localStorage.removeItem('auth_token');
        setUser(null);
    };

    const register = async (email, password, fullName) => {
        const { data } = await api.post('/auth/register', {
            email,
            password,
            full_name: fullName
        });
        return data;
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, register, loading }}>
            {loading ? (
                <div className="min-h-screen bg-black flex flex-col items-center justify-center p-6 text-center">
                    <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin mb-6"></div>
                    <div className="text-white font-mono text-lg animate-pulse">Loading System...</div>
                    <div className="mt-4 text-zinc-500 text-sm font-mono">{debugInfo}</div>
                    <button
                        onClick={() => setLoading(false)}
                        className="mt-8 px-4 py-2 text-xs border border-zinc-800 text-zinc-600 hover:text-white hover:border-zinc-400 transition-colors uppercase tracking-widest"
                    >
                        Skip Loading (Debug)
                    </button>
                </div>
            ) : children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);

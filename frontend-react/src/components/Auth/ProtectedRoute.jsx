import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export const ProtectedRoute = ({ children }) => {
    const { user, loading } = useAuth();

    if (loading) {
        // You can replace this with a nice spinner
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#0a0a0a', color: 'white' }}>
                Loading...
            </div>
        );
    }

    // If no user but loading finished, it means we are in a retry loop or failed.
    // Since we don't have a login page, we show a 'Connecting' state or retry button.
    if (!user) {
        return (
            <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
                <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
                <h2 className="text-xl font-serif font-bold text-primary">Connecting to Epochly...</h2>
                <p className="text-secondary text-sm mt-2">Establishing secure guest session.</p>
            </div>
        );
    }

    return children;
};

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Toaster } from 'sonner';
import { ProtectedRoute } from './components/Auth/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Landing from './pages/Landing';

import './styles/styles.css';
import './styles/auth.css';
import './styles/components.css';
import './styles/animations.css';
import './styles/dashboard.css';
import './styles/terminal.css';

function App() {
  return (
    <AuthProvider>
      <Toaster
        theme="dark"
        position="top-right"
        expand={true}
        richColors
        toastOptions={{
          style: {
            background: '#09090b',
            border: '1px solid #27272a',
            color: '#fff',
          },
        }}
      />
      <Router>
        <Routes>
          <Route
            path="/dashboard/*"
            element={
              // ProtectedRoute is effectively a passthrough now, or we can remove it.
              // Keeping it for now as it wraps the dashboard layout logic if any.
              // Since AuthContext always provides a user, this will always grant access.
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          {/* Redirect root directly to dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;

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
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/dashboard/*"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          {/* Redirect root to dashboard (will go to login if not auth) */}
          <Route path="/" element={<Landing />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;

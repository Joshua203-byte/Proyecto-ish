import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
    const { login } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        const email = e.target.email.value;
        const password = e.target.password.value;

        try {
            await login(email, password);
            navigate('/dashboard');
        } catch (err) {
            console.error(err);
            // Use the specific message from the error object or fallback
            setError(err.message || err.response?.data?.detail || 'Login failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            {/* Animated Background */}
            <div className="bg-grid"></div>
            <div className="bg-glow"></div>

            {/* Auth Container */}
            <div className="auth-container">
                {/* Brand Side */}
                <div className="auth-brand">
                    <div className="auth-brand-content">
                        <Link to="/" className="auth-logo">
                            <div className="logo-icon">
                                <svg viewBox="0 0 40 40" fill="none">
                                    <rect x="4" y="8" width="32" height="24" rx="2" stroke="currentColor" strokeWidth="2" />
                                    <path d="M12 16h4v8h-4z" fill="currentColor" opacity="0.8" />
                                    <path d="M18 14h4v10h-4z" fill="currentColor" />
                                    <path d="M24 12h4v12h-4z" fill="currentColor" opacity="0.8" />
                                </svg>
                            </div>
                            <span className="logo-text">HOME<span className="accent">GPU</span>CLOUD</span>
                        </Link>

                        <h1 className="auth-brand-title">
                            Welcome Back
                        </h1>
                        <p className="auth-brand-subtitle">
                            Access your GPU computing power. Train models, run experiments, and scale your ML projects.
                        </p>

                        <div className="auth-features">
                            <div className="auth-feature">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                                <span>Instant GPU Access</span>
                            </div>
                            <div className="auth-feature">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="12" cy="12" r="10" />
                                    <path d="M12 6v6l4 2" />
                                </svg>
                                <span>Pay Per Minute</span>
                            </div>
                            <div className="auth-feature">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                                </svg>
                                <span>Secure & Isolated</span>
                            </div>
                        </div>
                    </div>

                    <div className="auth-brand-visual">
                        <div className="gpu-card-mini glass-dark">
                            <div className="mini-stat">
                                <span className="mini-label">Active GPUs</span>
                                <span className="mini-value gradient-text">12</span>
                            </div>
                            <div className="mini-stat">
                                <span className="mini-label">Jobs Running</span>
                                <span className="mini-value">47</span>
                            </div>
                            <div className="mini-stat">
                                <span className="mini-label">Uptime</span>
                                <span className="mini-value">99.9%</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Form Side */}
                <div className="auth-form-container">
                    <div className="auth-form-wrapper">
                        <div className="auth-form-header">
                            <h2>Sign In</h2>
                            <p>Enter your credentials to access your account</p>
                        </div>

                        <form onSubmit={handleSubmit} className="auth-form">
                            <div className="form-group">
                                <label className="form-label" htmlFor="email">Email Address</label>
                                <input
                                    type="email"
                                    id="email"
                                    name="email"
                                    className="form-input"
                                    placeholder="you@example.com"
                                    required
                                    autoComplete="email"
                                />
                            </div>

                            <div className="form-group">
                                <div className="form-label-row">
                                    <label className="form-label" htmlFor="password">Password</label>
                                    <a href="#" className="form-link">Forgot password?</a>
                                </div>
                                <div className="input-group">
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        id="password"
                                        name="password"
                                        className="form-input"
                                        placeholder="••••••••"
                                        required
                                        autoComplete="current-password"
                                    />
                                    <button
                                        type="button"
                                        className="input-toggle"
                                        aria-label="Toggle password visibility"
                                        onClick={() => setShowPassword(!showPassword)}
                                    >
                                        {showPassword ? (
                                            <svg className="eye-open" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                                <circle cx="12" cy="12" r="3" />
                                            </svg>
                                        ) : (
                                            <svg className="eye-closed" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                                                <line x1="1" y1="1" x2="23" y2="23" />
                                            </svg>
                                        )}
                                    </button>
                                </div>
                            </div>

                            <div className="form-group">
                                <label className="form-check">
                                    <input type="checkbox" name="remember" defaultChecked />
                                    <span className="form-check-label">Remember me for 30 days</span>
                                </label>
                            </div>

                            <button type="submit" className="btn btn-primary btn-block btn-lg glow-effect" disabled={loading}>
                                {loading ? (
                                    <>
                                        <span className="spinner spinner-sm"></span> Signing in...
                                    </>
                                ) : (
                                    <>
                                        <span>Sign In</span>
                                        <svg className="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M5 12h14M12 5l7 7-7 7" />
                                        </svg>
                                    </>
                                )}
                            </button>
                        </form>

                        <p className="auth-footer-text">
                            Don't have an account? <Link to="/register" className="form-link">Create one</Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

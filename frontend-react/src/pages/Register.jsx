import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Register() {
    const { register, login } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        const fullName = e.target.full_name.value;
        const email = e.target.email.value;
        const password = e.target.password.value;

        try {
            await register(email, password, fullName);
            // Auto-login
            await login(email, password);
            navigate('/dashboard');
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || 'Registration failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="bg-grid"></div>
            <div className="bg-glow"></div>

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

                        <h1 className="auth-brand-title">Starts Training Today</h1>
                        <p className="auth-brand-subtitle">
                            Create your account and get instant access to powerful NVIDIA GPUs for your machine learning projects.
                        </p>

                        <div className="auth-features">
                            <div className="auth-feature">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <polyline points="20 6 9 17 4 12" />
                                </svg>
                                <span>No credit card required</span>
                            </div>
                            <div className="auth-feature">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <polyline points="20 6 9 17 4 12" />
                                </svg>
                                <span>Free starter credits</span>
                            </div>
                            <div className="auth-feature">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <polyline points="20 6 9 17 4 12" />
                                </svg>
                                <span>Cancel anytime</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Form Side */}
                <div className="auth-form-container">
                    <div className="auth-form-wrapper">
                        <div className="auth-form-header">
                            <h2>Create Account</h2>
                            <p>Fill in your details to get started</p>
                        </div>

                        <form onSubmit={handleSubmit} className="auth-form">
                            <div className="form-group">
                                <label className="form-label" htmlFor="fullName">Full Name</label>
                                <input
                                    type="text"
                                    id="fullName"
                                    name="full_name"
                                    className="form-input"
                                    placeholder="John Doe"
                                    required
                                    autoComplete="name"
                                />
                            </div>

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
                                <label className="form-label" htmlFor="password">Password</label>
                                <div className="input-group">
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        id="password"
                                        name="password"
                                        className="form-input"
                                        placeholder="••••••••"
                                        required
                                        minLength="8"
                                        autoComplete="new-password"
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
                                <span className="form-hint">Must be at least 8 characters</span>
                            </div>

                            <div className="form-group">
                                <label className="form-check">
                                    <input type="checkbox" name="terms" required />
                                    <span className="form-check-label">
                                        I agree to the <a href="#">Terms of Service</a> and <a href="#">Privacy Policy</a>
                                    </span>
                                </label>
                            </div>

                            <button type="submit" className="btn btn-primary btn-block btn-lg glow-effect" disabled={loading}>
                                {loading ? (
                                    <>
                                        <span className="spinner spinner-sm"></span> Creating account...
                                    </>
                                ) : (
                                    <>
                                        <span>Create Account</span>
                                        <svg className="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M5 12h14M12 5l7 7-7 7" />
                                        </svg>
                                    </>
                                )}
                            </button>
                        </form>

                        <p className="auth-footer-text">
                            Already have an account? <Link to="/login" className="form-link">Sign in</Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

import React, { useState } from 'react';
import { UserPlus } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Register({ onNavigate }) {
  const { register } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email.trim() || !password) {
      setError('Please provide your email and password.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      await register(email.trim(), password, fullName.trim());
      onNavigate('/');
    } catch (err) {
      setError(err.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container" style={{ maxWidth: 440, marginTop: '3rem' }}>
      <div className="card" style={{ padding: '2.25rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div
            style={{
              width: 50,
              height: 50,
              borderRadius: '50%',
              backgroundColor: 'var(--primary-light)',
              color: 'var(--primary)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '0.75rem',
            }}
          >
            <UserPlus style={{ width: 24, height: 24 }} />
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Create an Account</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            Get your own private resume analysis workspace
          </p>
        </div>

        {error && (
          <div className="alert alert-danger" style={{ display: 'block', marginBottom: '1.25rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="reg-fullname">
              Full Name (Optional)
            </label>
            <input
              id="reg-fullname"
              type="text"
              className="form-input"
              placeholder="e.g. Alex Johnson"
              autoComplete="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="reg-email">
              Email Address <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <input
              id="reg-email"
              type="email"
              className="form-input"
              placeholder="name@example.com"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="reg-password">
              Password <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <input
              id="reg-password"
              type="password"
              className="form-input"
              placeholder="At least 6 characters"
              required
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="reg-confirm">
              Confirm Password <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <input
              id="reg-confirm"
              type="password"
              className="form-input"
              placeholder="Repeat your password"
              required
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ marginTop: '0.5rem', width: '100%' }}
          >
            {loading ? (
              <>
                <span className="spinner"></span> Creating Account...
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
          Already have an account?{' '}
          <button
            type="button"
            onClick={() => onNavigate('/login')}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--primary)',
              fontWeight: 600,
              cursor: 'pointer',
              textDecoration: 'underline',
              padding: 0,
            }}
          >
            Sign in
          </button>
        </div>
      </div>
    </main>
  );
}

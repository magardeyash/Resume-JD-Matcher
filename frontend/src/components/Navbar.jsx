import React from 'react';
import { FileText, LogOut, User, LogIn, UserPlus } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ currentPath, onNavigate }) {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header className="navbar">
      <div className="nav-container">
        <div className="brand" onClick={() => onNavigate('/')}>
          <FileText className="brand-icon" />
          <span>ResumeMatch</span>
        </div>
        <nav className="nav-links" style={{ alignItems: 'center' }}>
          <button
            type="button"
            className={`nav-link ${currentPath === '/' ? 'active' : ''}`}
            onClick={() => onNavigate('/')}
          >
            Dashboard
          </button>
          <button
            type="button"
            className={`nav-link ${currentPath === '/history' ? 'active' : ''}`}
            onClick={() => onNavigate('/history')}
          >
            History
          </button>

          {isAuthenticated ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginLeft: '0.5rem' }}>
              <span
                style={{
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  color: 'var(--text)',
                  backgroundColor: 'var(--primary-light)',
                  padding: '0.3rem 0.75rem',
                  borderRadius: '9999px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                }}
              >
                <User style={{ width: 14, height: 14, color: 'var(--primary)' }} />
                {user?.full_name || user?.email?.split('@')[0]}
              </span>
              <button
                type="button"
                onClick={() => {
                  logout();
                  onNavigate('/');
                }}
                className="btn btn-secondary"
                style={{ padding: '0.35rem 0.75rem', fontSize: '0.85rem' }}
                title="Log out"
              >
                <LogOut style={{ width: 15, height: 15 }} />
                <span>Logout</span>
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginLeft: '0.5rem' }}>
              <button
                type="button"
                className={`btn btn-secondary ${currentPath === '/login' ? 'active' : ''}`}
                style={{ padding: '0.4rem 0.85rem', fontSize: '0.85rem' }}
                onClick={() => onNavigate('/login')}
              >
                <LogIn style={{ width: 14, height: 14 }} />
                <span>Log In</span>
              </button>
              <button
                type="button"
                className="btn btn-primary"
                style={{ padding: '0.4rem 0.85rem', fontSize: '0.85rem', width: 'auto' }}
                onClick={() => onNavigate('/register')}
              >
                <UserPlus style={{ width: 14, height: 14 }} />
                <span>Sign Up</span>
              </button>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}

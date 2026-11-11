import React from 'react';
import { useAuth } from '../context/AuthContext';

export default function Banner({ onNavigate }) {
  const { isAuthenticated, user } = useAuth();

  if (isAuthenticated) {
    return (
      <aside
        style={{
          backgroundColor: '#ECFDF5',
          borderBottom: '1px solid #A7F3D0',
          color: '#065F46',
          padding: '0.5rem 1.5rem',
          fontSize: '0.85rem',
          textAlign: 'center',
        }}
      >
        🔒 <strong>Private Workspace:</strong> Logged in as <strong>{user?.email}</strong>. Your uploaded analyses and history are securely saved to your private account.
      </aside>
    );
  }

  return (
    <aside className="demo-banner">
      💡 <strong>Tip:</strong> You are currently in guest mode.{' '}
      <button
        type="button"
        onClick={() => onNavigate && onNavigate('/login')}
        style={{
          background: 'none',
          border: 'none',
          color: 'inherit',
          fontWeight: 700,
          textDecoration: 'underline',
          cursor: 'pointer',
          padding: 0,
        }}
      >
        Sign in
      </button>{' '}
      or{' '}
      <button
        type="button"
        onClick={() => onNavigate && onNavigate('/register')}
        style={{
          background: 'none',
          border: 'none',
          color: 'inherit',
          fontWeight: 700,
          textDecoration: 'underline',
          cursor: 'pointer',
          padding: 0,
        }}
      >
        Create an account
      </button>{' '}
      to save and access your personal resume analysis history across sessions.
    </aside>
  );
}

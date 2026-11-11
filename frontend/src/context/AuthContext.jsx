import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('resumematch_token') || null);
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('resumematch_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);

  // Verify token on mount
  useEffect(() => {
    async function checkMe() {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const res = await fetch('/api/auth/me', {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const userData = await res.json();
          setUser(userData);
          localStorage.setItem('resumematch_user', JSON.stringify(userData));
        } else {
          // Token expired or invalid
          logout();
        }
      } catch (err) {
        console.warn('Auth check failed:', err);
      } finally {
        setLoading(false);
      }
    }
    checkMe();
  }, [token]);

  const login = async (email, password) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Login failed.');
    }
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('resumematch_token', data.access_token);
    localStorage.setItem('resumematch_user', JSON.stringify(data.user));
    return data.user;
  };

  const register = async (email, password, fullName) => {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        password,
        full_name: fullName || null,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Registration failed.');
    }
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('resumematch_token', data.access_token);
    localStorage.setItem('resumematch_user', JSON.stringify(data.user));
    return data.user;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('resumematch_token');
    localStorage.removeItem('resumematch_user');
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        isAuthenticated: !!token && !!user,
        loading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

import React, { createContext, useContext, useState, useEffect } from 'react';
import API from '@/lib/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem('lifeos_token');
    const savedUser = localStorage.getItem('lifeos_user');
    if (saved && savedUser) {
      setToken(saved);
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const res = await API.post('/auth/login', { email, password });
    const { token: t, user: u } = res.data;
    setToken(t);
    setUser(u);
    localStorage.setItem('lifeos_token', t);
    localStorage.setItem('lifeos_user', JSON.stringify(u));
    return u;
  };

  const register = async (name, email, password) => {
    const res = await API.post('/auth/register', { name, email, password });
    const { token: t, user: u } = res.data;
    setToken(t);
    setUser(u);
    localStorage.setItem('lifeos_token', t);
    localStorage.setItem('lifeos_user', JSON.stringify(u));
    return u;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('lifeos_token');
    localStorage.removeItem('lifeos_user');
  };

  const updateUser = (data) => {
    const updated = { ...user, ...data };
    setUser(updated);
    localStorage.setItem('lifeos_user', JSON.stringify(updated));
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
};

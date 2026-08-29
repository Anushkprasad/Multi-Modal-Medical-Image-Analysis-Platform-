/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem('med_token') || null);
  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem('med_user');
    if (storedUser) {
      try {
        return JSON.parse(storedUser);
      } catch (e) {
        console.error("Failed to parse stored user", e);
        return null;
      }
    }
    return null;
  });
  const loading = false;

  const login = async (email) => {
    // In a real application, this would make an API request.
    // For now, simulate a successful login.
    const fakeToken = 'sample_jwt_token_' + Date.now();
    const fakeUser = { email, role: 'physician' };

    localStorage.setItem('med_token', fakeToken);
    localStorage.setItem('med_user', JSON.stringify(fakeUser));

    setToken(fakeToken);
    setUser(fakeUser);
  };

  const logout = () => {
    localStorage.removeItem('med_token');
    localStorage.removeItem('med_user');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    isAuthenticated: !!token,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;

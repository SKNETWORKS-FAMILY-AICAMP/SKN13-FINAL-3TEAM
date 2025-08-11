import React, { createContext, useContext, useState, useEffect } from 'react';
import { isAuthenticated, getUserProfile, logout } from '../services/authService';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // 초기 인증 상태 확인
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        if (isAuthenticated()) {
          const result = await getUserProfile();
          if (result.success) {
            setUser(result.user);
          } else {
            // 토큰이 있지만 유효하지 않은 경우
            await logout();
            setUser(null);
          }
        }
      } catch (error) {
        console.error('Auth check error:', error);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const login = (userData) => {
    setUser(userData);
  };

  const logoutUser = async () => {
    await logout();
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    logout: logoutUser,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 
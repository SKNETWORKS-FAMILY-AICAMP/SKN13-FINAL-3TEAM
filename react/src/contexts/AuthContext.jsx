import React, { createContext, useContext, useState, useEffect } from 'react';
// useNavigate를 제거하고, loginService를 직접 사용하지 않습니다.
import { 
  isAuthenticated as checkIsAuthenticated, 
  getUserProfile, 
  logout as logoutService
} from '../services/authService';

const AuthContext = createContext(null);

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

  useEffect(() => {
    const checkAuthStatus = async () => {
      setLoading(true);
      try {
        if (checkIsAuthenticated()) {
          const result = await getUserProfile();
          if (result.success) {
            setUser(result.user);
          } else {
            await logoutService();
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

  // [수정] Login 컴포넌트가 전달해준 user 데이터로 상태만 설정하는 간단한 역할로 되돌립니다.
  const login = (userData) => {
    setUser(userData);
  };

  const logout = async () => {
    await logoutService();
    setUser(null);
    // 페이지 이동 로직은 이 함수를 호출하는 컴포넌트(예: Header)가 담당하게 됩니다.
  };

  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};
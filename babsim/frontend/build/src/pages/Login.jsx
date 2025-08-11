import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { login, getMockUsers, resetMockData } from '../services/authService';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/Header';
import Footer from '../components/Footer';

function Login() {
  const navigate = useNavigate();
  const { login: authLogin } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showMockData, setShowMockData] = useState(false);

  const mockUsers = getMockUsers();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // 입력값 검증
    if (!formData.email || !formData.password) {
      setError('이메일과 비밀번호를 모두 입력해주세요.');
      setLoading(false);
      return;
    }

    try {
      const result = await login(formData.email, formData.password);
      
      if (result.success) {
        // 전역 인증 상태 업데이트
        authLogin(result.user);
        // 로그인 성공 시 홈페이지로 이동
        navigate('/');
      } else {
        setError(result.error || '로그인에 실패했습니다.');
      }
    } catch (error) {
      setError('로그인 중 오류가 발생했습니다.');
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSocialLogin = (provider) => {
    // 소셜 로그인 기능은 추후 구현
    alert(`${provider} 로그인은 아직 구현되지 않았습니다.`);
  };

  const handleQuickLogin = (email, password) => {
    setFormData({ email, password });
  };

  const handleResetMockData = () => {
    if (window.confirm('더미 데이터를 초기화하시겠습니까? 모든 회원가입 데이터가 삭제됩니다.')) {
      resetMockData();
    }
  };

  return (
    <div className="min-h-screen" style={{backgroundColor: '#353745'}}>
      <Header />
      
      {/* Main Content */}
      <div className="flex items-center justify-center min-h-screen py-12">
        <div className="max-w-6xl mx-auto px-4">
          {/* Title */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-white mb-4">Sign in</h1>
            <p className="text-gray-400">
              Don't have an account?{' '}
              <Link to="/signup" className="text-blue-400 hover:text-blue-300 transition-colors">
                Sign up
              </Link>
            </p>
          </div>

          {/* Mock Data Info */}
          <div className="bg-yellow-600 text-white p-4 rounded-lg mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold">🧪 개발 모드 - 더미 데이터 사용 중</h3>
                <p className="text-sm opacity-90">아래 계정으로 로그인하여 기능을 테스트해보세요.</p>
              </div>
              <div className="flex space-x-2">
                <button onClick={() => setShowMockData(!showMockData)} className="bg-yellow-700 px-3 py-1 rounded text-sm hover:bg-yellow-800 transition-colors">
                  {showMockData ? '숨기기' : '계정 보기'}
                </button>
                <button onClick={handleResetMockData} className="bg-red-600 px-3 py-1 rounded text-sm hover:bg-red-700 transition-colors" title="더미 데이터 초기화">
                  초기화
                </button>
              </div>
            </div>
            {showMockData && (
              <div className="mt-4 space-y-2">
                {mockUsers.map((user, index) => (
                  <div key={index} className="bg-yellow-700 p-3 rounded">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-medium">{user.name}</span>
                        <span className="text-sm opacity-90 ml-2">({user.email})</span>
                      </div>
                      <button onClick={() => handleQuickLogin(user.email, user.password)} className="bg-yellow-800 px-2 py-1 rounded text-xs hover:bg-yellow-900 transition-colors">
                        사용하기
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Login Form Container */}
          <div className="bg-dark-blue rounded-lg p-8 border border-gray-700">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Left Side - Traditional Login */}
              <div>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">
                      Email
                    </label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      placeholder="이메일을 입력해주세요."
                      className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-400"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">
                      Password
                    </label>
                    <input
                      type="password"
                      name="password"
                      value={formData.password}
                      onChange={handleInputChange}
                      placeholder="비밀번호를 입력해주세요."
                      className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-400"
                    />
                  </div>
                  
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? '로그인 중...' : 'Sign In'}
                  </button>
                </form>
              </div>

              {/* Right Side - Social Login */}
              <div className="flex flex-col justify-center">
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-600"></div>
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-dark-blue text-gray-400">or</span>
                  </div>
                </div>
                
                <div className="mt-6 space-y-4">
                  <button
                    onClick={() => handleSocialLogin('Google')}
                    className="w-full bg-white text-gray-900 py-3 px-6 rounded-lg font-semibold hover:bg-gray-100 transition-colors flex items-center justify-center space-x-3"
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    <span>Continue with Google</span>
                  </button>
                  
                  <button
                    onClick={() => handleSocialLogin('Naver')}
                    className="w-full bg-green-500 text-white py-3 px-6 rounded-lg font-semibold hover:bg-green-600 transition-colors flex items-center justify-center space-x-3"
                  >
                    <span className="font-bold text-lg">N</span>
                    <span>Continue with Naver</span>
                  </button>
                  
                  <button
                    onClick={() => handleSocialLogin('Kakao')}
                    className="w-full bg-yellow-400 text-black py-3 px-6 rounded-lg font-semibold hover:bg-yellow-500 transition-colors flex items-center justify-center space-x-3"
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 3C6.48 3 2 6.48 2 12s4.48 9 10 9 10-4.48 10-9S17.52 3 12 3zm0 16c-3.86 0-7-3.14-7-7s3.14-7 7-7 7 3.14 7 7-3.14 7-7 7z"/>
                    </svg>
                    <span>Continue with Kakao</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-4 bg-red-600 text-white p-4 rounded-lg">
              {error}
            </div>
          )}
        </div>
      </div>
      
      <Footer />
    </div>
  );
}

export default Login; 
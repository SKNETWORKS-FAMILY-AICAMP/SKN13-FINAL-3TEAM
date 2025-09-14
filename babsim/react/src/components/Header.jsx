import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Header({ isAssetLibrary = false }) {
  const { user, isAuthenticated, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const menuRef = useRef(null);
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    setIsMenuOpen(false);
  };

  // 메뉴 외부 클릭 시 닫기
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // 스크롤 감지
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY;
      // 100px 이상 스크롤하면 Header 숨김
      setIsScrolled(scrollTop > 100);
    };

    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      isAssetLibrary 
        ? 'bg-white shadow-md' 
        : isScrolled 
          ? 'transform -translate-y-full' 
          : 'bg-transparent'
    }`}>
      <div className="w-full px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo - Left */}
          <div className="flex-shrink-0">
            <Link to="/" className="block">
              <div className="font-bold text-2xl tracking-tight italic">
                <span style={{color: isAssetLibrary ? '#1f2937' : '#f6f3f2'}}>JJACK</span>
                <span style={{color: isAssetLibrary ? '#1f2937' : '#f6f3f2'}}>LETTE</span>
              </div>
              <div className={`text-xs tracking-wide italic ${isAssetLibrary ? 'text-gray-600' : 'text-gray-400'}`}>
                with Hyundai Car
              </div>
            </Link>
          </div>
          
          {/* Navigation Links - Center */}
          <nav className="flex gap-8">
            <Link 
              to="/" 
              className={`relative transition-all duration-300 font-medium text-base ${
                isAssetLibrary 
                  ? location.pathname === '/' 
                    ? 'text-gray-900 border-b-2 border-gray-900 pb-1' 
                    : 'text-gray-700 hover:text-gray-900'
                  : location.pathname === '/' 
                    ? 'text-white border-b-2 border-white pb-1' 
                    : 'text-white hover:text-gray-300'
              }`}
            >
              Home
            </Link>
            <Link 
              to="/" 
              className={`relative transition-all duration-300 font-medium text-base ${
                isAssetLibrary 
                  ? 'text-gray-700 hover:text-gray-900'
                  : 'text-white hover:text-gray-300'
              }`}
              onClick={(e) => {
                e.preventDefault();
                if (window.location.pathname === '/') {
                  const aboutSection = document.getElementById('about');
                  if (aboutSection) {
                    aboutSection.scrollIntoView({ behavior: 'smooth' });
                  }
                } else {
                  window.location.href = '/#about';
                }
              }}
            >
              About us
            </Link>
            <Link 
              to="/library" 
              className={`relative transition-all duration-300 font-medium text-base ${
                isAssetLibrary 
                  ? location.pathname === '/library' 
                    ? 'text-gray-900 border-b-2 border-gray-900 pb-1' 
                    : 'text-gray-700 hover:text-gray-900'
                  : location.pathname === '/library' 
                    ? 'text-white border-b-2 border-white pb-1' 
                    : 'text-white hover:text-gray-300'
              }`}
            >
              Asset Library
            </Link>
            <Link 
              to="/insights" 
              className={`relative transition-all duration-300 font-medium text-base ${
                isAssetLibrary 
                  ? location.pathname === '/insights' 
                    ? 'text-gray-900 border-b-2 border-gray-900 pb-1' 
                    : 'text-gray-700 hover:text-gray-900'
                  : location.pathname === '/insights' 
                    ? 'text-white border-b-2 border-white pb-1' 
                    : 'text-white hover:text-gray-300'
              }`}
            >
              Insight&Trends
            </Link>
            <Link 
              to="/lab" 
              className={`relative transition-all duration-300 font-medium text-base ${
                isAssetLibrary 
                  ? location.pathname === '/lab' 
                    ? 'text-gray-900 border-b-2 border-gray-900 pb-1' 
                    : 'text-gray-700 hover:text-gray-900'
                  : location.pathname === '/lab' 
                    ? 'text-white border-b-2 border-white pb-1' 
                    : 'text-white hover:text-gray-300'
              }`}
            >
              Prototype Lab
            </Link>
          </nav>

          {/* Action Buttons - Right */}
          <div className="flex items-center space-x-3">
            {isAuthenticated ? (
              // 로그인된 상태: 사용자 정보와 메뉴 버튼
              <div className="flex items-center space-x-4">
                <div className={`text-sm ${isAssetLibrary ? 'text-gray-700' : 'text-white'}`}>
                  <div className="font-medium">{user?.user_name}</div>
                  <div className={`text-xs ${isAssetLibrary ? 'text-gray-500' : 'text-gray-400'}`}>{user?.email}</div>
                </div>
                
                {/* 세 개의 점 메뉴 버튼 */}
                <div className="relative" ref={menuRef}>
                  <button 
                    onClick={() => setIsMenuOpen(!isMenuOpen)}
                    className={`p-2 rounded-lg transition-all duration-300 ${
                      isAssetLibrary 
                        ? 'text-gray-700 hover:bg-gray-100' 
                        : 'text-white hover:bg-gray-800/50'
                    }`}
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                    </svg>
                  </button>
                  
                  {/* 드롭다운 메뉴 */}
                  {isMenuOpen && (
                    <div className="absolute right-0 mt-2 w-48 bg-gray-900/95 backdrop-blur-md rounded-xl shadow-2xl py-2 z-50 border border-gray-700/50">
                      <Link 
                        to="/profile" 
                        className="block px-4 py-3 text-white hover:bg-gray-800/50 transition-all duration-300 rounded-lg mx-2"
                        onClick={() => setIsMenuOpen(false)}
                      >
                        Profile
                      </Link>
                      <Link 
                        to="/myworkspace" 
                        className="block px-4 py-3 text-white hover:bg-gray-800/50 transition-all duration-300 rounded-lg mx-2"
                        onClick={() => setIsMenuOpen(false)}
                      >
                        My Workspace
                      </Link>
                      <hr className="my-2 border-gray-700" />
                      <button 
                        onClick={handleLogout}
                        className="block w-full text-left px-4 py-3 text-red-400 hover:bg-red-500/10 transition-all duration-300 rounded-lg mx-2"
                      >
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              // 로그아웃된 상태: 로그인/회원가입 버튼
              <>
                <Link to="/login">
                  <button className={`px-8 py-3 rounded-full text-base font-semibold transition-all duration-300 transform hover:scale-105 ${
                    isAssetLibrary 
                      ? 'bg-transparent text-gray-700 border-2 border-gray-700 hover:bg-gray-700 hover:text-white' 
                      : 'bg-transparent text-white border-2 border-white hover:bg-white hover:text-gray-900'
                  }`}>
                    Sign in
                  </button>
                </Link>
                <Link to="/signup">
                  <button className={`px-8 py-3 rounded-full text-base font-semibold transition-all duration-300 transform hover:scale-105 shadow-lg ${
                    isAssetLibrary 
                      ? 'bg-gray-700 text-white hover:bg-gray-800' 
                      : 'bg-white text-gray-900 hover:bg-gray-100'
                  }`}>
                    Sign up
                  </button>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

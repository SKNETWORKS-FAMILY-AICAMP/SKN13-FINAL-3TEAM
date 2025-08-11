import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Header() {
  const { user, isAuthenticated, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
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

  return (
    <header className="bg-gray-800 rounded-t-lg" style={{ borderBottom: '1px solid #374151' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo - Left */}
          <div className="flex-shrink-0">
            <div className="text-white font-bold text-xl">
              <span style={{color: '#60a5fa'}}>JACK</span>
              <span>LETTE</span>
            </div>
            <div className="text-gray-400 text-sm">
              with Hyundai Car
            </div>
          </div>
          
                     {/* Navigation Links - Center */}
           <nav style={{display: 'flex', gap: '48px'}}>
             <Link 
               to="/" 
               className={`text-white hover:text-gray-300 transition-colors font-medium ${
                 location.pathname === '/' ? 'border-b-2 border-purple-500 pb-1' : ''
               }`} 
               style={{color: 'white', textDecoration: 'none'}}
             >
               Home
             </Link>
             <Link 
               to="/" 
               className="text-white hover:text-gray-300 transition-colors font-medium" 
               style={{color: 'white', textDecoration: 'none'}}
               onClick={(e) => {
                 e.preventDefault();
                 // 현재 페이지가 홈페이지인 경우에만 스크롤
                 if (window.location.pathname === '/') {
                   const aboutSection = document.getElementById('about');
                   if (aboutSection) {
                     aboutSection.scrollIntoView({ behavior: 'smooth' });
                   }
                 } else {
                   // 다른 페이지에서 홈페이지로 이동 후 스크롤
                   window.location.href = '/#about';
                 }
               }}
             >
               About us
             </Link>
             <Link 
               to="/library" 
               className={`text-white hover:text-gray-300 transition-colors font-medium ${
                 location.pathname === '/library' ? 'border-b-2 border-purple-500 pb-1' : ''
               }`} 
               style={{color: 'white', textDecoration: 'none'}}
             >
               Asset Library
             </Link>
             <Link 
               to="/insights" 
               className={`text-white hover:text-gray-300 transition-colors font-medium ${
                 location.pathname === '/insights' ? 'border-b-2 border-purple-500 pb-1' : ''
               }`} 
               style={{color: 'white', textDecoration: 'none'}}
             >
               Insight&Trends
             </Link>
             <Link 
               to="/lab" 
               className={`text-white hover:text-gray-300 transition-colors font-medium ${
                 location.pathname === '/lab' ? 'border-b-2 border-purple-500 pb-1' : ''
               }`} 
               style={{color: 'white', textDecoration: 'none'}}
             >
               Prototype Lab
             </Link>
           </nav>

          {/* Action Buttons - Right */}
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              // 로그인된 상태: 사용자 정보와 메뉴 버튼
              <div className="flex items-center space-x-4">
                <div className="text-white text-sm">
                  <div className="font-medium">{user?.user_name}</div>
                  <div className="text-gray-400">{user?.e_mail}</div>
                </div>
                
                {/* 세 개의 점 메뉴 버튼 */}
                <div className="relative" ref={menuRef}>
                  <button 
                    onClick={() => setIsMenuOpen(!isMenuOpen)}
                    className="text-white p-2 hover:bg-gray-700 rounded-lg transition-colors"
                  >
                    <div className="flex flex-col space-y-1">
                      <div className="w-1 h-1 bg-white rounded-full"></div>
                      <div className="w-1 h-1 bg-white rounded-full"></div>
                      <div className="w-1 h-1 bg-white rounded-full"></div>
                    </div>
                  </button>
                  
                                     {/* 드롭다운 메뉴 */}
                   {isMenuOpen && (
                     <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-2 z-50">
                       <Link 
                         to="/profile" 
                         className="block px-4 py-2 text-gray-700 hover:bg-gray-100 transition-colors"
                         onClick={() => setIsMenuOpen(false)}
                       >
                         Profile
                       </Link>
                       <Link 
                         to="/workspace" 
                         className="block px-4 py-2 text-gray-700 hover:bg-gray-100 transition-colors"
                         onClick={() => setIsMenuOpen(false)}
                       >
                         My Workspace
                       </Link>
                       <hr className="my-1" />
                       <button 
                         onClick={handleLogout}
                         className="block w-full text-left px-4 py-2 text-red-600 hover:bg-red-50 transition-colors"
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
                  <button className="bg-blue-700 text-white px-8 py-3 rounded-full hover:bg-blue-800 transition-colors font-medium" style={{backgroundColor: '#60a5fa'}}>
                    Sign in
                  </button>
                </Link>
                <Link to="/signup">
                  <button className="bg-white text-blue-700 px-8 py-3 rounded-full hover:bg-gray-100 transition-colors font-medium">
                    Sign up
                  </button>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
      {/* Full width border */}
      <div style={{ 
        position: 'absolute', 
        bottom: 0, 
        left: 0, 
        right: 0, 
        height: '1px', 
        backgroundColor: '#374151' 
      }}></div>
    </header>
  );
}

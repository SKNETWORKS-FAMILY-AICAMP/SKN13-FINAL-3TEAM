import React, { useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { USE_MOCK_DATA } from '../services/authService';
import Header from '../components/Header';
import HeroSection from '../components/HeroSection';
import AboutSection from '../components/AboutSection';
import FAQSection from '../components/FAQSection';
import ContactSection from '../components/ContactSection';
import Footer from '../components/Footer';

function Home() {
  const { user, isAuthenticated } = useAuth();

  // URL 해시를 감지하여 해당 섹션으로 스크롤
  useEffect(() => {
    const hash = window.location.hash;
    if (hash) {
      const element = document.querySelector(hash);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }
  }, []);

  return (
    <div className="min-h-screen" style={{backgroundColor: '#353745'}}>
      <Header />
      
      {/* 로그인 상태 표시 (테스트용) - Only show when USE_MOCK_DATA is true */}
      {USE_MOCK_DATA && isAuthenticated && (
        <div className="bg-green-600 text-white p-4 text-center">
          로그인됨: {user?.user_name} ({user?.email})
        </div>
      )}
      
      <HeroSection />
      <AboutSection />
      <FAQSection />
      <ContactSection />
      <Footer />
    </div>
  );  
}

export default Home; 
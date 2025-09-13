import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import carMain from '../assets/car_main.jpg';

function HeroSection() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleGetStarted = () => {
    if (isAuthenticated) {
      navigate('/lab');
    } else {
      navigate('/login');
    }
  };

  return (
    <section
      className="relative min-h-screen flex items-center overflow-hidden"
      style={{
        backgroundImage: `url('/car_main.jpg')`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed'
      }}
    >
      {/* Dark Overlay */}
      {/* <div className="absolute inset-0 bg-black bg-opacity-20"></div> */}

      {/* Content */}
      <div className="relative z-10 w-full px-8 sm:px-12 lg:px-16 xl:px-20 text-left">
        <div className="max-w-4xl">
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold text-white mb-6 leading-tight">
            AI-powered<br />
            Car Prototype Image<br />
            in minutes
          </h1>
          <p className="text-gray-200 text-lg md:text-xl mb-12 max-w-2xl leading-relaxed">
          텍스트 한 줄로, 당신의 자동차 디자인을 실현하세요.<br />
          자동차 디자이너를 위한 AI 이미지 생성 플랫폼 — 아이디어를 곧바로 눈앞에.
          </p>

        {/* Action Buttons - Left Aligned */} 
        <div className="flex flex-col sm:flex-row gap-6 justify-start items-start"> 
          <button 
            onClick={handleGetStarted}
            className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-10 py-4 rounded-full text-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition-all duration-300 transform hover:scale-105 shadow-lg"
          > 
            Get Started 
          </button> 
          <button className="bg-transparent text-white border-2 border-white px-10 py-4 rounded-full text-lg font-semibold hover:bg-white hover:text-gray-900 transition-all duration-300 transform hover:scale-105"> How it works </button> 
          </div> 
          </div> 
          </div>

      {/* Scroll Indicator */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-10">
        <button 
          onClick={() => {
            const gallerySection = document.getElementById('gallery');
            if (gallerySection) {
              gallerySection.scrollIntoView({ behavior: 'smooth' });
            }
          }}
          className="animate-bounce cursor-pointer hover:scale-110 transition-transform duration-300"
        >
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </button>
      </div>
    </section>
  );
}

export default HeroSection;

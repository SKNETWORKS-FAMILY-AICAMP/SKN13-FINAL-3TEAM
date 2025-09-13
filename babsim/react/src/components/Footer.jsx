import React from 'react';
import { Link } from 'react-router-dom';

function Footer({ isAssetLibrary = false }) {
  const quickMenuLinks = [
    { name: 'Home', path: '/' },
    { name: 'About Us', path: '/about' },
    { name: 'Asset Library', path: '/asset-library' },
    { name: 'Insight & Trends', path: '/insight-trends' },
    { name: 'Prototype Lab', path: '/lab' }
  ];

  return (
    <footer className={`${isAssetLibrary ? 'bg-white border-t border-gray-200' : 'bg-dark-blue border-t border-gray-700'}`}>
      <div className="w-full px-6 lg:px-8 py-12">
        <div className="flex flex-col items-center text-center">
          {/* Logo and Description */}
          <div className="mb-8">
            <h3 className={`${isAssetLibrary ? 'text-gray-900' : 'text-white'} font-bold text-xl mb-4`}>
              JACKLETTE with Hyundai Car
            </h3>
            <p className={`${isAssetLibrary ? 'text-gray-600' : 'text-gray-400'} mb-6`}>
              AI-powered automotive design support platform
            </p>
          </div>

          {/* Quick Menu */}
          <div className="mb-8">
            <h4 className={`${isAssetLibrary ? 'text-gray-900' : 'text-white'} font-semibold mb-4`}>Quick Menu</h4>
            <div className="flex flex-wrap justify-center gap-6">
              {quickMenuLinks.map((link, index) => (
                <Link
                  key={index}
                  to={link.path}
                  className={`${isAssetLibrary ? 'text-gray-600 hover:text-gray-900' : 'text-gray-400 hover:text-white'} transition-colors font-medium`}
                >
                  {link.name}
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom Section */}
        <div className={`${isAssetLibrary ? 'border-t border-gray-200' : 'border-t border-gray-700'} mt-8 pt-8 flex flex-col md:flex-row justify-between items-center`}>
          <p className={`${isAssetLibrary ? 'text-gray-600' : 'text-gray-400'} text-sm`}>
            © Copyright 2025, all right reserved by Babsim
          </p>
          <div className="flex space-x-4 mt-4 md:mt-0">
            <button className={`${isAssetLibrary ? 'text-gray-600 hover:text-gray-900' : 'text-gray-400 hover:text-white'} transition-colors`}>
              <span className="text-lg">a</span>
            </button>
            <button className={`${isAssetLibrary ? 'text-gray-600 hover:text-gray-900' : 'text-gray-400 hover:text-white'} transition-colors`}>
              <span className="text-lg">⊞</span>
            </button>
            <button className={`${isAssetLibrary ? 'text-gray-600 hover:text-gray-900' : 'text-gray-400 hover:text-white'} transition-colors`}>
              <span className="text-lg">×</span>
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer; 
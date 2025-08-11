import React from 'react';
import { Link } from 'react-router-dom';

export default function Header() {
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
            <Link to="/" className="text-white hover:text-gray-300 transition-colors font-medium border-b-2 border-purple-500 pb-1" style={{color: 'white', textDecoration: 'none'}}>
              Home
            </Link>
            <Link to="/about" className="text-white hover:text-gray-300 transition-colors font-medium" style={{color: 'white', textDecoration: 'none'}}>
              About us
            </Link>
            <Link to="/library" className="text-white hover:text-gray-300 transition-colors font-medium" style={{color: 'white', textDecoration: 'none'}}>
              Asset Library
            </Link>
            <Link to="/insights" className="text-white hover:text-gray-300 transition-colors font-medium" style={{color: 'white', textDecoration: 'none'}}>
              Insight&Trends
            </Link>
            <Link to="/lab" className="text-white hover:text-gray-300 transition-colors font-medium" style={{color: 'white', textDecoration: 'none'}}>
              Prototype Lab
            </Link>
          </nav>

          {/* Action Buttons - Right */}
          <div className="flex items-center space-x-4">
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
            <button className="text-white p-2 hover:bg-gray-700 rounded-lg transition-colors">
              <div className="flex flex-col space-y-1">
                <div className="w-1 h-1 bg-white rounded-full"></div>
                <div className="w-1 h-1 bg-white rounded-full"></div>
                <div className="w-1 h-1 bg-white rounded-full"></div>
              </div>
            </button>
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

import React from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';

function AssetLibrary() {
  return (
    <div className="min-h-screen" style={{backgroundColor: '#353745'}}>
      <Header />
      
      {/* Hero Section */}
      <section className="relative py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          {/* Background Glow Effect */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-96 h-96 rounded-full" style={{
              background: 'radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, rgba(16, 185, 129, 0.2) 50%, transparent 100%)',
              filter: 'blur(60px)'
            }}></div>
          </div>
          
          {/* Content */}
          <div className="relative z-10">
            <h1 className="text-6xl font-bold text-white mb-6">Asset Library</h1>
            <p className="text-gray-300 text-xl mb-8">
              A starting point of inspiration that sparks a designer's imagination.
            </p>
            <div className="text-gray-400 space-y-2 mb-8">
              <p>디자인 리소스를 한눈에 모아보고 조합하세요.</p>
              <p>자동차 디자인에 필요한 이미지, 컬러 팔레트, 파츠 요소 등을 태그 기반으로 쉽게 탐색할 수 있습니다.</p>
            </div>
            
            {/* Search Bar */}
            <div className="flex max-w-md mx-auto">
              <input
                type="text"
                placeholder="검색어를 입력해주세요"
                className="flex-1 px-4 py-3 bg-gray-700 border border-gray-600 rounded-l-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
              />
              <button className="px-6 py-3 bg-blue-600 text-white rounded-r-lg hover:bg-blue-700 transition-colors">
                Search
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            
            {/* UX Design Process Card */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-white text-xl font-semibold mb-4">UX design process</h3>
              <div className="bg-gray-700 rounded-lg p-4 mb-4">
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-white text-sm font-bold">01</div>
                    <span className="text-white text-sm">Problem/Product Definition</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white text-sm font-bold">02</div>
                    <span className="text-white text-sm">Roadmap to get started</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center text-white text-sm font-bold">03</div>
                    <span className="text-white text-sm">Research</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center text-white text-sm font-bold">04</div>
                    <span className="text-white text-sm">Analyze</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-white text-sm font-bold">05</div>
                    <span className="text-white text-sm">Design</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white text-sm font-bold">06</div>
                    <span className="text-white text-sm">Validation</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center text-white text-sm font-bold">07</div>
                    <span className="text-white text-sm">Handover</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Preserve Hyundai's Brand Identity Card */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-white text-xl font-semibold mb-2">Preserve Hyundai's Brand Identity</h3>
              <p className="text-gray-400 text-sm mb-4">2025-07-24 04:11</p>
              <div className="bg-blue-900 rounded-lg p-4 flex items-center justify-center">
                <span className="text-white text-2xl font-bold">HYUNDAI</span>
              </div>
            </div>

            {/* User-Centered Design Support Card */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-white text-xl font-semibold mb-2">User-Centered Design Support</h3>
              <p className="text-gray-400 text-sm mb-4">2025-07-24 04:11</p>
              <div className="bg-gray-700 rounded-lg p-4 mb-4">
                <div className="w-full h-32 bg-gradient-to-r from-gray-600 to-gray-500 rounded flex items-center justify-center">
                  <span className="text-gray-400">🚗 Car Design Sketches</span>
                </div>
              </div>
              <p className="text-white text-sm">How to sketch the car design</p>
            </div>

            {/* Market-Driven Design Analysis Card */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-white text-xl font-semibold mb-2">Market-Driven Design Analysis</h3>
              <p className="text-gray-400 text-sm mb-4">2025-07-24 04:11</p>
              <div className="bg-gray-700 rounded-lg p-4">
                <h4 className="text-white font-semibold mb-3">Why you should do market analysis in business plan?</h4>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-green-400">📊</span>
                    <span className="text-white text-sm">Know Market Trend</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-blue-400">🛡️</span>
                    <span className="text-white text-sm">Reduce Risk</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-yellow-400">💰</span>
                    <span className="text-white text-sm">Project Revenues</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-red-400">🎯</span>
                    <span className="text-white text-sm">Pinpoint Customer Base</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-purple-400">📈</span>
                    <span className="text-white text-sm">Set Growth Benchmarks</span>
                  </div>
                </div>
                <div className="mt-3 text-xs text-gray-400">
                  <p>Fortam Themes</p>
                  <p>Market Segmentation and Analysis</p>
                </div>
              </div>
            </div>
          </div>

          {/* Pagination */}
          <div className="flex justify-center items-center space-x-4 mt-12">
            <button className="text-gray-400 hover:text-white transition-colors">← Previous</button>
            <div className="flex space-x-2">
              <button className="w-8 h-8 bg-blue-600 text-white rounded">1</button>
              <button className="w-8 h-8 bg-gray-700 text-white rounded hover:bg-gray-600">2</button>
              <button className="w-8 h-8 bg-gray-700 text-white rounded hover:bg-gray-600">3</button>
              <span className="text-gray-400">...</span>
              <button className="w-8 h-8 bg-gray-700 text-white rounded hover:bg-gray-600">14</button>
              <button className="w-8 h-8 bg-gray-700 text-white rounded hover:bg-gray-600">15</button>
            </div>
            <button className="text-gray-400 hover:text-white transition-colors">Next →</button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}

export default AssetLibrary; 
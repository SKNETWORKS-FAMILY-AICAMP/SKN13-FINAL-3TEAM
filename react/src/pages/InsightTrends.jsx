import React from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';

function InsightTrends() {
  return (
    <div className="min-h-screen" style={{backgroundColor: '#353745'}}>
      <Header />
      
      {/* Hero Section */}
      <section className="relative py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          {/* Background Glow Effect */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-96 h-96 rounded-full" style={{
              background: 'radial-gradient(circle, rgba(139, 92, 246, 0.4) 0%, rgba(16, 185, 129, 0.2) 50%, transparent 100%)',
              filter: 'blur(60px)'
            }}></div>
          </div>
          
          {/* Content */}
          <div className="relative z-10">
            <h1 className="text-6xl font-bold text-white mb-6">Insight & Trends</h1>
            <p className="text-gray-300 text-xl mb-8">
              Design with data, not just intuition.
            </p>
            <div className="text-gray-400 space-y-2">
              <p>시장과 사용자의 데이터를 분석해 인사이트를 도출합니다.</p>
              <p>차종별 리뷰, 트렌드 키워드, 감성 분석 데이터를 시각화하여 현재 소비자가 원하는 디자인 방향을 제시합니다.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Dashboard Widgets */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Revenue Widget */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-white text-xl font-semibold">Revenue</h3>
                <button className="text-blue-400 text-sm hover:text-blue-300">View Report</button>
              </div>
              <p className="text-gray-400 text-sm mb-4">Data from 1-12 Apr, 2024</p>
              <div className="bg-gray-700 rounded-lg p-4 h-32">
                <div className="flex items-end justify-between h-full">
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((i) => (
                    <div key={i} className="flex flex-col items-center">
                      <div className="w-3 bg-green-500 rounded-t" style={{height: `${Math.random() * 30 + 10}px`}}></div>
                      <div className="w-3 bg-purple-500 rounded-t mt-1" style={{height: `${Math.random() * 25 + 8}px`}}></div>
                    </div>
                  ))}
                </div>
                <div className="flex justify-center space-x-4 mt-2 text-xs text-gray-400">
                  <div className="flex items-center space-x-1">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span>Income</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                    <span>Expense</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Daily Expenses Widget */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-white text-xl font-semibold">Daily Expenses</h3>
                <button className="text-blue-400 text-sm hover:text-blue-300">View Report</button>
              </div>
              <p className="text-gray-400 text-sm mb-4">Data from 1-12 Apr, 2024</p>
              <div className="bg-gray-700 rounded-lg p-4 h-32">
                <div className="flex items-end justify-between h-full">
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((i) => (
                    <div key={i} className="w-4 bg-purple-500 rounded" style={{height: `${Math.random() * 40 + 20}px`}}></div>
                  ))}
                </div>
                <div className="flex justify-center space-x-4 mt-2 text-xs text-gray-400">
                  <div className="flex items-center space-x-1">
                    <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                    <span>Expenses</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
                    <span>Compare to last month</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Summary Widget */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-white text-xl font-semibold">Summary</h3>
                <button className="text-blue-400 text-sm hover:text-blue-300">View Report</button>
              </div>
              <p className="text-gray-400 text-sm mb-4">Data from 1-12 Apr, 2024</p>
              <div className="bg-gray-700 rounded-lg p-4">
                <div className="text-center mb-4">
                  <div className="text-3xl font-bold text-white">$8,295</div>
                  <div className="flex items-center justify-center text-green-400 text-sm">
                    <span>↓</span>
                    <span className="ml-1">2.1%</span>
                  </div>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                      <span className="text-white">Food & Drink</span>
                    </div>
                    <span className="text-white">48%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-purple-400 rounded-full"></div>
                      <span className="text-white">Grocery</span>
                    </div>
                    <span className="text-white">32%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-red-400 rounded-full"></div>
                      <span className="text-white">Shopping</span>
                    </div>
                    <span className="text-white">13%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-orange-400 rounded-full"></div>
                      <span className="text-white">Transport</span>
                    </div>
                    <span className="text-white">7%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Car Visualization Section */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            
            {/* 3D Car Model */}
            <div>
              <div className="flex space-x-4 mb-4">
                <button className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm">3D view</button>
                <button className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg text-sm">Scheme view</button>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-8 border border-gray-700">
                <div className="relative h-64 bg-gradient-to-br from-gray-700 to-gray-800 rounded-lg flex items-center justify-center">
                  {/* 3D Car Model */}
                  <div className="relative w-48 h-24 bg-white rounded-lg transform rotate-12">
                    <div className="absolute -top-2 -left-2 w-4 h-4 bg-yellow-300 rounded-full opacity-80"></div>
                    <div className="absolute -top-1 left-8 w-3 h-3 bg-yellow-300 rounded-full opacity-80"></div>
                    <div className="absolute -bottom-1 right-4 w-2 h-2 bg-yellow-300 rounded-full opacity-80"></div>
                    <div className="absolute top-1/2 left-2 w-2 h-2 bg-black rounded-full"></div>
                    <div className="absolute top-1/2 right-2 w-2 h-2 bg-black rounded-full"></div>
                  </div>
                </div>
                
                {/* Rotation Control */}
                <div className="mt-4 flex items-center justify-between">
                  <button className="text-gray-400 hover:text-white">←</button>
                  <div className="flex space-x-1">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((i) => (
                      <div key={i} className="w-1 h-4 bg-gray-600 rounded"></div>
                    ))}
                  </div>
                  <button className="text-gray-400 hover:text-white">→</button>
                </div>
                
                <p className="text-gray-400 text-sm mt-2">Parts overview</p>
              </div>
            </div>

            {/* Car Information */}
            <div>
              <h3 className="text-white text-xl font-semibold mb-6">General information</h3>
              
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="text-white font-semibold">Audi A4, 2008</h4>
                    <p className="text-gray-400 text-sm">1.8L SVT (160H/P), SEDAN • 120,500 MILES DRIVEN • GASOLINE</p>
                  </div>
                  <div className="bg-gray-700 px-3 py-1 rounded text-white text-sm">NM-2546</div>
                </div>
                
                <div className="flex space-x-2 mb-4">
                  <button className="px-3 py-2 bg-gray-700 text-gray-300 rounded text-sm">Driver information</button>
                  <button className="px-3 py-2 bg-blue-600 text-white rounded text-sm">Car details</button>
                  <button className="px-3 py-2 bg-gray-700 text-gray-300 rounded text-sm">Accident details</button>
                  <button className="px-3 py-2 bg-gray-700 text-gray-300 rounded text-sm">Accident history</button>
                </div>
                
                <div className="flex justify-between items-center">
                  <div>
                    <h5 className="text-white font-semibold mb-2">Uploaded photos (15)</h5>
                  </div>
                  <button className="text-blue-400 text-sm hover:text-blue-300">View all &gt;</button>
                </div>
                
                <div className="grid grid-cols-6 gap-2 mt-2">
                  {[1, 2, 3, 4, 5, 6].map((i) => (
                    <div key={i} className="w-12 h-8 bg-gray-600 rounded"></div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      <Footer />
    </div>
  );
}

export default InsightTrends; 
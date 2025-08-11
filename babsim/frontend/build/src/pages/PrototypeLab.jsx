import React from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';

function PrototypeLab() {
  return (
    <div className="min-h-screen" style={{backgroundColor: '#353745'}}>
      <Header />
      
      <div className="flex">
        {/* Left Sidebar */}
        <div className="w-80 bg-gray-800 min-h-screen p-6 border-r border-gray-700">
          <h2 className="text-white text-xl font-semibold mb-6">내 대화</h2>
          
          <button className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg mb-6 flex items-center justify-center space-x-2 hover:bg-blue-700 transition-colors">
            <span>+</span>
            <span>새로운 대화</span>
          </button>
          
          <div className="space-y-4">
            <div className="bg-gray-700 rounded-lg p-4">
              <h3 className="text-white text-sm font-medium mb-2">현대자동차 아이오닉6 이미지...</h3>
              <p className="text-gray-400 text-xs">2025-07-22</p>
            </div>
            
            <div className="bg-gray-700 rounded-lg p-4">
              <h3 className="text-white text-sm font-medium mb-2">현대자동차의 아이오닉6에 대...</h3>
              <p className="text-gray-400 text-xs">2025-07-22</p>
            </div>
            
            <div className="bg-gray-700 rounded-lg p-4">
              <h3 className="text-white text-sm font-medium mb-2">현대자동차에 대해 설명해줘</h3>
              <p className="text-gray-400 text-xs">2025-07-22</p>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1">
          <div className="max-w-6xl mx-auto px-8 py-12">
            {/* Hero Section */}
            <div className="text-center mb-16">
              <h1 className="text-6xl font-bold text-white mb-6">Prototype Lab</h1>
              <p className="text-gray-300 text-xl mb-8">
                Turn your ideas into images — with just one prompt.
              </p>
              <p className="text-gray-400 max-w-3xl mx-auto">
                다양한 조건을 프롬프트로 입력하면, AI가 text-to-image 및 image-to-image 기술로 다채로운 시각적 프로토타입을 생성해줍니다.
              </p>
            </div>

            {/* Feature Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
              
              {/* 2D Prototype Card */}
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 text-center">
                <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white text-2xl">🎨</span>
                </div>
                <h3 className="text-white text-lg font-semibold mb-4">
                  당신의 아이디어를 2D 프로토타입으로 만들어보세요.
                </h3>
                <button className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors">
                  시작하기
                </button>
              </div>

              {/* Image Modification Card */}
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 text-center">
                <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white text-2xl">✏️</span>
                </div>
                <h3 className="text-white text-lg font-semibold mb-4">
                  프로토타입 이미지의 원하는 부분을 지워서 수정해보세요.
                </h3>
                <button className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors">
                  시작하기
                </button>
              </div>

              {/* 3D Modeling Card */}
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 text-center">
                <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white text-2xl">🔲</span>
                </div>
                <h3 className="text-white text-lg font-semibold mb-4">
                  최종 아이디어 이미지를 3D 모델링으로 만들어보세요.
                </h3>
                <button className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors">
                  시작하기
                </button>
              </div>
            </div>

            {/* Chat Input */}
            <div className="max-w-4xl mx-auto">
              <div className="relative">
                <input
                  type="text"
                  placeholder="무엇이든 물어보세요"
                  className="w-full px-6 py-4 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 pr-12"
                />
                <button className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white">
                  ↑
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}

export default PrototypeLab; 
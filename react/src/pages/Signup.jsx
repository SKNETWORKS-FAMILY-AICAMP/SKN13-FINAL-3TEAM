import React from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';

function Signup() {
  return (
    <div className="min-h-screen" style={{backgroundColor: '#353745'}}>
      <Header />
      
      {/* Main Content */}
      <div className="flex items-center justify-center min-h-screen py-12">
        <div className="max-w-4xl mx-auto px-4">
          {/* Title */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-white mb-4">Create your account</h1>
            <p className="text-gray-400">
              Already have an account?{' '}
              <Link to="/login" className="text-blue-400 hover:text-blue-300 transition-colors">
                Sign in
              </Link>
            </p>
          </div>

          {/* Signup Form Container */}
          <div className="bg-gray-800 rounded-lg p-8 border border-gray-700">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Left Side - Email/Password Signup */}
              <div>
                <h2 className="text-white text-xl font-semibold mb-6">Sign up with Email</h2>
                
                <form className="space-y-6">
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">
                      Name
                    </label>
                    <input
                      type="text"
                      placeholder="이름을 입력해주세요"
                      className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">
                      Email
                    </label>
                    <input
                      type="email"
                      placeholder="이메일을 입력해주세요"
                      className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">
                      비밀번호
                    </label>
                    <input
                      type="password"
                      placeholder="비밀번호를 입력해주세요"
                      className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                    />
                    <p className="text-gray-400 text-xs mt-1">
                      영문자, 기호(!,&,*,_,^)를 포함하여 8글자 이상을 입력해주세요.
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">
                      비밀번호 확인
                    </label>
                    <input
                      type="password"
                      placeholder="비밀번호를 다시 한번 입력해주세요"
                      className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                    />
                    <p className="text-gray-400 text-xs mt-1">
                      영문자, 기호(!,&,*,_,^)를 포함하여 8글자 이상을 입력해주세요.
                    </p>
                  </div>
                  
                  <button
                    type="submit"
                    className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                  >
                    Sign up
                  </button>
                </form>
              </div>

              {/* Right Side - Social Signup */}
              <div>
                <h2 className="text-white text-xl font-semibold mb-6">Social Signup</h2>
                
                <div className="space-y-4">
                  <button className="w-full bg-white text-gray-900 py-3 px-6 rounded-lg font-semibold hover:bg-gray-100 transition-colors flex items-center justify-center space-x-3">
                    <span>🔍</span>
                    <span>Sign up with Google</span>
                  </button>
                  
                  <button className="w-full bg-green-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-green-700 transition-colors flex items-center justify-center space-x-3">
                    <span>N</span>
                    <span>Sign up with Naver</span>
                  </button>
                  
                  <button className="w-full bg-yellow-400 text-gray-900 py-3 px-6 rounded-lg font-semibold hover:bg-yellow-500 transition-colors flex items-center justify-center space-x-3">
                    <span>💬</span>
                    <span>Sign up with Kakao</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}

export default Signup; 
import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

function MyWorkspace() {
  const { user } = useAuth();
  const navigate = useNavigate();

  if (!user) {
    navigate('/login');
    return null;
  }

  return (
    <div className="min-h-screen" style={{backgroundColor: '#353745'}}>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">내 작업 공간</h1>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* 최근 채팅 세션 */}
            <div className="bg-blue-50 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-blue-900 mb-4">최근 채팅</h2>
              <p className="text-blue-700 mb-4">AI와의 대화 기록을 확인하세요</p>
              <button 
                onClick={() => navigate('/chatbot')}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                채팅 시작
              </button>
            </div>

            {/* 인사이트 & 트렌드 */}
            <div className="bg-green-50 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-green-900 mb-4">인사이트 & 트렌드</h2>
              <p className="text-green-700 mb-4">자동차 디자인 트렌드와 인사이트를 확인하세요</p>
              <button 
                onClick={() => navigate('/insights')}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
              >
                트렌드 보기
              </button>
            </div>

            {/* 에셋 라이브러리 */}
            <div className="bg-purple-50 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-purple-900 mb-4">에셋 라이브러리</h2>
              <p className="text-purple-700 mb-4">디자인 에셋과 자료를 관리하세요</p>
              <button 
                onClick={() => navigate('/library')}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
              >
                라이브러리 보기
              </button>
            </div>

            {/* 프로토타입 랩 */}
            <div className="bg-orange-50 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-orange-900 mb-4">프로토타입 랩</h2>
              <p className="text-orange-700 mb-4">새로운 아이디어를 실험해보세요</p>
              <button 
                onClick={() => navigate('/lab')}
                className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors"
              >
                랩 시작
              </button>
            </div>

            {/* 프로필 설정 */}
            <div className="bg-gray-50 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">프로필 설정</h2>
              <p className="text-gray-700 mb-4">개인 정보를 관리하세요</p>
              <button 
                onClick={() => navigate('/profile')}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
              >
                프로필 수정
              </button>
            </div>

            {/* 통계 */}
            <div className="bg-indigo-50 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-indigo-900 mb-4">활동 통계</h2>
              <div className="space-y-2 text-indigo-700">
                <p>총 채팅 세션: 12</p>
                <p>저장된 에셋: 8</p>
                <p>생성된 프로토타입: 3</p>
              </div>
            </div>
          </div>

          {/* 사용자 정보 요약 */}
          <div className="mt-8 bg-gray-50 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">사용자 정보</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">이름</p>
                <p className="font-medium">{user.user_name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">이메일</p>
                <p className="font-medium">{user.e_mail}</p>
              </div>
              {user.company && (
                <div>
                  <p className="text-sm text-gray-600">회사</p>
                  <p className="font-medium">{user.company}</p>
                </div>
              )}
              {user.department && (
                <div>
                  <p className="text-sm text-gray-600">부서</p>
                  <p className="font-medium">{user.department}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MyWorkspace;

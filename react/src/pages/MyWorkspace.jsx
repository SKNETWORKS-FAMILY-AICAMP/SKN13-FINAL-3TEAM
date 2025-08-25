import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import { useAuth } from '../contexts/AuthContext';
import { updateUserProfile, uploadProfileImage } from '../services/authService';
import ioniq6Image from '../assets/profile/Ionic6.png';

function MyWorkspace() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [backgroundImage, setBackgroundImage] = useState(ioniq6Image);
  const [profileImage, setProfileImage] = useState('');
  const [imageLoading, setImageLoading] = useState(false);
  const [message, setMessage] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (user) {
      setProfileImage(user.profile_image || '');
      if (user.background_image) {
        setBackgroundImage(user.background_image);
      }
    }
  }, [user]);

  const handleImageClick = () => {
    fileInputRef.current?.click();
  };

  const handleImageChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // 파일 크기 검증 (5MB 이하)
    if (file.size > 5 * 1024 * 1024) {
      setMessage('이미지 파일 크기는 5MB 이하여야 합니다.');
      return;
    }

    // 파일 타입 검증
    if (!file.type.startsWith('image/')) {
      setMessage('이미지 파일만 업로드 가능합니다.');
      return;
    }

    setImageLoading(true);
    setMessage('');

    try {
      // 1단계: 프로필 이미지 업로드 (MOCKDATA 모드: 로컬 저장, 실제 모드: S3 업로드)
      const uploadResult = await uploadProfileImage(file);
      
      if (!uploadResult.success) {
        setMessage(uploadResult.error || '이미지 업로드에 실패했습니다.');
        setImageLoading(false);
        return;
      }

      // 2단계: 업로드된 이미지 URL을 사용자 정보에 저장
      const result = await updateUserProfile({
        profile_image: uploadResult.image_url,
      });
      
      if (result.success) {
        setProfileImage(uploadResult.image_url);
        setMessage(uploadResult.message);
        
        // AuthContext의 사용자 정보도 업데이트
        if (user) {
          const updatedUser = { ...user, profile_image: uploadResult.image_url };
          login(updatedUser);
        }
      } else {
        setMessage(result.error || '프로필 정보 업데이트에 실패했습니다.');
      }
      setImageLoading(false);
    } catch (error) {
      console.error('이미지 업로드 오류:', error);
      setMessage('이미지 업로드 중 오류가 발생했습니다.');
      setImageLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative" style={{backgroundColor: '#353745'}}>
      {/* Background Image */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-20 pointer-events-none mt-0"
        style={{
          backgroundImage: `url(${backgroundImage})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat'
        }}
      />
      
      <div className="relative z-50">
        <Header />
      </div>
      
      <div className="flex min-h-screen pt-20 relative z-10">
        {/* Left Sidebar */}
        <div className="w-80 bg-gray-900/90 backdrop-blur-sm text-white p-6">
          {/* Profile Image Section */}
          <div className="text-center mb-8">
            <div 
              className="w-32 h-32 mx-auto mb-4 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center cursor-pointer hover:opacity-80 transition-opacity relative overflow-hidden"
              onClick={handleImageClick}
            >
              {profileImage || user?.profile_image ? (
                <img 
                  src={profileImage || user?.profile_image} 
                  alt="프로필 이미지" 
                  className="w-full h-full object-cover rounded-full"
                />
              ) : (
                <svg className="w-16 h-16 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              )}
              
              {/* Image Change Overlay */}
              <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity duration-200 rounded-full cursor-pointer">
                <div className="text-center">
                  <svg className="w-8 h-8 text-white mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <span className="text-white text-sm font-medium">이미지 변경</span>
                </div>
              </div>

              {/* Loading Spinner */}
              {imageLoading && (
                <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded-full">
                  <svg className="animate-spin w-8 h-8 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
              )}
            </div>
            
            {/* Hidden File Input */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              className="hidden"
            />
            
            <h2 className="text-xl font-bold text-white">{user?.user_name || '사용자'}</h2>
            <p className="text-gray-400 text-sm">{user?.position || '직책'}</p>
            <p className="text-gray-500 text-xs mt-2">이미지를 클릭하여 변경</p>
          </div>

          {/* Navigation Menu */}
          <nav className="space-y-2">
            <button 
              onClick={() => navigate('/profile')}
              className="w-full text-left p-3 rounded-lg hover:bg-gray-800 transition-colors duration-200"
            >
              <div className="flex items-center space-x-3">
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span className="text-gray-300">Profile</span>
              </div>
            </button>
            
            <div className="bg-blue-600 rounded-lg p-3">
              <div className="flex items-center space-x-3">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <span className="font-medium text-white">MyWorkspace</span>
              </div>
            </div>
          </nav>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 p-8">
          <div className="max-w-6xl mx-auto">
            {/* Page Header */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-white mb-2">My Workspace</h1>
              <p className="text-gray-300">내 작업 공간과 활동 내역을 확인하세요</p>
            </div>

            {/* Message Display */}
            {message && (
              <div className={`mb-6 p-4 rounded-xl border-l-4 ${
                message.includes('성공') || message.includes('업데이트') || message.includes('저장')
                  ? 'bg-green-900/50 text-green-300 border-green-400' 
                  : 'bg-red-900/50 text-red-300 border-red-400'
              }`}>
                <div className="flex items-center">
                  <svg className={`w-5 h-5 mr-2 ${
                    message.includes('성공') || message.includes('업데이트') || message.includes('저장') ? 'text-green-400' : 'text-red-400'
                  }`} fill="currentColor" viewBox="0 0 20 20">
                    {message.includes('성공') || message.includes('업데이트') || message.includes('저장') ? (
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    ) : (
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    )}
                  </svg>
                  {message}
                </div>
              </div>
            )}

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8" style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem'}}>
              
              {/* 1. 자신의 Asset */}
              <div className="bg-gray-700/30 rounded-xl p-6 border border-gray-600">
                <h3 className="text-lg font-semibold text-white border-b border-gray-600 pb-2 mb-6">
                  🗂️ 내가 올린 Asset
                </h3>
                <div className="space-y-4">
                  <div className="bg-gray-600/30 rounded-lg p-4">
                    <p className="text-gray-300 text-sm mb-3">현재 업로드된 Asset이 없습니다.</p>
                    <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                      + 새 Asset 업로드
                    </button>
                  </div>
                  <div className="text-gray-400 text-xs">
                    * PDF, 이미지, 3D 모델 등을 업로드할 수 있습니다
                  </div>
                </div>
              </div>

              {/* 2. Asset 모아보기 (관심표시한 Asset) */}
              <div className="bg-gray-700/30 rounded-xl p-6 border border-gray-600">
                <h3 className="text-lg font-semibold text-white border-b border-gray-600 pb-2 mb-6">
                  ❤️ 관심표시한 Asset
                </h3>
                <div className="space-y-4">
                  <div className="bg-gray-600/30 rounded-lg p-4">
                    <p className="text-gray-300 text-sm mb-3">하트나 댓글을 남긴 Asset이 없습니다.</p>
                  </div>
                  
                  {/* 카테고리별 원그래프 분석 */}
                  <div className="bg-gray-600/30 rounded-lg p-4">
                    <h4 className="text-white text-sm font-medium mb-3">카테고리별 분석</h4>
                    <div className="flex items-center justify-center h-32">
                      <div className="text-gray-400 text-sm">원그래프가 여기에 표시됩니다</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 3. Lab의 보관된 대화 */}
              <div className="bg-gray-700/30 rounded-xl p-6 border border-gray-600">
                <h3 className="text-lg font-semibold text-white border-b border-gray-600 pb-2 mb-6">
                  💬 보관된 대화
                </h3>
                <div className="space-y-4">
                  <div className="bg-gray-600/30 rounded-lg p-4">
                    <p className="text-gray-300 text-sm mb-3">보관된 대화가 없습니다.</p>
                  </div>
                  <div className="text-gray-400 text-xs">
                    * Prototype Lab에서 생성된 대화들이 여기에 저장됩니다
                  </div>
                </div>
              </div>

              {/* 4. 보관된 이미지, 3D, 4D */}
              <div className="bg-gray-700/30 rounded-xl p-6 border border-gray-600">
                <h3 className="text-lg font-semibold text-white border-b border-gray-600 pb-2 mb-6">
                  🎨 보관된 생성물
                </h3>
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-gray-600/30 rounded-lg p-3 text-center">
                      <div className="text-2xl mb-2">🖼️</div>
                      <p className="text-gray-300 text-xs">이미지</p>
                      <p className="text-gray-400 text-xs">0개</p>
                    </div>
                    <div className="bg-gray-600/30 rounded-lg p-3 text-center">
                      <div className="text-2xl mb-2">🎲</div>
                      <p className="text-gray-300 text-xs">3D 모델</p>
                      <p className="text-gray-400 text-xs">0개</p>
                    </div>
                    <div className="bg-gray-600/30 rounded-lg p-3 text-center">
                      <div className="text-2xl mb-2">🎬</div>
                      <p className="text-gray-300 text-xs">4D 시뮬레이션</p>
                      <p className="text-gray-400 text-xs">0개</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* 5. 활동 세션 (월, 일별 통계) */}
              <div className="bg-gray-700/30 rounded-xl p-6 border border-gray-600">
                <h3 className="text-lg font-semibold text-white border-b border-gray-600 pb-2 mb-6">
                  📊 활동 세션 통계
                </h3>
                <div className="space-y-4">
                  <div className="bg-gray-600/30 rounded-lg p-4">
                    <h4 className="text-white text-sm font-medium mb-3">이번 달 활동</h4>
                    <div className="grid grid-cols-2 gap-4 text-center">
                      <div>
                        <p className="text-2xl font-bold text-blue-400">0</p>
                        <p className="text-gray-400 text-xs">대화 세션</p>
                      </div>
                      <div>
                        <p className="text-2xl font-bold text-green-400">0</p>
                        <p className="text-gray-400 text-xs">생성된 결과물</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-600/30 rounded-lg p-4">
                    <h4 className="text-white text-sm font-medium mb-3">일별 활동 그래프</h4>
                    <div className="flex items-center justify-center h-20">
                      <div className="text-gray-400 text-sm">일별 활동 그래프가 여기에 표시됩니다</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 6. 추가 기능을 위한 빈 칸 */}
              <div className="bg-gray-700/30 rounded-xl p-6 border border-gray-600">
                <h3 className="text-lg font-semibold text-white border-b border-gray-600 pb-2 mb-6">
                  🔮 향후 기능
                </h3>
                <div className="space-y-4">
                  <div className="bg-gray-600/30 rounded-lg p-4">
                    <p className="text-gray-300 text-sm">추가 기능을 위한 공간입니다.</p>
                  </div>
                </div>
              </div>
            </div>

          {/* Background Image Section - 아래로 이동 */}
          <div className="mt-8 space-y-4">
            <h3 className="text-lg font-semibold text-white border-b border-gray-600 pb-2">
              배경 이미지 설정
            </h3>
            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                <div className="w-24 h-16 rounded-lg overflow-hidden border-2 border-gray-600">
                  <img 
                    src={backgroundImage} 
                    alt="현재 배경 이미지" 
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="flex-1">
                  <p className="text-gray-300 text-sm mb-2">현재 배경 이미지</p>
                  <p className="text-gray-400 text-xs">현재는 MOCKDATA로 IONIQ 5 이미지를 사용합니다</p>
                </div>
              </div>
              <div className="text-gray-400 text-xs">
                * 향후 사용자가 보유한 세션의 이미지들 중에서 선택할 수 있도록 구현 예정
              </div>
            </div>
          </div>

          </div>
        </div>
      </div>
    </div>
  );
}

export default MyWorkspace;

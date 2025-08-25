import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { updateUserProfile, uploadProfileImage } from '../services/authService';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import ioniq6Image from '../assets/profile/Ionic6.png';

function Profile() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [formData, setFormData] = useState({
    user_name: '',
    e_mail: '',
    phone_number: '',
    company: '',
    department: '',
    position: '',
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [profileImage, setProfileImage] = useState('');
  const [imageLoading, setImageLoading] = useState(false);
  const [backgroundImage, setBackgroundImage] = useState(ioniq6Image);

  useEffect(() => {
    if (user) {
      setFormData({
        user_name: user.user_name || '',
        e_mail: user.e_mail || '',
        phone_number: user.phone_number || '',
        company: user.company || '',
        department: user.department || '',
        position: user.position || '',
      });
      setProfileImage(user.profile_image || '');
      // 사용자가 설정한 배경 이미지가 있으면 사용, 없으면 기본값
      setBackgroundImage(user.background_image || ioniq6Image);
    }
  }, [user]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

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
        ...formData,
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
      setMessage('이미지 업로드 중 오류가 발생했습니다.');
      setImageLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const result = await updateUserProfile({
        ...formData,
        profile_image: profileImage,
        background_image: backgroundImage,
      });
      
      if (result.success) {
        setMessage('사용자 정보가 성공적으로 업데이트되었습니다.');
        // AuthContext의 사용자 정보도 업데이트
        login(result.user);
      } else {
        setMessage(result.error || '사용자 정보 수정에 실패했습니다.');
      }
    } catch (error) {
      setMessage('오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    navigate('/login');
    return null;
  }

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
              {profileImage ? (
                <img 
                  src={profileImage} 
                  alt="프로필 이미지" 
                  className="w-full h-full object-cover rounded-full"
                />
              ) : (
                <svg className="w-16 h-16 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              )}
              
              {/* Image Upload Overlay */}
              <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                <div className="text-center">
                  <svg className="w-8 h-8 text-white mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <span className="text-white text-sm font-medium">이미지 변경</span>
                </div>
              </div>

              {/* Loading Spinner */}
              {imageLoading && (
                <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
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
            
            <h2 className="text-xl font-bold text-white">{user.user_name || '사용자'}</h2>
            <p className="text-gray-400 text-sm">{user.position || '직책'}</p>
            <p className="text-gray-500 text-xs mt-2">이미지를 클릭하여 변경</p>
          </div>

          {/* Navigation Menu */}
          <nav className="space-y-2">
            <div className="bg-blue-600 rounded-lg p-3">
              <div className="flex items-center space-x-3">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span className="font-medium text-white">Profile</span>
              </div>
            </div>
            
            <button 
              onClick={() => navigate('/myworkspace')}
              className="w-full text-left p-3 rounded-lg hover:bg-gray-800 transition-colors duration-200"
            >
              <div className="flex items-center space-x-3">
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <span className="text-gray-300">MyWorkspace</span>
              </div>
            </button>
          </nav>
        </div>

        {/* Right Content Area - Full Width */}
        <div className="flex-1 p-8">
          {/* Page Header - Full Width */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">프로필 설정</h1>
            <p className="text-gray-300">개인 정보를 관리하고 업데이트하세요</p>
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

          {/* Profile Form - Dark Theme */}
          <div className="bg-gray-800/30 backdrop-blur-sm rounded-2xl border border-gray-700 shadow-xl p-8">
            {/* Form Header */}
            <div className="mb-8 pb-6 border-b border-gray-600">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white">사용자 정보</h2>
                  <p className="text-gray-300">프로필 정보를 확인하고 수정하세요</p>
                </div>
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-8">
              {/* Personal & Professional Information Section - 2 Columns */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8" style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem'}}>
                {/* Left Column - Personal Information */}
                <div className="bg-gray-700/30 rounded-xl p-6 border border-gray-600">
                  <h3 className="text-lg font-semibold text-white border-b border-gray-600 pb-2 mb-6">
                    개인 정보
                  </h3>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-gray-300">
                        이름 <span className="text-red-400">*</span>
                      </label>
                      <input
                        type="text"
                        name="user_name"
                        value={formData.user_name}
                        onChange={handleInputChange}
                        required
                        className="w-full px-4 py-3 bg-gray-700 border border-gray-600 text-white rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:border-gray-500"
                        placeholder="이름을 입력하세요"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-gray-300">
                        이메일 <span className="text-red-400">*</span>
                      </label>
                      <input
                        type="email"
                        name="e_mail"
                        value={formData.e_mail}
                        onChange={handleInputChange}
                        required
                        className="w-full px-4 py-3 bg-gray-700 border border-gray-600 text-white rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:border-gray-500"
                        placeholder="이메일을 입력하세요"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-gray-300">
                        전화번호
                      </label>
                      <input
                        type="tel"
                        name="phone_number"
                        value={formData.phone_number}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 bg-gray-700 border border-gray-600 text-white rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:border-gray-500"
                        placeholder="전화번호를 입력하세요"
                      />
                    </div>
                  </div>
                </div>

                {/* Right Column - Professional Information */}
                <div className="bg-gray-700/30 rounded-xl p-6 border border-gray-600">
                  <h3 className="text-lg font-semibold text-white border-b border-gray-600 pb-2 mb-6">
                    직업 정보
                  </h3>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-gray-300">
                        회사
                      </label>
                      <input
                        type="text"
                        name="company"
                        value={formData.company}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 bg-gray-700 border border-gray-600 text-white rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:border-gray-500"
                        placeholder="회사명을 입력하세요"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-gray-300">
                        부서
                      </label>
                      <input
                        type="text"
                        name="department"
                        value={formData.department}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 bg-gray-700 border border-gray-600 text-white rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:border-gray-500"
                        placeholder="부서명을 입력하세요"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-gray-300">
                        직책
                      </label>
                      <input
                        type="text"
                        name="position"
                        value={formData.position}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 bg-gray-700 border border-gray-600 text-white rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:border-gray-500"
                        placeholder="직책을 입력하세요"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Background Image Section */}
              <div className="space-y-6">
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

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row justify-end space-y-3 sm:space-y-0 sm:space-x-4 pt-8 border-t border-gray-600">
                <button
                  type="button"
                  onClick={() => navigate('/')}
                  className="w-full sm:w-auto px-8 py-3 border-2 border-gray-600 text-gray-300 rounded-xl hover:bg-gray-700 hover:border-gray-500 transition-all duration-200 font-medium"
                >
                  홈으로 돌아가기
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full sm:w-auto px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 font-medium shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-lg"
                >
                  {loading ? (
                    <div className="flex items-center justify-center">
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      저장 중...
                    </div>
                  ) : (
                    '정보 저장'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Profile;

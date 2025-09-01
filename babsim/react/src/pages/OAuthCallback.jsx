import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { setToken, setRefreshToken } from '../services/authService';

function OAuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();

  useEffect(() => {
    const handleOAuthCallback = async () => {
      try {
        // URL 파라미터에서 토큰과 사용자 정보 추출
        const accessToken = searchParams.get('access_token');
        const refreshToken = searchParams.get('refresh_token');
        const userId = searchParams.get('user_id');
        const email = searchParams.get('email');

        // 디버깅을 위한 로그 추가
        console.log('OAuth Callback Parameters:', {
          accessToken: accessToken ? 'Present' : 'Missing',
          refreshToken: refreshToken ? 'Present' : 'Missing',
          userId: userId || 'Missing',
          email: email || 'Missing'
        });

        if (accessToken && refreshToken && userId && email) {
          // 토큰을 로컬 스토리지에 저장
          setToken(accessToken);
          setRefreshToken(refreshToken);

          // 사용자 정보를 인증 컨텍스트에 설정
          const userData = {
            user_id: userId,
            email: email,
            access_token: accessToken,
            refresh_token: refreshToken
          };

          // login 함수가 완료될 때까지 기다림
          // await login(userData); 
                      login({ userId, e_mail: email }); // Pass user data object to login function

          // 홈페이지로 리디렉션
          navigate('/', { replace: true });
        } else {
          console.error('OAuth 콜백에서 필요한 정보를 받지 못했습니다.');
          navigate('/login', { replace: true });
        }
      } catch (error) {
        console.error('OAuth 콜백 처리 중 오류 발생:', error);
        navigate('/login', { replace: true });
      }
    };

    handleOAuthCallback();
  }, [searchParams, navigate, login]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="text-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <h2 className="text-2xl font-bold text-white mb-2">로그인 처리 중...</h2>
        <p className="text-gray-400">잠시만 기다려주세요.</p>
      </div>
    </div>
  );
}

export default OAuthCallback; 
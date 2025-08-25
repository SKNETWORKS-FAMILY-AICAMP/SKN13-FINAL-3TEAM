import { 
  mockUsers, 
  mockLoginSuccess, 
  mockLoginError, 
  mockRegisterSuccess, 
  mockUserProfile, 
  mockLogoutSuccess,
  mockRefreshTokenSuccess,
  createMockResponse,
  getMockUsers,
  addMockUser,
  validateMockUser,
  checkEmailExists
} from './mockData';

const API_BASE_URL = 'http://localhost:8000/api';

// 목업 데이터 사용 여부 (개발 중에는 true로 설정)
export const USE_MOCK_DATA = true;

// 프로필 이미지 업로드 API
export const uploadProfileImage = async (imageFile) => {
  if (USE_MOCK_DATA) {
    // MOCKDATA 모드: base64로 변환해서 localStorage에 저장
    try {
      const reader = new FileReader();
      return new Promise((resolve) => {
        reader.onload = () => {
          const base64Image = reader.result;
          const fileName = `profile_${Date.now()}_${Math.random().toString(36).substr(2, 9)}.${imageFile.name.split('.').pop()}`;
          
          // localStorage에 base64 이미지 저장
          localStorage.setItem(`profile_image_${fileName}`, base64Image);
          
          resolve({
            success: true,
            image_url: base64Image, // base64 데이터 직접 반환
            message: '프로필 이미지가 로컬에 저장되었습니다.',
          });
        };
        reader.readAsDataURL(imageFile);
      });
    } catch (error) {
      return {
        success: false,
        error: '프로필 이미지 저장 중 오류가 발생했습니다.',
      };
    }
  }

  // 실제 API 모드: /auth/profile/upload-image/ 호출
  try {
    const formData = new FormData();
    formData.append('profile_image', imageFile);

    const response = await apiRequest(`${API_BASE_URL}/auth/profile/upload-image/`, {
      method: 'POST',
      body: formData,
      headers: {
        // FormData를 사용할 때는 Content-Type을 설정하지 않음
      },
    });

    const data = await response.json();
    
    if (response.ok) {
      return {
        success: true,
        image_url: data.image_url,
        message: data.message || '프로필 이미지가 성공적으로 업로드되었습니다.',
      };
    } else {
      return {
        success: false,
        error: data.message || '프로필 이미지 업로드에 실패했습니다.',
      };
    }
  } catch (error) {
    console.error('Upload profile image error:', error);
    return {
      success: false,
      error: '프로필 이미지 업로드 중 오류가 발생했습니다.',
    };
  }
};

// 사용자 정보 수정 API
export const updateUserProfile = async (userData) => {
  if (USE_MOCK_DATA) {
    // 목업 데이터 사용
    try {
      // 현재 사용자 정보 가져오기
      const currentUser = JSON.parse(localStorage.getItem('mockUsers') || '[]').find(
        user => user.e_mail === userData.e_mail
      );
      
      if (!currentUser) {
        return {
          success: false,
          error: '사용자를 찾을 수 없습니다.',
        };
      }

      // 사용자 정보 업데이트
      const updatedUser = { ...currentUser, ...userData };
      const users = JSON.parse(localStorage.getItem('mockUsers') || '[]');
      const userIndex = users.findIndex(user => user.e_mail === userData.e_mail);
      
      if (userIndex !== -1) {
        users[userIndex] = updatedUser;
        localStorage.setItem('mockUsers', JSON.stringify(users));
        
        return {
          success: true,
          message: '사용자 정보가 성공적으로 업데이트되었습니다.',
          user: updatedUser,
        };
      } else {
        return {
          success: false,
          error: '사용자 정보 업데이트에 실패했습니다.',
        };
      }
    } catch (error) {
      return {
        success: false,
        error: '사용자 정보 업데이트 중 오류가 발생했습니다.',
      };
    }
  }

  // 실제 API 호출
  try {
    const response = await apiRequest(`${API_BASE_URL}/auth/profile/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || '사용자 정보 업데이트에 실패했습니다.');
    }

    return {
      success: true,
      message: '사용자 정보가 성공적으로 업데이트되었습니다.',
      user: data.user,
    };
  } catch (error) {
    console.error('Update user profile error:', error);
    return {
      success: false,
      error: error.message || '사용자 정보 업데이트 중 오류가 발생했습니다.',
    };
  }
};

// 로그인 API
export const login = async (email, password) => {
  if (USE_MOCK_DATA) {
    // 목업 데이터 사용
    const user = validateMockUser(email, password);
    
    if (user) {
      const mockResponse = await createMockResponse(mockLoginSuccess(user));
      const data = await mockResponse.json();
      
      // 토큰 저장
      setToken(data.access_token);
      setRefreshToken(data.refresh_token);
      
      return {
        success: true,
        message: data.message,
        user: data.user,
      };
    } else {
      const mockResponse = await createMockResponse(mockLoginError('이메일 또는 비밀번호가 올바르지 않습니다.'), 400);
      const data = await mockResponse.json();
      
      return {
        success: false,
        error: data.message,
      };
    }
  }

  // 실제 API 호출
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        e_mail: email,
        password: password,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || '로그인에 실패했습니다.');
    }

    // 토큰 저장
    setToken(data.access_token);
    setRefreshToken(data.refresh_token);

    return {
      success: true,
      message: data.message,
      user: data.user,
    };
  } catch (error) {
    console.error('Login error:', error);
    return {
      success: false,
      error: error.message || '로그인 중 오류가 발생했습니다.',
    };
  }
};

// 회원가입 API
export const register = async (userData) => {
  if (USE_MOCK_DATA) {
    // 목업 데이터 사용
    try {
      // 이메일 중복 체크
      if (checkEmailExists(userData.e_mail)) {
        return {
          success: false,
          error: '이미 존재하는 이메일입니다.',
        };
      }

      // 새 사용자 추가
      const newUser = {
        user_id: `user_${Date.now()}`,
        ...userData,
        created_at: new Date().toISOString(),
        last_login: new Date().toISOString(),
      };

      addMockUser(newUser);

      const mockResponse = await createMockResponse(mockRegisterSuccess(newUser));
      const data = await mockResponse.json();

      return {
        success: true,
        message: data.message,
        user: data.user,
      };
    } catch (error) {
      return {
        success: false,
        error: '회원가입 중 오류가 발생했습니다.',
      };
    }
  }

  // 실제 API 호출
  try {
    const response = await fetch(`${API_BASE_URL}/auth/register/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || '회원가입에 실패했습니다.');
    }

    return {
      success: true,
      message: data.message,
      user: data.user,
    };
  } catch (error) {
    console.error('Register error:', error);
    return {
      success: false,
      error: error.message || '회원가입 중 오류가 발생했습니다.',
    };
  }
};

// 로그아웃 API
export const logout = async () => {
  if (USE_MOCK_DATA) {
    // 목업 데이터 사용
    removeToken();
    const mockResponse = await createMockResponse(mockLogoutSuccess);
    const data = await mockResponse.json();
    
    return {
      success: true,
      message: data.message,
    };
  }

  // 실제 API 호출
  try {
    const response = await apiRequest(`${API_BASE_URL}/auth/logout/`, {
      method: 'POST',
    });

    if (response.ok) {
      removeToken();
      return {
        success: true,
        message: '로그아웃 성공',
      };
    } else {
      throw new Error('로그아웃에 실패했습니다.');
    }
  } catch (error) {
    console.error('Logout error:', error);
    removeToken(); // 에러가 발생해도 토큰은 제거
    return {
      success: false,
      error: error.message || '로그아웃 중 오류가 발생했습니다.',
    };
  }
};

// 유저 정보 조회 API
export const getUserProfile = async () => {
  if (USE_MOCK_DATA) {
    // 목업 데이터 사용 - 토큰에서 사용자 ID 추출
    const token = getToken();
    if (!token) {
      return {
        success: false,
        error: "토큰이 없습니다.",
      };
    }

    // 간단한 토큰 파싱 (실제로는 JWT 라이브러리 사용)
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const users = getMockUsers();
      const user = users.find(u => u.user_id === payload.user_id);
      
      if (user) {
        const mockResponse = await createMockResponse(mockUserProfile(user));
        const data = await mockResponse.json();
        
        return {
          success: true,
          user: data,
        };
      } else {
        return {
          success: false,
          error: "사용자를 찾을 수 없습니다.",
        };
      }
    } catch (error) {
      return {
        success: false,
        error: "토큰이 유효하지 않습니다.",
      };
    }
  }

  // 실제 API 호출
  try {
    const response = await fetch(`${API_BASE_URL}/auth/profile/`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || '유저 정보 조회에 실패했습니다.');
    }

    return {
      success: true,
      user: data,
    };
  } catch (error) {
    console.error('Get user profile error:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

// 인증 헤더 생성
const getAuthHeaders = () => {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

// 인증 상태 확인
export const isAuthenticated = () => {
  return !!getToken();
};

// 토큰 저장
export const setToken = (token) => {
  localStorage.setItem('access_token', token);
};

// refresh token 저장
export const setRefreshToken = (refreshToken) => {
  localStorage.setItem('refresh_token', refreshToken);
};

// 토큰 가져오기
export const getToken = () => {
  return localStorage.getItem('access_token');
};

// refresh token 가져오기
export const getRefreshToken = () => {
  return localStorage.getItem('refresh_token');
};

// 토큰 삭제
export const removeToken = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

// 토큰 갱신 API
export const refreshToken = async (refreshToken) => {
  if (USE_MOCK_DATA) {
    // 목업 데이터 사용
    const mockResponse = await createMockResponse(mockRefreshTokenSuccess());
    const data = await mockResponse.json();
    
    setToken(data.access_token);
    setRefreshToken(data.refresh_token);
    
    return {
      success: true,
      access_token: data.access_token,
      refresh_token: data.refresh_token,
    };
  }

  // 실제 API 호출
  try {
    // django 실제 토큰 갱신 주소는 /auth/token/refresh라서 수정.
    const response = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh_token: refreshToken,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || '토큰 갱신에 실패했습니다.');
    }

    setToken(data.access_token);
    setRefreshToken(data.refresh_token);
    
    return {
      success: true,
      access_token: data.access_token,
      refresh_token: data.refresh_token,
    };
  } catch (error) {
    console.error('Refresh token error:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

// 더미 데이터 사용자 목록 반환 (테스트용)
export const getMockUsersFromService = () => {
  const users = getMockUsers();
  return users.map(user => ({
    email: user.e_mail,
    password: user.password,
    name: user.user_name
  }));
};

// 더미 데이터 초기화 (테스트용)
export const resetMockData = () => {
  localStorage.removeItem('mockUsers');
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  window.location.reload();
};

// HTTP 요청 인터셉터 (토큰 자동 갱신)
export const apiRequest = async (url, options = {}) => {
  const token = getToken();
  const refreshTokenValue = getRefreshToken();
  
  // 기본 헤더 설정
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // 401 에러가 발생하고 refresh token이 있는 경우
    if (response.status === 401 && refreshTokenValue) {
      try {
        const refreshResult = await refreshToken(refreshTokenValue);
        if (refreshResult.success) {
          // 새로운 토큰으로 재시도
          const newHeaders = {
            'Content-Type': 'application/json',
            ...(refreshResult.access_token && { Authorization: `Bearer ${refreshResult.access_token}` }),
            ...options.headers,
          };

          const retryResponse = await fetch(url, {
            ...options,
            headers: newHeaders,
          });

          return retryResponse;
        } else {
          // 토큰 갱신 실패 시 로그아웃
          removeToken();
          throw new Error('토큰이 만료되었습니다. 다시 로그인해주세요.');
        }
      } catch (refreshError) {
        removeToken();
        throw new Error('토큰 갱신에 실패했습니다. 다시 로그인해주세요.');
      }
    }

    return response;
  } catch (error) {
    throw error;
  }
};

export default {
  login,
  register,
  logout,
  getUserProfile,
  updateUserProfile,
  isAuthenticated,
  refreshToken,
  getMockUsersFromService,
  resetMockData,
  apiRequest,
};

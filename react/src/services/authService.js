import { 
  mockUsers, 
  mockLoginSuccess, 
  mockLoginError, 
  mockRegisterSuccess, 
  mockUserProfile, 
  mockLogoutSuccess,
  mockRefreshTokenSuccess,
  createMockResponse,
  getMockUsers as getMockUsersFromData,
  addMockUser,
  validateMockUser,
  checkEmailExists
} from './mockData';

const API_BASE_URL = 'http://localhost:8000/api';

// 목업 데이터 사용 여부 (개발 중에는 true로 설정)
const USE_MOCK_DATA = true;

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
      const updatedUser = {
        ...currentUser,
        user_name: userData.user_name || currentUser.user_name,
        e_mail: userData.e_mail || currentUser.e_mail,
        phone_number: userData.phone_number || currentUser.phone_number,
        company: userData.company || currentUser.company,
        department: userData.department || currentUser.department,
        position: userData.position || currentUser.position,
      };

      // 로컬 스토리지 업데이트
      const users = JSON.parse(localStorage.getItem('mockUsers') || '[]');
      const updatedUsers = users.map(user => 
        user.e_mail === currentUser.e_mail ? updatedUser : user
      );
      localStorage.setItem('mockUsers', JSON.stringify(updatedUsers));

      const mockResponse = await createMockResponse({
        success: true,
        user: updatedUser,
        message: '사용자 정보가 성공적으로 업데이트되었습니다.',
      });
      
      return await mockResponse.json();
    } catch (error) {
      return {
        success: false,
        error: '사용자 정보 수정 중 오류가 발생했습니다.',
      };
    }
  }

  // 실제 API 호출
  try {
    const response = await apiRequest(`${API_BASE_URL}/auth/profile/update/`, {
      method: 'PUT',
      body: JSON.stringify(userData),
    });

    const data = await response.json();
    
    if (response.ok) {
      return {
        success: true,
        user: data.user,
        message: data.message || '사용자 정보가 성공적으로 업데이트되었습니다.',
      };
    } else {
      return {
        success: false,
        error: data.message || '사용자 정보 수정에 실패했습니다.',
      };
    }
  } catch (error) {
    console.error('Update user profile error:', error);
    return {
      success: false,
      error: '사용자 정보 수정 중 오류가 발생했습니다.',
    };
  }
};

// 토큰 저장
const setToken = (token) => {
  localStorage.setItem('access_token', token);
};

// refresh token 저장
const setRefreshToken = (refreshToken) => {
  localStorage.setItem('refresh_token', refreshToken);
};

// 토큰 가져오기
const getToken = () => {
  return localStorage.getItem('access_token');
};

// refresh token 가져오기
const getRefreshToken = () => {
  return localStorage.getItem('refresh_token');
};

// 토큰 삭제
const removeToken = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

// API 요청 헤더 생성
const getAuthHeaders = () => {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
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
        user: data.user,
        access_token: data.access_token,
        refresh_token: data.refresh_token,
      };
    } else {
      const mockResponse = await createMockResponse(mockLoginError(), 401);
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
      user: data.user,
      access_token: data.access_token,
      refresh_token: data.refresh_token,
    };
  } catch (error) {
    console.error('Login error:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

// 회원가입 API
export const register = async (userData) => {
  if (USE_MOCK_DATA) {
    // 목업 데이터 사용 - 이미 존재하는 이메일인지 확인
    const existingUser = checkEmailExists(userData.e_mail);
    
    if (existingUser) {
      const mockResponse = await createMockResponse({
        error: "Registration failed",
        message: "이미 존재하는 이메일입니다.",
        details: {}
      }, 400);
      const data = await mockResponse.json();
      
      return {
        success: false,
        error: data.message,
      };
    }

    // 새 사용자 생성
    const newUser = {
      user_id: `550e8400-e29b-41d4-a716-${Date.now()}`,
      user_name: userData.user_name,
      e_mail: userData.e_mail,
      password: userData.password,
      created_at: new Date().toISOString(),
      last_login: new Date().toISOString()
    };

    // localStorage에 새 사용자 추가
    addMockUser(newUser);

    const mockResponse = await createMockResponse(mockRegisterSuccess(newUser));
    const data = await mockResponse.json();
    
    return {
      success: true,
      user: data.user,
    };
  }

  // 실제 API 호출
  try {
    const response = await fetch(`${API_BASE_URL}/auth/register/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_name: userData.user_name,
        e_mail: userData.e_mail,
        password: userData.password,
        password_confirm: userData.password_confirm,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || '회원가입에 실패했습니다.');
    }

    return {
      success: true,
      user: data.user,
    };
  } catch (error) {
    console.error('Register error:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

// 로그아웃 API
export const logout = async () => {
  if (USE_MOCK_DATA) {
    // 목업 데이터 사용
    await createMockResponse(mockLogoutSuccess);
    removeToken();
    return { success: true };
  }

  // 실제 API 호출
  try {
    const refreshToken = getRefreshToken();
    
    const response = await fetch(`${API_BASE_URL}/auth/logout/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        refresh_token: refreshToken,
      }),
    });

    if (response.ok) {
      removeToken();
      return { success: true };
    }
  } catch (error) {
    console.error('Logout error:', error);
  }
  
  // API 호출 실패해도 토큰은 삭제
  removeToken();
  return { success: true };
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
      const users = getMockUsersFromData();
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
    const response = await fetch(`${API_BASE_URL}/users/profile/`, {
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

// 인증 상태 확인
export const isAuthenticated = () => {
  return !!getToken();
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
    const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
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
export const getMockUsers = () => {
  const users = getMockUsersFromData();
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
  getMockUsers,
  resetMockData,
  apiRequest,
}; 
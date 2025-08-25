// 더미 사용자 데이터
const getMockUsersInternal = () => {
  const storedUsers = localStorage.getItem('mockUsers');
  if (storedUsers) {
    return JSON.parse(storedUsers);
  }
  
  // 기본 사용자 데이터
  const defaultUsers = [
    {
      user_id: "550e8400-e29b-41d4-a716-446655440001",
      user_name: "김철수",
      e_mail: "test1@example.com",
      password: "password123",
      created_at: "2024-01-15T10:30:00Z",
      last_login: "2024-01-20T14:25:00Z"
    },
    {
      user_id: "550e8400-e29b-41d4-a716-446655440002", 
      user_name: "이영희",
      e_mail: "test2@example.com",
      password: "password123",
      created_at: "2024-01-10T09:15:00Z",
      last_login: "2024-01-19T16:45:00Z"
    },
    {
      user_id: "550e8400-e29b-41d4-a716-446655440003",
      user_name: "박민수", 
      e_mail: "test3@example.com",
      password: "password123",
      created_at: "2024-01-05T11:20:00Z",
      last_login: "2024-01-18T13:30:00Z"
    }
  ];
  
  // 기본 사용자 데이터를 localStorage에 저장
  localStorage.setItem('mockUsers', JSON.stringify(defaultUsers));
  return defaultUsers;
};

// 사용자 데이터 저장
const saveMockUsers = (users) => {
  localStorage.setItem('mockUsers', JSON.stringify(users));
};

// 새 사용자 추가
const addMockUser = (newUser) => {
  const users = getMockUsersInternal();
  users.push(newUser);
  saveMockUsers(users);
  return users;
};

// 사용자 검증 (이메일 중복 체크 포함)
const validateMockUser = (email, password) => {
  const users = getMockUsersInternal();
  return users.find(user => 
    user.e_mail === email && user.password === password
  );
};

// 이메일 중복 체크
const checkEmailExists = (email) => {
  const users = getMockUsersInternal();
  return users.find(user => user.e_mail === email);
};

// 외부에서 사용할 getMockUsers 함수
export const getMockUsers = () => {
  return getMockUsersInternal();
};

export const mockUsers = getMockUsersInternal();

// 더미 JWT 토큰 생성
export const generateMockToken = (userId) => {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(JSON.stringify({ 
    user_id: userId, 
    exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60) // 24시간 후 만료
  }));
  const signature = btoa('mock-signature');
  
  return `${header}.${payload}.${signature}`;
};

// 더미 API 응답 생성
export const createMockResponse = (data, status = 200, delay = 1000) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        ok: status >= 200 && status < 300,
        status,
        json: async () => data
      });
    }, delay);
  });
};

// 로그인 성공 응답
export const mockLoginSuccess = (user) => ({
  message: "로그인 성공",
  access_token: generateMockToken(user.user_id),
  refresh_token: generateMockToken(user.user_id),
  user: {
    user_id: user.user_id,
    user_name: user.user_name,
    e_mail: user.e_mail,
    last_login: new Date().toISOString()
  }
});

// 로그인 실패 응답
export const mockLoginError = (message) => ({
  error: "Authentication failed",
  message: message || "이메일 또는 비밀번호가 올바르지 않습니다.",
  details: {}
});

// 회원가입 성공 응답
export const mockRegisterSuccess = (user) => ({
  message: "회원가입이 완료되었습니다.",
  user: {
    user_id: user.user_id,
    user_name: user.user_name,
    e_mail: user.e_mail,
    created_at: user.created_at
  }
});

// 유저 정보 조회 응답
export const mockUserProfile = (user) => ({
  user_id: user.user_id,
  user_name: user.user_name,
  e_mail: user.e_mail,
  created_at: user.created_at,
  last_login: user.last_login
});

// 로그아웃 성공 응답
export const mockLogoutSuccess = {
  message: "로그아웃 성공"
};

// 토큰 갱신 응답
export const mockRefreshTokenSuccess = (user) => ({
  access_token: generateMockToken(user.user_id),
  refresh_token: generateMockToken(user.user_id)
});

// 내보내기
export { addMockUser, validateMockUser, checkEmailExists }; 
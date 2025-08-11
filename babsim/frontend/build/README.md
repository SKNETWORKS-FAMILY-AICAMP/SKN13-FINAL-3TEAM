# JACKLETTE - Hyundai Car AI Platform

현대 자동차 AI 플랫폼으로, 챗봇, 디자인 자산 라이브러리, 인사이트 트렌드, 프로토타입 랩 기능을 제공합니다.

## 🚀 시작하기

### 설치 및 실행

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

## 🧪 개발 모드 - 더미 데이터

현재 개발 모드에서는 더미 데이터를 사용하여 API 서버 없이도 기능을 테스트할 수 있습니다.

### 테스트 계정

다음 계정으로 로그인하여 기능을 테스트해보세요:

| 이름 | 이메일 | 비밀번호 |
|------|--------|----------|
| 김철수 | test1@example.com | password123 |
| 이영희 | test2@example.com | password123 |
| 박민수 | test3@example.com | password123 |

### 로그인 방법

1. `/login` 페이지로 이동
2. "계정 보기" 버튼 클릭
3. 원하는 계정의 "사용하기" 버튼 클릭
4. 자동으로 폼이 채워지면 "Sign In" 버튼 클릭

### 회원가입

새로운 계정을 만들어 테스트할 수도 있습니다:

1. `/signup` 페이지로 이동
2. 정보 입력 후 회원가입
3. 로그인 페이지로 자동 이동
4. 새로 만든 계정으로 로그인

## 🔧 기능

### 인증 시스템
- ✅ 로그인/회원가입
- ✅ JWT 토큰 기반 인증
- ✅ 보호된 라우트
- ✅ 자동 로그인 상태 확인
- ✅ 로그아웃 기능

### 페이지별 기능
- **Home**: 메인 페이지
- **Login**: 로그인 페이지 (더미 데이터 지원)
- **Signup**: 회원가입 페이지 (더미 데이터 지원)
- **Asset Library**: 디자인 자산 라이브러리 (로그인 필요)
- **Insight & Trends**: 현대 자동차 인사이트 (로그인 필요)
- **Prototype Lab**: 프로토타입 랩 (로그인 필요)
- **Chatbot**: AI 챗봇 (로그인 필요)

## 🛠 기술 스택

- **Frontend**: React 18, Vite
- **Styling**: Tailwind CSS
- **Routing**: React Router v6
- **State Management**: React Context API
- **Authentication**: JWT Token

## 📁 프로젝트 구조

```
src/
├── components/          # 재사용 가능한 컴포넌트
│   ├── Header.jsx     # 헤더 (로그인 상태 표시)
│   ├── Footer.jsx     # 푸터
│   └── ProtectedRoute.jsx # 보호된 라우트 컴포넌트
├── contexts/           # React Context
│   └── AuthContext.jsx # 인증 상태 관리
├── pages/              # 페이지 컴포넌트
│   ├── Home.jsx       # 메인 페이지
│   ├── Login.jsx      # 로그인 페이지
│   ├── Signup.jsx     # 회원가입 페이지
│   └── ...            # 기타 페이지들
├── services/           # API 서비스
│   ├── authService.js # 인증 관련 API
│   └── mockData.js    # 더미 데이터
└── App.jsx            # 메인 앱 컴포넌트
```

## 🔄 API 연동

### 실제 API 서버 사용

`src/services/authService.js`에서 `USE_MOCK_DATA`를 `false`로 변경하면 실제 API 서버와 연동됩니다.

```javascript
const USE_MOCK_DATA = false; // 실제 API 사용
```

### API 엔드포인트

- **Base URL**: `http://localhost:8000/api/v1`
- **인증 방식**: JWT Bearer Token
- **Content-Type**: `application/json`

## 🎯 주요 기능

### 1. 인증 시스템
- 이메일/비밀번호 로그인
- 회원가입
- JWT 토큰 관리
- 자동 로그인 상태 확인
- 보호된 라우트

### 2. 더미 데이터 시스템
- 개발 모드에서 API 서버 없이 테스트 가능
- 미리 정의된 테스트 계정
- 실제 API와 동일한 응답 형식
- 토큰 기반 인증 시뮬레이션

### 3. 사용자 인터페이스
- 반응형 디자인
- 로딩 상태 표시
- 에러 메시지 처리
- 성공 메시지 표시

## 🚀 배포

```bash
# 프로덕션 빌드
npm run build

# 빌드 결과 확인
npm run preview
```

## 📝 개발 노트

- 현재 더미 데이터 모드로 설정되어 있습니다
- 실제 API 서버 연동 시 `USE_MOCK_DATA`를 `false`로 변경하세요
- 모든 보호된 페이지는 로그인이 필요합니다
- 토큰은 localStorage에 저장됩니다

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

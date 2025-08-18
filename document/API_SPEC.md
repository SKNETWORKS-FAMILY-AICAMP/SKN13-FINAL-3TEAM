# API 명세서 (Django-React 통신)

## 개요
이 문서는 Django 백엔드와 React 프론트엔드 간의 API 통신 명세를 정의합니다.
데이터베이스 설계문서를 기반으로 실제 테이블 구조에 맞춰 API를 구성하며, React 프론트엔드의 실제 구현을 반영합니다.

## 기본 정보
- **Base URL**: `http://localhost:8000/api`
- **Content-Type**: `application/json`
- **인증 방식**: JWT Token (Bearer Token)
- **개발 모드**: Mock Data 지원 (USE_MOCK_DATA = true)

## 데이터베이스 구조 기반 API

### 0. 주요 기능
1. **Users 테이블 관련 API**
   - 회원가입, 로그인, 로그아웃
   - 유저 정보 조회 및 수정
   - 프로필 업데이트 (전화번호, 회사, 부서, 직책 포함)

2. **Chat_session 테이블 관련 API**
   - 유저별 챗봇 세션 조회
   - 챗봇 세션 생성 및 종료
   - 세션별 제목 관리

3. **Prompt_log 테이블 관련 API**
   - 세션별 프롬프트 로그 조회
   - 프롬프트 로그 생성
   - AI 응답 저장

4. **Generated_result 테이블 관련 API**
   - 프롬프트별 생성 결과 조회
   - 생성 결과 저장 (텍스트, 이미지, 3D, 4D)

5. **Asset_library 테이블 관련 API**
   - 디자인 자료 목록 조회 (검색, 필터링, 페이지네이션)
   - 디자인 자료 업로드 (PDF, 이미지)
   - 좋아요 기능
   - 카테고리별 분류

6. **Library_comments 테이블 관련 API**
   - 라이브러리 댓글 조회 및 작성
   - 댓글 좋아요 기능
   - 사용자별 댓글 관리

7. **Insight_trends 테이블 관련 API**
   - 차량 모델 목록 조회 (차종, 출시연도별 필터링)
   - 특정 차량 모델 상세 정보
   - CSV 데이터 파싱 및 분석

8. **Design_material 테이블 관련 API**
   - 차량별 디자인 재질 정보 조회
   - 재질 유형 및 사용 위치별 필터링

9. **Engineering_spec 테이블 관련 API**
   - 차량별 공학적 스펙 조회
   - 공기역학, 무게, 알루미늄 비율 등

10. **Sales_stat 테이블 관련 API**
    - 차량별 판매 통계 조회
    - 연도/월별 필터링

11. **User_review 테이블 관련 API**
    - 차량별 사용자 리뷰 조회
    - 감성 점수별 필터링

12. **새로운 기능**
    - Unsplash 이미지 검색 서비스
    - 3D 모델 뷰어 (Three.js)
    - 프로토타입 랩 (4D 모델링)
    - 트렌드 분석 및 인사이트 생성

### 1. Users 테이블 관련 API

#### 1.1 회원가입
**POST** `/auth/register/`

**Request Body:**
```json
{
  "user_name": "string",
  "e_mail": "string",
  "password": "string",
  "password_confirm": "string",
  "phone_number": "string",
  "company": "string",
  "department": "string",
  "position": "string"
}
```

**Response (201 Created):**
```json
{
  "message": "회원가입이 완료되었습니다.",
  "user": {
    "user_id": "uuid",
    "user_name": "string",
    "e_mail": "string",
    "phone_number": "string",
    "company": "string",
    "department": "string",
    "position": "string",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### 1.2 로그인
**POST** `/auth/login/`

**Request Body:**
```json
{
  "e_mail": "string",
  "password": "string"
}
```

**Response (200 OK):**
```json
{
  "message": "로그인 성공",
  "access_token": "string",
  "refresh_token": "string",
  "user": {
    "user_id": "uuid",
    "user_name": "string",
    "e_mail": "string",
    "phone_number": "string",
    "company": "string",
    "department": "string",
    "position": "string",
    "last_login": "2024-01-01T00:00:00Z"
  }
}
```

#### 1.3 로그아웃
**POST** `/auth/logout/`

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response (200 OK):**
```json
{
  "message": "로그아웃 성공"
}
```

#### 1.4 유저 정보 조회
**GET** `/auth/profile/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "user_id": "uuid",
  "user_name": "string",
  "e_mail": "string",
  "phone_number": "string",
  "company": "string",
  "department": "string",
  "position": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T00:00:00Z"
}
```

#### 1.5 유저 정보 수정
**PUT** `/auth/profile/update/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "user_name": "string",
  "e_mail": "string",
  "phone_number": "string",
  "company": "string",
  "department": "string",
  "position": "string"
}
```

**Response (200 OK):**
```json
{
  "message": "사용자 정보가 성공적으로 업데이트되었습니다.",
  "user": {
    "user_id": "uuid",
    "user_name": "string",
    "e_mail": "string",
    "phone_number": "string",
    "company": "string",
    "department": "string",
    "position": "string",
    "last_login": "2024-01-01T00:00:00Z"
  }
}
```

#### 1.6 토큰 갱신
**POST** `/auth/refresh/`

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response (200 OK):**
```json
{
  "access_token": "string",
  "refresh_token": "string"
}
```

## Mock Data 지원

개발 중에는 `USE_MOCK_DATA = true` 설정으로 실제 API 호출 없이 목업 데이터를 사용할 수 있습니다.

### Mock Data 구조
- 사용자 정보, 채팅 세션, 프롬프트 로그
- 에셋 라이브러리 자료 및 댓글
- 차량 모델 정보 및 스펙
- 판매 통계 및 사용자 리뷰

## 에러 응답 형식

### 4xx 에러
```json
{
  "error": "string",
  "message": "string",
  "details": {}
}
```

### 5xx 에러
```json
{
  "error": "Internal Server Error",
  "message": "서버 내부 오류가 발생했습니다.",
  "details": {}
}
```

## 상태 코드

- **200**: 성공
- **201**: 생성 성공
- **400**: 잘못된 요청
- **401**: 인증 실패
- **403**: 권한 없음
- **404**: 리소스 없음
- **500**: 서버 오류

## 인증 헤더 예시

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 파일 업로드

이미지 및 문서 파일 업로드 시 `multipart/form-data` 형식을 사용합니다.

## 페이지네이션

모든 목록 조회 API는 페이지네이션을 지원하며, `page`와 `page_size` 파라미터를 사용합니다.

## 검색 및 필터링

지원되는 API에서 검색과 필터링 기능을 제공합니다. 각 API의 `Query Parameters` 섹션을 참조하세요.

## 데이터베이스 관계

이 API는 다음과 같은 데이터베이스 관계를 반영합니다:

- **Users** ↔ **Chat_session**: 1:N 관계
- **Chat_session** ↔ **Prompt_log**: 1:N 관계  
- **Prompt_log** ↔ **Generated_result**: 1:N 관계
- **Users** ↔ **Asset_library**: 1:N 관계
- **Asset_library** ↔ **Library_comments**: 1:N 관계
- **Insight_trends** ↔ **Design_material/Engineering_spec/Sales_stat/User_review**: 1:N 관계

## 개발 환경 설정

### Mock Data 사용
```javascript
const USE_MOCK_DATA = true; // 개발 중
const USE_MOCK_DATA = false; // 프로덕션
```

### 환경 변수
```bash
VITE_UNSPLASH_ACCESS_KEY=your_unsplash_api_key
```

## 프론트엔드 컴포넌트

### 주요 페이지
- Home, About, Login, Signup
- AssetLibrary, InsightTrends, PrototypeLab
- Chatbot, Profile, MyWorkspace

### 주요 컴포넌트
- Header, Footer, HeroSection
- ThreeDViewer, ProtectedRoute
- FAQSection, ContactSection

## 업데이트 내역

- **2024-01-XX**: React 프론트엔드 구현 반영
- **2024-01-XX**: Mock Data 지원 추가
- **2024-01-XX**: 새로운 기능 API 추가 (Unsplash, 3D 뷰어, 프로토타입 랩)
- **2024-01-XX**: 사용자 프로필 확장 (전화번호, 회사, 부서, 직책)
- **2024-01-XX**: 에셋 라이브러리 기능 확장 (좋아요, 댓글, 카테고리)

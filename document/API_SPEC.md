# API 명세서 (Django-React 통신)

## 개요
이 문서는 Django 백엔드와 React 프론트엔드 간의 API 통신 명세를 정의합니다.
데이터베이스 설계문서를 기반으로 실제 테이블 구조에 맞춰 API를 구성합니다.

## 기본 정보
- **Base URL**: `http://localhost:8000/api`
- **Content-Type**: `application/json`
- **인증 방식**: JWT Token (Bearer Token)

## 데이터베이스 구조 기반 API

### 0. 주요 기능

#### **인증 및 사용자 관리**
1. **Users 테이블 관련 API**
   - 1.1 회원가입: `/auth/register/` - 사용자 정보 등록
   - 1.2 로그인: `/auth/login/` - JWT 토큰 발급
   - 1.3 로그아웃: `/auth/logout/` - 토큰 무효화
   - 1.4 유저 정보 조회: `/auth/profile/` - 프로필 정보 조회 (GET)
   - 1.5 유저 정보 수정: `/auth/profile/` - 프로필 정보 업데이트
   - 1.6 프로필 이미지 업로드: `/auth/profile/upload-image/` - 이미지 파일 업로드 (S3)
   - 1.7 사용 가능한 배경 이미지 조회: `/auth/profile/available-images/` - 채팅 세션 이미지 목록

#### **챗봇 시스템**
2. **Chat_session 테이블 관련 API**
   - 2.1 유저별 챗봇 세션 조회: `GET /chat/sessions/` - 페이지네이션 지원
   - 2.2 챗봇 세션 생성: `POST /chat/sessions/` - 새 세션 생성
   - 2.3 세션 제목 수정: `PUT /chat/sessions/{session_id}/title/` - 세션 제목 변경
   - 2.4 챗봇 세션 종료: `PUT /chat/sessions/{session_id}/end/` - 세션 종료

3. **Prompt_log & Generated_result 통합 API**
   - 3.1 세션별 프롬프트 로그 조회: `GET /chat/sessions/{session_id}/prompts/` - 결과 포함
   - 3.2 프롬프트 로그 생성: - AI 응답 및 결과 저장 / Django 내부 처리
   - 3.3 챗봇 메세지 생성: `POST /chat/sessions/{session_id}/message/` - 챗봇 응답 생성
   - **통합 특징**: 프롬프트와 생성 결과를 하나의 API로 관리 (result_type: text, image, 3d, 4d)

#### **에셋 라이브러리 시스템**
4. **Asset_library 테이블 관련 API**
   - 4.1 디자인 자료 목록 조회: `/library/assets/` - 검색, 필터링, 페이지네이션
   - 4.2 디자인 자료 업로드: `/library/assets/` - PDF 및 이미지 업로드 (단일 POST)
   - 4.3 디자인 자료 수정: `/library/assets/{asset_id}/` - 선택적 필드 업데이트
   - 4.4 디자인 자료 삭제: `/library/assets/{asset_id}/` - 자산 삭제
   - 4.5 디자인 자료 좋아요: `/library/assets/{asset_id}/like/` - 좋아요 토글

5. **Library_comments 테이블 관련 API**
   - 5.1 댓글 조회: `/library/assets/{asset_id}/comments/` - 페이지네이션 지원
   - 5.2 댓글 작성: `/library/assets/{asset_id}/comments/` - 새 댓글 작성
   - 5.3 댓글 삭제: `/library/assets/{asset_id}/comments/{comment_id}/` - 댓글 삭제
   - 5.4 댓글 좋아요: `/library/assets/{asset_id}/comments/{comment_id}/like/` - 좋아요 토글

#### **인사이트 및 트렌드 분석**
6. **Insight_trends 테이블 관련 API**
   - 6.1 차량 모델 목록 조회: `/insights/models/` - 차종, 출시연도별 필터링
   - 6.2 차량 상세 정보 조회: `/insights/models/{car_model_id}/` - 통합 정보 제공
   - **통합 특징**: Engineering_spec, User_review, Recent_articles를 하나의 API로 통합
   - **3D 모델 지원**: model_3d_path를 통한 Three.js 3D 뷰어 연동

#### **고급 기능 및 통합 서비스**
7. **외부 서비스 통합**
   - Unsplash 이미지 검색 서비스 연동
   - S3 파일 저장 및 관리
   - Three.js 3D 모델 뷰어 지원

8. **데이터 분석 및 시각화**
   - CSV 데이터 파싱 및 분석 (`hyundai_car_reviews.json`, `hyundai_car_history.json`)
   - 차량별 공학적 스펙 시각화 (전장, 전폭, 전고, 축거, 승차정원, 공차중량)
   - 사용자 리뷰 태그 분석 (성능, 공간, 디자인, 승차감)

9. **개발 및 테스트 지원**
   - Mock Data 지원 (USE_MOCK_DATA = true)
   - 페이지네이션 및 검색/필터링 (page, page_size, search, type, release_year)
   - 파일 업로드 (multipart/form-data)
   - 에러 처리 및 로깅
   - Presigned URL을 통한 S3 직접 업로드

## 파일 업로드 및 이미지 관리

### 프로필 이미지 업로드
- **API 엔드포인트**: `POST /auth/profile/upload-image/`
- **지원 형식**: JPEG, PNG, GIF 등 이미지 파일
- **최대 크기**: 5MB
- **저장 방식**: 
  - **MOCKDATA 모드**: Base64로 변환하여 localStorage에 저장
  - **실제 API 모드**: S3에 업로드 후 URL 반환
- **처리 과정**: 
  1. 이미지 파일 업로드 → S3 저장 또는 Base64 변환
  2. 반환된 URL/Base64를 `updateUserProfile`로 사용자 정보에 저장

### 배경 이미지 설정
- **API 엔드포인트**: `GET /auth/profile/available-images/`
- **이미지 소스**: 사용자 채팅 세션에서 생성된 기존 S3 이미지들
- **저장 방식**: 사용자가 선택한 기존 S3 이미지 경로를 `background_image` 필드에 저장
- **현재 구현**: MOCKDATA로 `assets/ioniq5.png` 사용
- **향후 확장**: 사용자 세션의 이미지들 중에서 선택 가능하도록 구현 예정

### 이미지 처리 흐름
```
프로필 이미지: 파일 선택 → uploadProfileImage() → S3/Base64 → updateUserProfile()
배경 이미지: Chat_session → Prompt_log_Generated_result → result_path(S3_URL) → updateUserProfile()
```

### ERD 기반 배경 이미지 검색 과정
```sql
-- 1. 사용자 ID로 채팅 세션들 조회
SELECT session_id, session_title FROM Chat_session WHERE user_id = ?

-- 2. 해당 세션들에서 이미지 타입 결과들 조회
SELECT prompt_id, session_id, result_path, created_at, user_prompt
FROM Prompt_log_Generated_result 
WHERE session_id IN (세션ID들) AND result_type = 'image'
ORDER BY created_at DESC
```

### 1. Users 테이블 관련 API

#### 1.1 회원가입
**POST** `/auth/register/`

**Request Body:**
```json
{
  "user_name": "string",
  "e_mail": "string",
  "password": "string",
  "password_confirm": "string"
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
  "profile_image": "string (S3 URL)",
  "background_image": "string (S3 URL)",
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T00:00:00Z"
}
```

**특징:**
- **완전한 프로필 정보**: 모든 사용자 정보 필드 포함
- **이미지 URL**: profile_image와 background_image의 S3 URL 제공
- **JWT 인증**: Authorization 헤더의 Bearer 토큰으로 사용자 식별

#### 1.5 유저 정보 수정
**POST** `/auth/profile/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_name": "string",
  "e_mail": "string",
  "phone_number": "string",
  "company": "string",
  "department": "string",
  "position": "string",
  "background_image": "string (S3 경로 또는 URL)"
}
```

**특징:**
- **배경 이미지**: 사용자 채팅 세션의 기존 S3 이미지 중에서 선택
- **프로필 이미지**: 별도 API로 분리하여 S3에 새로 업로드
- **텍스트 정보**: 기본 사용자 정보만 처리

**Response (200 OK):**
```json
{
  "success": true,
  "message": "사용자 정보가 성공적으로 업데이트되었습니다.",
  "user": {
    "user_id": "uuid",
    "user_name": "string",
    "e_mail": "string",
    "phone_number": "string",
    "company": "string",
    "department": "string",
    "position": "string",
    "background_image": "string (S3 경로)",
    "last_login": "2024-01-01T00:00:00Z"
  }
}
```

#### 1.6 프로필 이미지 업로드
**POST** `/auth/profile/upload-image/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body (FormData):**
```
profile_image: file (이미지 파일, 5MB 이하)
```

**특징:**
- **별도 API**: 프로필 이미지만을 위한 전용 엔드포인트
- **S3 업로드**: 이미지를 S3에 새로 업로드
- **파일 제한**: 5MB 이하, 이미지 파일만 지원

**Response (200 OK):**
```json
{
  "success": true,
  "message": "프로필 이미지가 성공적으로 업로드되었습니다.",
  "profile_image_url": "string (S3 URL)",
  "user": {
    "user_id": "uuid",
    "profile_image": "string (S3 URL)"
  }
}
```

**에러 Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "이미지 파일 크기는 5MB 이하여야 합니다."
}
```

**에러 Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "이미지 파일만 업로드 가능합니다."
}
```

#### 1.7 사용 가능한 배경 이미지 조회
**GET** `/auth/profile/available-images/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**특징:**
- **이미지 소스**: 사용자 채팅 세션에서 생성된 이미지 결과들 (result_type = 'image')
- **데이터 흐름**: Users → Chat_session → Prompt_log & Generated_result
- **JWT 인증**: Authorization 헤더의 JWT 토큰으로 사용자 식별
- **S3 경로**: result_path에서 S3 이미지 URL 목록 제공

**Response (200 OK):**
```json
{
  "success": true,
  "available_images": [
    {
      "prompt_id": "uuid",
      "session_id": "uuid",
      "session_title": "string (채팅 세션 제목)",
      "image_url": "string (S3 URL, result_path 값)",
      "created_at": "2024-01-01T00:00:00Z",
      "user_prompt": "string (이미지 생성 프롬프트)"
    }
  ],
  "total_count": 10
}
```

**Response (204 No Content):**
사용자가 생성한 이미지가 없는 경우

**에러 Response (401 Unauthorized):**
```json
{
  "success": false,
  "error": "인증이 필요합니다."
}
```

## MOCKDATA 모드 지원

### 개발 환경 이미지 처리
- **USE_MOCK_DATA = true**: Base64 인코딩으로 localStorage에 저장
- **USE_MOCK_DATA = false**: S3 업로드 후 URL 반환
- **프로필 이미지**: MOCKDATA 모드에서 Base64 문자열을 `profile_image` 필드에 저장
- **배경 이미지**: MOCKDATA 모드에서 `assets/ioniq5.png` 사용

### MOCKDATA 모드 동작 방식
```javascript
// authService.js에서 USE_MOCK_DATA 플래그로 분기
export const uploadProfileImage = async (imageFile) => {
  if (USE_MOCK_DATA) {
    // Base64 변환 → localStorage 저장 → Base64 반환
    return { image_url: base64String };
  } else {
    // S3 업로드 → URL 반환
    return { image_url: s3Url };
  }
};
```
**GET** `/auth/profile/available-images/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**특징:**
- **배경 이미지 선택용**: 사용자의 모든 채팅 세션에서 생성된 이미지 목록
- **S3 경로 제공**: 배경 이미지로 선택할 수 있는 이미지들의 S3 경로 반환

**Response (200 OK):**
```json
{
  "success": true,
  "images": [
    {
      "image_id": "uuid",
      "session_title": "string",
      "image_url": "string (S3 URL)",
      "created_at": "2024-01-01T00:00:00Z",
      "result_type": "image"
    }
  ]
}
```

### 2. Chat_session 테이블 관련 API

#### 2.1 유저별 챗봇 세션 조회
**GET** `/chat/sessions/`

**Query Parameters:**
```
page: integer (기본값: 1)
page_size: integer (기본값: 10)
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "session_id": "uuid",
      "user_id": "uuid",
      "title": "현대자동차 디자인 문의",
      "created_at": "2024-01-01T10:00:00Z",
      "last_activity": "2024-01-01T15:30:00Z",
      "prompt_count": 8
    }
  ]
}
```

#### 2.2 챗봇 세션 생성
**POST** `/chat/sessions/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "string"
}
```

**Response (201 Created):**
```json
{
  "message": "챗봇 세션이 생성되었습니다.",
  "session": {
    "session_id": "uuid",
    "user_id": "uuid",
    "title": "string",
    "created_at": "2024-01-01T10:00:00Z",
    "last_activity": "2024-01-01T10:00:00Z",
    "prompt_count": 0
  }
}
```

#### 2.3 세션 제목 수정
**PUT** `/chat/sessions/{session_id}/title/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "string"
}
```

**Response (200 OK):**
```json
{
  "message": "세션 제목이 수정되었습니다.",
  "session": {
    "session_id": "uuid",
    "title": "string",
    "updated_at": "2024-01-01T16:30:00Z"
  }
}
```

#### 2.4 챗봇 세션 종료
**PUT** `/chat/sessions/{session_id}/end/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "챗봇 세션이 종료되었습니다.",
  "session": {
    "session_id": "uuid",
    "ended_at": "2024-01-01T16:00:00Z",
    "total_prompts": 12,
    "total_duration": "6시간"
  }
}
```

### 3. Prompt_log & Generated_result 통합 API

#### 3.1 세션별 프롬프트 로그 조회 (결과 포함)
**GET** `/chat/sessions/{session_id}/prompts/`

**Query Parameters:**
```
page: integer (기본값: 1)
page_size: integer (기본값: 20)
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "count": 8,
  "next": null,
  "previous": null,
  "results": [
    {
      "prompt_id": "uuid",
      "session_id": "uuid",
      "user_prompt": "현대자동차의 디자인 철학에 대해 설명해줘",
      "ai_response": "현대자동차는 'Sensuous Sportiness'라는 디자인 철학을...",
      "result_type": "text",
      "result_path": "string (결과 파일 경로)",
      "created_at": "2024-01-01T10:30:00Z",
      "response_time": 2.5
    }
  ]
}
```

#### 3.2 프롬프트 로그 생성 (AI 응답 및 결과 포함)
**POST** `/chat/sessions/{session_id}/prompts/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_prompt": "string",
  "ai_response": "string",
  "result_type": "string (text, image, 3d, 4d)",
  "result_path": "string (결과 파일 경로, 선택사항)",
  "response_time": "number"
}
```

**Response (201 Created):**
```json
{
  "message": "프롬프트 로그가 생성되었습니다.",
  "prompt": {
    "prompt_id": "uuid",
    "session_id": "uuid",
    "user_prompt": "string",
    "ai_response": "string",
    "result_type": "string",
    "result_path": "string",
    "created_at": "2024-01-01T10:30:00Z",
    "response_time": 2.5
  }
}
```

#### 3.3 특정 프롬프트 로그 조회
**GET** `/chat/prompts/{prompt_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "prompt_id": "uuid",
  "session_id": "uuid",
  "user_prompt": "string",
  "ai_response": "string",
  "result_type": "string",
  "result_path": "string",
  "created_at": "2024-01-01T10:30:00Z",
  "response_time": 2.5,
  "session": {
    "session_id": "uuid",
    "title": "string"
  }
}
```

**참고사항:**
- **2번 Chat_session**: 세션 관리 (생성, 제목 수정, 종료)
- **3번 Prompt_log & Generated_result**: 대화 내용과 AI 생성 결과를 통합 관리
- `result_type`: AI가 생성한 결과의 유형 (text, image, 3d, 4d)
- `result_path`: 생성된 결과 파일의 경로 (이미지, 3D 모델, 4D 애니메이션 등)
- `response_time`: AI 응답 생성에 걸린 시간 (초 단위)

### 4. Asset_library 테이블 관련 API

#### 4.1 디자인 자료 목록 조회
**GET** `/library/assets/`

**Query Parameters:**
```
page: integer (기본값: 1)
page_size: integer (기본값: 6)
search: string (검색어)
search_type: string (검색 타입: 'all', 'title', 'summary')
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/library/assets/?page=2",
  "previous": null,
  "upload_presigned_url": "https://s3.amazonaws.com/...",
  "cover_presigned_url": "https://s3.amazonaws.com/...",
  "results": [
    {
      "lib_id": "uuid",
      "user_id": "uuid",
      "title": "string",
      "summary": "string",
      "documents": "string",
      "pdf_path": "string (S3 URL)",
      "img_path": "string (S3 URL 또는 Unsplash URL)",
      "upload_date": "2024-01-01",
      "likes": 0,
      "comment_count": 0,
      "category": "string"
    }
  ]
}
```

#### 4.2 디자인 자료 업로드 (단일 POST 요청)
**POST** `/library/assets/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body (FormData):**
```
title: string
summary: string
category: string
documents: file (PDF 파일)
cover_photo: file (커버 이미지, 선택사항)
```

**Response (201 Created):**
```json
{
  "message": "자산이 성공적으로 업로드되었습니다.",
  "asset": {
    "lib_id": "uuid",
    "title": "string",
    "summary": "string",
    "category": "string",
    "documents": "string",
    "pdf_path": "string (S3 URL)",
    "img_path": "string (S3 URL 또는 Unsplash URL)",
    "upload_date": "2024-01-01T00:00:00Z",
    "likes": 0,
    "comment_count": 0
  }
}
```

#### 4.3 디자인 자료 수정
**PUT** `/library/assets/{asset_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body (FormData):**
```
title: string (선택사항)
summary: string (선택사항)
category: string (선택사항)
documents: file (선택사항, 새로운 PDF 파일)
cover_photo: file (선택사항, 새로운 커버 이미지)
```

**Response (200 OK):**
```json
{
  "message": "자산이 성공적으로 수정되었습니다.",
  "asset": {
    "lib_id": "uuid",
    "title": "string",
    "summary": "string",
    "category": "string",
    "documents": "string",
    "pdf_path": "string (S3 URL)",
    "img_path": "string (S3 URL 또는 Unsplash URL)",
    "updated_at": "2024-01-01T00:00:00Z",
    "likes": 0,
    "comment_count": 0
  }
}
```

**참고사항:**
- 모든 필드는 선택사항입니다. 수정하고 싶은 필드만 전송하면 됩니다.
- `documents` 파일을 변경하면 기존 PDF가 새로운 파일로 교체됩니다.
- `cover_photo` 이미지를 변경하면 기존 커버 이미지가 새로운 이미지로 교체됩니다.
- 파일을 변경하지 않으면 기존 파일이 유지됩니다.
- 텍스트 필드만 변경하고 싶다면 파일 필드는 전송하지 않아도 됩니다.

#### 4.4 디자인 자료 삭제
**DELETE** `/library/assets/{asset_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (204 No Content):**
```
삭제 성공 (응답 본문 없음)
```

#### 4.5 디자인 자료 좋아요/취소
**POST** `/library/assets/{lib_id}/like/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "likes": 15,
  "user_liked": true
}
```

**특징:**
- **토글 방식**: 이미 좋아요한 경우 취소, 안 한 경우 추가
- **실시간 카운트**: 좋아요 수가 실시간으로 업데이트
- **사용자 상태**: 현재 사용자의 좋아요 상태 반환

### 5. Library_comments 테이블 관련 API

#### 5.1 댓글 조회
**GET** `/library/assets/{lib_id}/comments/`

**Query Parameters:**
```
page: integer (기본값: 1)
page_size: integer (기본값: 10)
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "count": 15,
  "next": "http://localhost:8000/api/library/assets/{lib_id}/comments/?page=2",
  "previous": null,
  "results": [
    {
      "comment_id": "uuid",
      "asset_library": "uuid",
      "user_id": "uuid",
      "user_name": "string",
      "comments": "string",
      "created_at": "2024-01-01T10:30:00Z",
      "updated_at": "2024-01-01T10:30:00Z",
      "likes": 5
    }
  ]
}
```

#### 5.2 댓글 작성
**POST** `/library/assets/{lib_id}/comments/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "comments": "string"
}
```

**Response (201 Created):**
```json
{
  "comment_id": "uuid",
  "asset_library": "uuid",
  "user_id": "uuid",
  "user_name": "string",
  "comments": "string",
  "created_at": "2024-01-01T10:30:00Z",
  "updated_at": "2024-01-01T10:30:00Z",
  "likes": 0
}
```

**특징:**
- **자동 카운트**: 댓글 생성 시 `comment_count` 자동 증가
- **사용자 정보**: JWT 토큰에서 사용자 정보 자동 추출

#### 5.3 댓글 상세/수정/삭제
**GET/PUT/DELETE** `/library/comments/{comment_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json (PUT 요청 시)
```

**PUT Request Body:**
```json
{
  "comments": "string"
}
```

**GET Response (200 OK):**
```json
{
  "comment_id": "uuid",
  "asset_library": "uuid",
  "user_id": "uuid",
  "user_name": "string",
  "comments": "string",
  "created_at": "2024-01-01T10:30:00Z",
  "updated_at": "2024-01-01T10:30:00Z",
  "likes": 5
}
```

**DELETE Response (204 No Content):**
```
삭제 성공 (응답 본문 없음)
```

**특징:**
- **자동 카운트**: 댓글 삭제 시 `comment_count` 자동 감소
- **권한 확인**: 댓글 작성자만 수정/삭제 가능

#### 5.4 댓글 좋아요/취소
**POST** `/library/comments/{comment_id}/like/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "likes": 8,
  "user_liked": true
}
```

**특징:**
- **토글 방식**: 이미 좋아요한 경우 취소, 안 한 경우 추가
- **실시간 카운트**: 좋아요 수가 실시간으로 업데이트
- **사용자 상태**: 현재 사용자의 좋아요 상태 반환

### 6. Insight_trends 테이블 관련 API

#### 6.1 차량 모델 목록 조회
**GET** `/insights/models/`

**Query Parameters:**
```
page: integer (기본값: 1)
page_size: integer (기본값: 12)
type: string (차종: 'sedan', 'suv', 'ev', 'hybrid')
release_year: integer (출시연도)
search: string (검색어)
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/insights/models/?page=2",
  "previous": null,
  "results": [
    {
      "car_model_id": "uuid",
      "car_name": "string",
      "type": "string",
      "release_year": 2024
    }
  ]
}
```

#### 6.2 차량 상세 정보 조회
**GET** `/insights/models/{car_model_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "car_model_id": "uuid",
  "car_name": "string",
  "type": "string",
  "release_year": 2024,
  "engineering_specs": {
    "전장": "4,900 mm",
    "전폭": "1,860 mm", 
    "전고": "1,445 mm",
    "축거": "2,840 mm",
    "승차정원": "5명",
    "공차중량": "1,420 kg"
  },
  "user_reviews": [
    {
      "data_id": "string",
      "car_name": "string",
      "review": "string",
      "tags": {
        "성능": "string",
        "공간": "string", 
        "디자인": "string",
        "승차감": "string"
      }
    }
  ],
  "recent_articles": [
    {
      "car_name": "string",
      "year": "string",
      "explain": "string"
    }
  ],
  "model_3d_path": "string (S3 URL 또는 로컬 경로)"
}
```

**참고사항:**
- `engineering_specs`: 차량의 공학적 스펙 정보 (전장, 전폭, 전고, 축거, 승차정원, 공차중량)
- `user_reviews`: `hyundai_car_reviews.json`에서 해당 차량에 대한 사용자 리뷰 데이터
- `recent_articles`: `hyundai_car_history.json`에서 차량별 역사 정보를 Recent Articles 기능으로 활용
- `model_3d_path`: S3에 저장된 3D GLB 파일의 URL (Three.js 3D 뷰어에서 활용)

## Mock Data 지원

개발 중에는 `USE_MOCK_DATA = true` 설정으로 실제 API 호출 없이 목업 데이터를 사용할 수 있습니다.

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

### 프로필 이미지 업로드
- **지원 형식**: JPEG, PNG, GIF 등 이미지 파일
- **최대 크기**: 5MB
- **저장 방식**: S3에 업로드 후 URL 반환
- **API 엔드포인트**: `/auth/profile/upload-image/`

### 배경 이미지 설정
- **지원 형식**: 사용자 채팅 세션의 기존 S3 이미지
- **저장 방식**: 사용자가 선택한 기존 S3 이미지 경로 사용
- **API 엔드포인트**: `/auth/profile/available-images/` (이미지 목록 조회)
- **현재 구현**: MOCKDATA로 `assets/ioniq5.png` 사용
- **향후 확장**: 사용자 세션의 이미지들 중에서 선택 가능하도록 구현 예정

## 페이지네이션

모든 목록 조회 API는 페이지네이션을 지원하며, `page`와 `page_size` 파라미터를 사용합니다.

## 검색 및 필터링

지원되는 API에서 검색과 필터링 기능을 제공합니다. 각 API의 `Query Parameters` 섹션을 참조하세요.

## 데이터베이스 관계

이 API는 다음과 같은 데이터베이스 관계를 반영합니다:

- **Users** ↔ **Chat_session**: 1:N 관계
- **Chat_session** ↔ **Prompt_log**: 1:N 관계 (통합됨)
- **Users** ↔ **Asset_library**: 1:N 관계
- **Asset_library** ↔ **Library_comments**: 1:N 관계
- **Insight_trends** ↔ **Design_material/Engineering_spec/Sales_stat/User_review**: 1:N 관계 (7번으로 통합)

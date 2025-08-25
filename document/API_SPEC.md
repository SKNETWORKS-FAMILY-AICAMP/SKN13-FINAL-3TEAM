# API 명세서 (Django-React 통신)

## 개요
이 문서는 Django 백엔드와 React 프론트엔드 간의 API 통신 명세를 정의합니다.
데이터베이스 설계문서를 기반으로 실제 테이블 구조에 맞춰 API를 구성합니다.

## 기본 정보
- **Base URL**: `http://localhost:8000/api`
- **Content-Type**: `application/json`
- **인증 방식**: JWT Token (Bearer Token)

## 데이터베이스 구조 기반 API

### 0. 주요 기능<br>
1. Users 테이블 관련 API<br>
1.1 회원가입<br>
1.2 로그인<br>
1.3 로그아웃<br>
1.4 유저 정보 조회<br>
1.5 유저 정보 수정<br>

2. Chat_session 테이블 관련 API<br>
2.1 유저별 챗봇 세션 조회<br>
2.2 챗봇 세션 생성<br>
2.3 챗봇 세션 종료<br>

3. Prompt_log 테이블 관련 API<br>
3.1 세션별 프롬프트 로그 조회<br>
3.2 프롬프트 로그 생성<br>

5. **Asset_library 테이블 관련 API**
5.1 디자인 자료 목록 조회<br>
5.2 디자인 자료 업로드<br>

6. Library_comments 테이블 관련 API<br>
6.1 라이브러리 댓글 조회<br>
6.2 댓글 작성<br>

7. Insight_trends 테이블 관련 API<br>
7.1 차량 모델 목록 조회<br>
7.2 특정 차량 모델 상세 정보<br>

8. Design_material 테이블 관련 API<br>
8.1 차량별 디자인 재질 정보 조회<br>

9. Engineering_spec 테이블 관련 API<br>
9.1 차량별 공학적 스펙 조회<br>

10. Sales_stat 테이블 관련 API<br>
10.1 차량별 판매 통계 조회<br>

11. User_review 테이블 관련 API<br>
11.1 차량별 사용자 리뷰 조회<br>


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
**GET** `/users/profile/`

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
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T00:00:00Z"
}
```

#### 1.5 유저 정보 수정
**PUT** `/users/profile/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "user_name": "string",
  "e_mail": "string"
}
```

**Response (200 OK):**
```json
{
  "message": "유저 정보가 업데이트되었습니다.",
  "user": {
    "user_id": "uuid",
    "user_name": "string",
    "e_mail": "string",
    "last_login": "2024-01-01T00:00:00Z"
  }
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
documents: file (PDF 파일)
title: string
summary: string
category: string
cover_photo: file (선택사항, 이미지 파일)
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
**POST** `/library/assets/{asset_id}/like/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "likes": 15,
  "user_liked": true,
  "message": "좋아요가 추가되었습니다."
}
```

### 5. Library_comments 테이블 관련 API

#### 5.1 댓글 조회
**GET** `/library/assets/{asset_id}/comments/`

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
  "next": "http://localhost:8000/api/library/assets/{asset_id}/comments/?page=2",
  "previous": null,
  "results": [
    {
      "comment_id": "uuid",
      "lib_id": "uuid",
      "user_id": "uuid",
      "username": "string",
      "comments": "string",
      "created_at": "2024-01-01T10:30:00Z",
      "updated_at": "2024-01-01T10:30:00Z",
      "likes": 5,
      "user_liked": false,
      "user": {
        "user_id": "uuid",
        "user_name": "string"
      }
    }
  ]
}
```

#### 5.2 댓글 작성
**POST** `/library/assets/{asset_id}/comments/`

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
  "message": "댓글이 성공적으로 작성되었습니다.",
  "comment": {
    "comment_id": "uuid",
    "lib_id": "uuid",
    "user_id": "uuid",
    "username": "string",
    "comments": "string",
    "created_at": "2024-01-01T10:30:00Z",
    "updated_at": "2024-01-01T10:30:00Z",
    "likes": 0,
    "user_liked": false
  }
}
```

#### 5.3 댓글 삭제
**DELETE** `/library/assets/{asset_id}/comments/{comment_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (204 No Content):**
```
삭제 성공 (응답 본문 없음)
```

**참고사항:**
- 댓글 작성자만 삭제할 수 있습니다.
- 댓글 삭제 시 해당 댓글의 좋아요 정보도 함께 삭제됩니다.
- 삭제된 댓글은 복구할 수 없습니다.

#### 5.4 댓글 좋아요/취소
**POST** `/library/assets/{asset_id}/comments/{comment_id}/like/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "likes": 8,
  "user_liked": true,
  "message": "댓글 좋아요가 추가되었습니다."
}
```

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

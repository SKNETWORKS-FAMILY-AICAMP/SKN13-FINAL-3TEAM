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
1.1 로그인<br>
1.2 유저 정보 조회<br>
1.3 유저 정보 수정<br>

2. Chat_session 테이블 관련 API<br>
2.1 유저별 챗봇 세션 조회<br>
2.2 챗봇 세션 생성<br>
2.3 챗봇 세션 종료<br>

3. Prompt_log 테이블 관련 API<br>
3.1 세션별 프롬프트 로그 조회<br>
3.2 프롬프트 로그 생성<br>

4. Generated_result 테이블 관련 API<br>
4.1 프롬프트별 생성 결과 조회<br>
4.2 생성 결과 저장<br>

5. Asset_library 테이블 관련 APi<br>
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

#### 1.3 유저 정보 조회
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

#### 1.4 유저 정보 수정
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

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page`: 페이지 번호 (기본값: 1)
- `page_size`: 페이지당 항목 수 (기본값: 10)

**Response (200 OK):**
```json
{
  "count": 10,
  "next": "http://localhost:8000/api/v1/chat/sessions/?page=2",
  "previous": null,
  "results": [
    {
      "session_id": "uuid",
      "user_id": "uuid",
      "started_at": "2024-01-01T00:00:00Z",
      "ended_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### 2.2 챗봇 세션 생성
**POST** `/chat/sessions/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "started_at": "2024-01-01T00:00:00Z"
}
```

**Response (201 Created):**
```json
{
  "session_id": "uuid",
  "user_id": "uuid",
  "started_at": "2024-01-01T00:00:00Z",
  "ended_at": null
}
```

#### 2.3 챗봇 세션 종료
**PUT** `/chat/sessions/{session_id}/end/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "ended_at": "2024-01-01T00:00:00Z"
}
```

**Response (200 OK):**
```json
{
  "message": "세션이 종료되었습니다.",
  "session": {
    "session_id": "uuid",
    "user_id": "uuid",
    "started_at": "2024-01-01T00:00:00Z",
    "ended_at": "2024-01-01T00:00:00Z"
  }
}
```

### 3. Prompt_log 테이블 관련 API

#### 3.1 세션별 프롬프트 로그 조회
**GET** `/chat/sessions/{session_id}/prompts/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page`: 페이지 번호 (기본값: 1)
- `page_size`: 페이지당 항목 수 (기본값: 20)

**Response (200 OK):**
```json
{
  "count": 20,
  "next": "http://localhost:8000/api/v1/chat/sessions/1/prompts/?page=2",
  "previous": null,
  "results": [
    {
      "prompt_id": "uuid",
      "session_id": "uuid",
      "user_prompt": "string",
      "ai_response": "string",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### 3.2 프롬프트 로그 생성
**POST** `/chat/prompts/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "session_id": "uuid",
  "user_prompt": "string",
  "ai_response": "string"
}
```

**Response (201 Created):**
```json
{
  "prompt_id": "uuid",
  "session_id": "uuid",
  "user_prompt": "string",
  "ai_response": "string",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 4. Generated_result 테이블 관련 API

#### 4.1 프롬프트별 생성 결과 조회
**GET** `/chat/prompts/{prompt_id}/results/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "count": 5,
  "results": [
    {
      "result_id": "uuid",
      "prompt_id": "uuid",
      "result_type": "text|image|3d|4d",
      "result_path": "string",
      "result": "string"
    }
  ]
}
```

#### 4.2 생성 결과 저장
**POST** `/chat/results/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "prompt_id": "uuid",
  "result_type": "text|image|3d|4d",
  "result_path": "string",
  "result": "string"
}
```

**Response (201 Created):**
```json
{
  "result_id": "uuid",
  "prompt_id": "uuid",
  "result_type": "text",
  "result_path": "string",
  "result": "string"
}
```

### 5. Asset_library 테이블 관련 API

#### 5.1 디자인 자료 목록 조회
**GET** `/library/assets/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page`: 페이지 번호 (기본값: 1)
- `page_size`: 페이지당 항목 수 (기본값: 10)
- `search`: 검색어

**Response (200 OK):**
```json
{
  "count": 10,
  "next": "http://localhost:8000/api/v1/library/assets/?page=2",
  "previous": null,
  "results": [
    {
      "lib_id": "uuid",
      "user_id": "uuid",
      "documents": "string",
      "img_path": "string"
    }
  ]
}
```

#### 5.2 디자인 자료 업로드
**POST** `/library/assets/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body:**
```json
{
  "documents": "file",
  "img_path": "string"
}
```

**Response (201 Created):**
```json
{
  "lib_id": "uuid",
  "user_id": "uuid",
  "documents": "string",
  "img_path": "string"
}
```

### 6. Library_comments 테이블 관련 API

#### 6.1 라이브러리 댓글 조회
**GET** `/library/assets/{lib_id}/comments/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "count": 5,
  "results": [
    {
      "comment_id": "uuid",
      "lib_id": "uuid",
      "user_id": "uuid",
      "comments": "string"
    }
  ]
}
```

#### 6.2 댓글 작성
**POST** `/library/comments/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "lib_id": "uuid",
  "comments": "string"
}
```

**Response (201 Created):**
```json
{
  "comment_id": "uuid",
  "lib_id": "uuid",
  "user_id": "uuid",
  "comments": "string"
}
```

### 7. Insight_trends 테이블 관련 API

#### 7.1 차량 모델 목록 조회
**GET** `/insights/models/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `type`: 차종 (SUV, 세단 등)
- `release_year`: 출시 연도
- `page`: 페이지 번호 (기본값: 1)
- `page_size`: 페이지당 항목 수 (기본값: 10)

**Response (200 OK):**
```json
{
  "count": 10,
  "next": "http://localhost:8000/api/v1/insights/models/?page=2",
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

#### 7.2 특정 차량 모델 상세 정보
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
  "design_materials": [
    {
      "material_id": "uuid",
      "material_type": "string",
      "usage_area": "string"
    }
  ],
  "engineering_specs": [
    {
      "spec_id": "uuid",
      "cd_value": 0.25,
      "weight": 1500,
      "material_al_ratio": 0.3,
      "wheel_base": 2700,
      "pedestrian_safety_score": 85.5,
      "sensor_ready": true
    }
  ],
  "sales_stats": [
    {
      "year": 2024,
      "month": 1,
      "units_sold": 1500
    }
  ],
  "user_reviews": [
    {
      "review_id": "uuid",
      "sentiment_score": 4.2,
      "mentioned_features": "string"
    }
  ]
}
```

### 8. Design_material 테이블 관련 API

#### 8.1 차량별 디자인 재질 정보 조회
**GET** `/insights/models/{car_model_id}/materials/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `material_type`: 재질 유형
- `usage_area`: 사용 위치

**Response (200 OK):**
```json
{
  "count": 5,
  "results": [
    {
      "material_id": "uuid",
      "car_model_id": "uuid",
      "material_type": "string",
      "usage_area": "string"
    }
  ]
}
```

### 9. Engineering_spec 테이블 관련 API

#### 9.1 차량별 공학적 스펙 조회
**GET** `/insights/models/{car_model_id}/specs/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "count": 1,
  "results": [
    {
      "spec_id": "uuid",
      "car_model_id": "uuid",
      "cd_value": 0.25,
      "weight": 1500,
      "material_al_ratio": 0.3,
      "wheel_base": 2700,
      "pedestrian_safety_score": 85.5,
      "sensor_ready": true
    }
  ]
}
```

### 10. Sales_stat 테이블 관련 API

#### 10.1 차량별 판매 통계 조회
**GET** `/insights/models/{car_model_id}/sales/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `year`: 연도
- `month`: 월
- `page`: 페이지 번호 (기본값: 1)
- `page_size`: 페이지당 항목 수 (기본값: 12)

**Response (200 OK):**
```json
{
  "count": 12,
  "results": [
    {
      "car_model_id": "uuid",
      "year": 2024,
      "month": 1,
      "units_sold": 1500
    }
  ]
}
```

### 11. User_review 테이블 관련 API

#### 11.1 차량별 사용자 리뷰 조회
**GET** `/insights/models/{car_model_id}/reviews/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `sentiment_score_min`: 최소 감성 점수
- `sentiment_score_max`: 최대 감성 점수
- `page`: 페이지 번호 (기본값: 1)
- `page_size`: 페이지당 항목 수 (기본값: 10)

**Response (200 OK):**
```json
{
  "count": 10,
  "results": [
    {
      "review_id": "uuid",
      "car_model_id": "uuid",
      "sentiment_score": 4.2,
      "mentioned_features": "string"
    }
  ]
}
```

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

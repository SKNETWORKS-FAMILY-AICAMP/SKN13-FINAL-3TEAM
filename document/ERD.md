# ERD (Entity Relationship Diagram)

## 데이터베이스 테이블 구조

### 1. Users (사용자 정보)
| 필드명 | 데이터 타입 | PK | FK | Not Null | 설명 |
|--------|-------------|----|----|----------|------|
| user_id | UUID | ✅ | | ✅ | 사용자 고유 식별자 |
| password | VARCHAR(50) | | | ✅ | 비밀번호 |
| user_name | VARCHAR(50) | | | ✅ | 사용자 이름 |
| e_mail | VARCHAR(50) | | | ✅ | 이메일 |
| phone_number | VARCHAR(20) | | | | 전화번호 |
| company | VARCHAR(100) | | | | 회사명 |
| department | VARCHAR(100) | | | | 부서명 |
| position | VARCHAR(100) | | | | 직책 |
| profile_image | TEXT | | | | 프로필 이미지 (S3 URL) |
| background_image | TEXT | | | | 배경 이미지 (S3 URL) |
| created_at | TIMESTAMP | | | ✅ | 계정 생성일자 |
| last_login | TIMESTAMP | | | ✅ | 마지막 로그인 일자 |

### 2. Chat_session (챗봇 세션)
| 필드명 | 데이터 타입 | PK | FK | Not Null | 설명 |
|--------|-------------|----|----|----------|------|
| session_id | UUID | ✅ | | ✅ | 세션 고유 ID |
| user_id | UUID | | users | ✅ | 세션 주체 사용자 ID |
| session_title | VARCHAR(200) | | | | 세션 제목 |
| started_at | TIMESTAMP | | | ✅ | 시작 시간 |
| ended_at | TIMESTAMP | | | | 종료 시간 |

### 3. Prompt_log & Generated_result (통합 테이블)
| 필드명 | 데이터 타입 | PK | FK | Not Null | 설명 |
|--------|-------------|----|----|----------|------|
| prompt_id | UUID | ✅ | | ✅ | 프롬프트 고유 ID |
| session_id | UUID | | chat_session | ✅ | 세션 ID |
| user_prompt | TEXT | | | ✅ | 사용자 입력 프롬프트 |
| ai_response | TEXT | | | ✅ | AI의 응답 |
| result_type | VARCHAR(50) | | | | 결과 유형 (text, image, 3d, 4d) |
| result_path | VARCHAR(255) | | | | 결과 파일 경로 (이미지, 3D 모델, 4D 애니메이션 등) |
| response_time | FLOAT | | | | AI 응답 생성에 걸린 시간 (초 단위) |
| created_at | TIMESTAMP | | | ✅ | 프롬프트 생성 시간 |

### 4. Asset_library (에셋 라이브러리)
| 필드명 | 데이터 타입 | PK | FK | Not Null | 설명 |
|--------|-------------|----|----|----------|------|
| lib_id | UUID | ✅ | | ✅ | 라이브러리 고유 ID |
| user_id | UUID | | users | ✅ | 업로더 ID |
| title | VARCHAR(200) | | | ✅ | 자료 제목 |
| summary | TEXT | | | | 자료 요약 |
| category | VARCHAR(100) | | | | 카테고리 |
| lib_name | VARCHAR(255) | | | | 원본 파일명 저장용 |
| pdf_path | VARCHAR(255) | | | | PDF 파일 경로 (S3 URL) |
| img_path | VARCHAR(255) | | | | 이미지 경로 (S3 URL 또는 Unsplash URL) |
| upload_date | DATE | | | | 업로드 날짜 |
| likes | INTEGER | | | | 좋아요 수 |
| comment_count | INTEGER | | | | 댓글 수 |
| created_at | TIMESTAMP | | | ✅ | 업로드 시간 |
| updated_at | TIMESTAMP | | | | 수정 시간 |

**변경사항:**
- ❌ **제거**: `documents` 필드 (FileField) - S3 업로드로 대체
- ❌ **제거**: `cover_photo` 필드 (ImageField) - S3 업로드로 대체  
- ✅ **추가**: `lib_name` 필드 - 원본 파일명 저장용

### 5. Library_comments (라이브러리 댓글)
| 필드명 | 데이터 타입 | PK | FK | Not Null | 설명 |
|--------|-------------|----|----|----------|------|
| comment_id | UUID | ✅ | | ✅ | 댓글 고유 ID |
| asset_library | UUID | | asset_library | ✅ | 대상 라이브러리 ID |
| user_id | UUID | | users | ✅ | 댓글 작성자 ID |
| comments | TEXT | | | ✅ | 댓글 내용 |
| likes | INTEGER | | | | 좋아요 수 |
| created_at | TIMESTAMP | | | ✅ | 작성 시간 |
| updated_at | TIMESTAMP | | | | 수정 시간 |

**변경사항:**
- ❌ **제거**: `username` 필드 - `user.user_name`으로 대체
- ❌ **제거**: `user_liked` 필드 - 별도 좋아요 테이블로 관리
- ✅ **변경**: `lib_id` → `asset_library` (ForeignKey 필드명 변경)

### 6. Insight_trends (인사이트 트렌드)
| 필드명 | 데이터 타입 | PK | FK | Not Null | 설명 |
|--------|-------------|----|----|----------|------|
| car_model_id | UUID | ✅ | | ✅ | 차량 모델 고유 ID |
| car_name | VARCHAR(100) | | | ✅ | 차량 이름 |
| type | VARCHAR(50) | | | | 차종 (sedan, suv, ev, hybrid) |
| release_year | INTEGER | | | | 출시 연도 |
| model_3d_path | VARCHAR(255) | | | | 3D GLB 파일 경로 (S3 URL 또는 로컬 경로) |
| created_at | TIMESTAMP | | | ✅ | 생성 시간 |

### 7. Engineering_spec (공학적 스펙)
| 필드명 | 데이터 타입 | PK | FK | Not Null | 설명 |
|--------|-------------|----|----|----------|------|
| spec_id | UUID | ✅ | | ✅ | 스펙 고유 ID |
| car_model_id | UUID | | insight_trends | ✅ | 차량 모델 ID |
| 전장 | VARCHAR(20) | | | | 차량 전장 (mm) |
| 전폭 | VARCHAR(20) | | | | 차량 전폭 (mm) |
| 전고 | VARCHAR(20) | | | | 차량 전고 (mm) |
| 축거 | VARCHAR(20) | | | | 휠베이스 (mm) |
| 승차정원 | VARCHAR(10) | | | | 승차 인원 |
| 공차중량 | VARCHAR(20) | | | | 차량 무게 (kg) |
| created_at | TIMESTAMP | | | ✅ | 생성 시간 |

### 8. User_review (사용자 리뷰)
| 필드명 | 데이터 타입 | PK | FK | Not Null | 설명 |
|--------|-------------|----|----|----------|------|
| review_id | UUID | ✅ | | ✅ | 리뷰 고유 ID |
| car_model_id | UUID | | insight_trends | ✅ | 차량 모델 ID |
| data_id | VARCHAR(50) | | | | 데이터 식별자 |
| car_name | VARCHAR(100) | | | | 차량명 |
| review | TEXT | | | | 리뷰 내용 |
| tags | JSON | | | | 태그 정보 (성능, 공간, 디자인, 승차감) |
| created_at | TIMESTAMP | | | ✅ | 생성 시간 |

### 9. Recent_article (최근 기사)
| 필드명 | 데이터 타입 | PK | FK | Not Null | 설명 |
|--------|-------------|----|----|----------|------|
| article_id | UUID | ✅ | | ✅ | 기사 고유 ID |
| car_model_id | UUID | | insight_trends | ✅ | 차량 모델 ID |
| car_name | VARCHAR(100) | | | | 차량명 |
| year | VARCHAR(10) | | | | 연도 |
| explain | TEXT | | | | 기사 내용 |
| created_at | TIMESTAMP | | | ✅ | 생성 시간 |

### 10. Asset_likes (에셋 좋아요)
| 필드명 | 데이터 타입 | PK | FK | Not Null | 설명 |
|--------|-------------|----|----|----------|------|
| like_id | UUID | ✅ | | ✅ | 좋아요 고유 ID |
| asset_library | UUID | | asset_library | ✅ | 라이브러리 ID (lib_id 참조) |
| user | UUID | | users | ✅ | 사용자 ID (user_id 참조) |
| created_at | TIMESTAMP | | | ✅ | 좋아요 시간 |

**특징:**
- **유니크 제약**: `(asset_library, user)` - 한 사용자가 한 에셋에 한 번만 좋아요
- **토글 방식**: 좋아요 추가/제거를 동일한 API로 처리

### 11. Comment_likes (댓글 좋아요)
| 필드명 | 데이터 타입 | PK | FK | Not Null | 설명 |
|--------|-------------|----|----|----------|------|
| like_id | UUID | ✅ | | ✅ | 좋아요 고유 ID |
| comment | UUID | | library_comments | ✅ | 댓글 ID (comment_id 참조) |
| user | UUID | | users | ✅ | 사용자 ID (user_id 참조) |
| created_at | TIMESTAMP | | | ✅ | 좋아요 시간 |

**특징:**
- **유니크 제약**: `(comment, user)` - 한 사용자가 한 댓글에 한 번만 좋아요
- **토글 방식**: 좋아요 추가/제거를 동일한 API로 처리

## 테이블 간 관계

### **사용자 중심 관계**
- **Users** ↔ **Chat_session**: 1:N (한 사용자는 여러 세션 생성 가능)
- **Users** ↔ **Asset_library**: 1:N (사용자별 자산 라이브러리 생성)
- **Users** ↔ **Library_comments**: 1:N (한 사용자가 여러 댓글 작성)
- **Users** ↔ **Asset_likes**: 1:N (한 사용자가 여러 에셋에 좋아요)
- **Users** ↔ **Comment_likes**: 1:N (한 사용자가 여러 댓글에 좋아요)

### **챗봇 시스템 관계**
- **Chat_session** ↔ **Prompt_log & Generated_result**: 1:N (한 세션에 여러 프롬프트와 결과)
- **참고**: Prompt_log와 Generated_result가 통합되어 하나의 테이블로 관리

### **에셋 라이브러리 관계**
- **Asset_library** ↔ **Library_comments**: 1:N (라이브러리 하나에 여러 댓글)
- **Asset_library** ↔ **Asset_likes**: 1:N (에셋 하나에 여러 좋아요)
- **Library_comments** ↔ **Comment_likes**: 1:N (댓글 하나에 여러 좋아요)

**API 엔드포인트:**
- **댓글 관리**: `GET/POST /library/assets/{lib_id}/comments/`
- **댓글 상세**: `GET/PUT/DELETE /library/comments/{comment_id}/`
- **에셋 좋아요**: `POST /library/assets/{lib_id}/like/`
- **댓글 좋아요**: `POST /library/comments/{comment_id}/like/`

### **인사이트 트렌드 관계**
- **Insight_trends** ↔ **Engineering_spec**: 1:N (차량 모델별 공학적 스펙)
- **Insight_trends** ↔ **User_review**: 1:N (차량 모델별 사용자 리뷰)
- **Insight_trends** ↔ **Recent_article**: 1:N (차량 모델별 최근 기사)
- **3D 모델 지원**: model_3d_path를 통한 Three.js 3D 뷰어 연동
- **외부 데이터 소스**: hyundai_car_reviews.json, hyundai_car_history.json 활용

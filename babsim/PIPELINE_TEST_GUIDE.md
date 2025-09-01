# BABSIM Pipeline 테스트 가이드

## 🚀 테스트 실행 전 준비사항

### 1. 환경 설정 파일 생성

`.env` 파일을 `babsim/` 디렉토리에 생성하세요:

```bash
# .env 파일 생성
touch babsim/.env
```

`.env` 파일에 다음 내용을 추가하세요:

```env
# Django 설정
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# 데이터베이스 설정
DB_NAME=babsim_db
DB_USER=babsim_user
DB_PASSWORD=babsim_password
DB_HOST=postgres
DB_PORT=5432

# Qdrant 설정
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_PORT_REST=6333
QDRANT_COLLECTION=babsim_rag_db

# Inference 서버 설정
INFERENCE_SERVER_URL=http://inference-server:8001

# 모델 설정
EXAONE_MODEL_PATH=/app/models/exaone_4.0_1.2b
EMBEDDING_MODEL_NAME=BAAI/bge-m3

# 기타 설정
CURRENT_MODEL_FOLDER_NAME=exaone_4.0_1.2b
```

### 2. 모델 파일 준비

`babsim/models/` 디렉토리에 Exaone 모델이 있어야 합니다:

```bash
# 모델 디렉토리 구조 확인
ls -la babsim/models/
# exaone_4.0_1.2b/ 디렉토리가 있어야 함
```

### 3. Python 의존성 설치

```bash
cd babsim
pip install -r requirements.txt
```

### 4. Docker 서비스 실행

```bash
# Docker Compose로 모든 서비스 실행
docker compose up -d

# 또는 특정 서비스만 실행
docker compose up -d postgres qdrant inference-server
```

### 5. 서비스 상태 확인

```bash
# 모든 서비스 상태 확인
docker compose ps

# 로그 확인
docker compose logs inference-server
docker compose logs qdrant
docker compose logs postgres
```

### 6. 데이터베이스 마이그레이션

```bash
# Django 마이그레이션 실행
python manage.py makemigrations
python manage.py migrate

# 또는 Docker 컨테이너 내에서 실행
docker compose exec django_gunicorn python manage.py migrate
```

### 7. Vector DB 초기화 (필요시)

```bash
# Vector DB 초기화 스크립트 실행 (필요시)
python text_data/init_vectorDB.py
```

## 🧪 테스트 실행

### 기본 테스트 실행

```bash
cd babsim
python test_pipeline_complete.py
```

### 단계별 테스트

테스트는 다음 순서로 진행됩니다:

1. **설정 일관성 테스트** - JJACKLETTE와 Pipeline 설정 비교
2. **Embedding 모델 테스트** - BAAI/bge-m3 모델 로딩 및 임베딩 생성
3. **Pipeline 컴포넌트 테스트** - 모든 컴포넌트 import 확인
4. **Pipeline 통합 테스트** - 실제 메시지 처리 테스트
5. **채팅 세션 테스트** - Django 모델 연동 확인
6. **대화형 테스트** (선택사항) - 실시간 채팅 테스트

## 🔧 문제 해결

### 일반적인 문제들

#### 1. Inference 서버 연결 실패
```bash
# Inference 서버 상태 확인
curl http://localhost:8001/health

# 로그 확인
docker-compose logs inference-server
```

#### 2. Qdrant 연결 실패
```bash
# Qdrant 상태 확인
curl http://localhost:6333/collections

# 로그 확인
docker-compose logs qdrant
```

#### 3. 데이터베이스 연결 실패
```bash
# PostgreSQL 상태 확인
docker compose exec postgres psql -U babsim_user -d babsim_db -c "SELECT 1;"

# 로그 확인
docker compose logs postgres
```

#### 4. 모델 파일 없음
```bash
# 모델 디렉토리 확인
ls -la models/exaone_4.0_1.2b/

# 모델 파일 다운로드 (필요시)
# Exaone 모델을 models/ 디렉토리에 다운로드
```

### 디버깅 모드

```bash
# 상세한 로그와 함께 테스트 실행
python test_pipeline_complete.py 2>&1 | tee test_log.txt
```

## 📊 테스트 결과 해석

### 성공적인 테스트 결과
```
🚗 BABSIM Pipeline 통합 테스트
============================================================

📋 설정 일관성
------------------------------
✅ LLM 모델 설정 일치
✅ Embedding 모델 설정 일치
✅ Qdrant 설정 일치

📋 Embedding 모델
------------------------------
✅ Embedding 모델 로딩 성공
   모델: BAAI/bge-m3
   임베딩 차원: 1024

📋 Pipeline 컴포넌트
------------------------------
✅ Pipeline 서비스 초기화 성공
✅ 모든 Pipeline 컴포넌트 import 성공

📊 테스트 결과 요약
==================================================
설정 일관성: ✅ 통과
Embedding 모델: ✅ 통과
Pipeline 컴포넌트: ✅ 통과
Pipeline 통합: ✅ 통과
채팅 세션: ✅ 통과

총 5개 테스트 중 5개 통과

🎉 모든 테스트 통과! Pipeline이 정상적으로 작동합니다.
```

### 실패 시 확인사항

1. **Docker 서비스 상태 확인**
2. **환경변수 설정 확인**
3. **모델 파일 존재 확인**
4. **네트워크 연결 확인**
5. **로그 파일 확인**

## 🚀 다음 단계

테스트가 성공하면:

1. **Django 서버 실행**: `python manage.py runserver`
2. **API 테스트**: Postman이나 curl로 API 엔드포인트 테스트
3. **프론트엔드 연동**: React 앱과 연동 테스트

## 📝 참고사항

- 테스트는 로컬 환경에서 실행됩니다
- Docker 서비스들이 실행 중이어야 합니다
- 모델 파일이 올바른 위치에 있어야 합니다
- 데이터베이스 마이그레이션이 완료되어야 합니다

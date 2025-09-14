# EC2 + RDS 배포 설정 가이드

## 1. RDS PostgreSQL 설정

### RDS 인스턴스 생성
- **엔진**: PostgreSQL
- **버전**: 15.x
- **인스턴스 클래스**: db.t3.micro (테스트용) 또는 db.t3.small (프로덕션용)
- **스토리지**: 20GB 이상
- **보안 그룹**: EC2와 같은 보안 그룹 또는 EC2에서 접근 가능하도록 설정

### 데이터베이스 생성
```sql
-- 메인 애플리케이션 DB
CREATE DATABASE babsim_db;

-- Airflow DB
CREATE DATABASE airflow_db;
```

## 2. 환경변수 설정 (.env 파일)

```bash
# Django 설정
SECRET_KEY=your-secret-key-here-change-this-in-production
DEBUG=False
ALLOWED_HOSTS=localhost,52.62.239.147.nip.io

# RDS 데이터베이스 설정
POSTGRES_DB=babsim_db
POSTGRES_USER=your-rds-username
POSTGRES_PASSWORD=your-rds-password
POSTGRES_HOST=your-rds-endpoint.region.rds.amazonaws.com
POSTGRES_PORT=5432

# Qdrant 설정
QDRANT_HOST=qdrant
QDRANT_PORT=6334
QDRANT_PORT_REST=6333

# 프론트엔드 URL
FRONTEND_URL=http://52.62.239.147.nip.io

# 추론 서버 URL
INFERENCE_SERVER_URL=http://inference-server:8001

# AWS S3 설정
ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket-name
AWS_S3_REGION_NAME=ap-northeast-2

# RunPod vLLM API 설정
VLLM_API_URL=your-runpod-vllm-api-url
VLLM_MODEL_NAME=your-model-name

# Google OAuth 설정
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
```

## 3. EC2 배포 명령어

```bash
# 1. 프로젝트 클론
git clone <your-repository-url>
cd babsim

# 2. .env 파일 생성 (위의 내용으로)
nano .env

# 3. React 빌드
cd react
npm install
npm run build
cd ..

# 4. Docker 서비스 시작
docker-compose up -d --build

# 5. 데이터베이스 마이그레이션
docker-compose exec django_gunicorn python manage.py migrate

# 6. 초기 데이터 임포트
docker-compose exec django_gunicorn python manage.py import_data

# 7. 정적 파일 수집
docker-compose exec django_gunicorn python manage.py collectstatic --noinput
```

## 4. RDS 연결 확인

```bash
# RDS 연결 테스트
docker-compose exec django_gunicorn python manage.py dbshell

# 또는 Django 쉘에서 확인
docker-compose exec django_gunicorn python manage.py shell
```

## 5. 보안 그룹 설정

### EC2 보안 그룹 (Inbound Rules)
- **Type**: HTTP, **Port**: 80, **Source**: 0.0.0.0/0
- **Type**: Custom TCP, **Port**: 8080, **Source**: 0.0.0.0/0 (Airflow)
- **Type**: Custom TCP, **Port**: 6333, **Source**: 0.0.0.0/0 (Qdrant)

### RDS 보안 그룹 (Inbound Rules)
- **Type**: PostgreSQL, **Port**: 5432, **Source**: EC2 보안 그룹 ID

## 6. 서비스 확인

- **메인 사이트**: http://52.62.239.147.nip.io
- **Airflow**: http://52.62.239.147.nip.io:8080
- **Qdrant**: http://52.62.239.147.nip.io:6333

## 7. 문제 해결

### RDS 연결 실패 시
1. RDS 보안 그룹에서 EC2 보안 그룹 허용 확인
2. RDS 엔드포인트 URL 확인
3. 데이터베이스 이름과 사용자명 확인

### 서비스 재시작
```bash
# 전체 재시작
docker-compose restart

# 특정 서비스만 재시작
docker-compose restart django_gunicorn
```

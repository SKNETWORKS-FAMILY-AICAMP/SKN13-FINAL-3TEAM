# Dockerfile

# Python 기반 이미지 사용
FROM python:3.10-slim-bullseye

# 환경 변수 설정
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=config.settings

# 필요한 시스템 패키지 설치 (여기서는 PostgreSQL client 제거)
# 모델이 다른 빌드 도구를 필요로 한다면 추가해야 합니다.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . /app/
# COPY JJACKLETTE/models_ai/exaone_4.0_1.2b /app/JJACKLETTE/models/exaone_4.0_1.2b
# --> Dockerfile에서 이미지 띄울 때 모델 크기가 부담스러울 수 있어 docker-compose에 추가
# Nginx 설정을 위한 빌드 단계 (optional, if you want to put nginx inside same container)
# 일반적으로 Nginx는 별도 컨테이너로 분리합니다. 아래는 참고용.
# RUN apt-get update && apt-get install -y nginx
# COPY nginx.conf /etc/nginx/sites-available/default
# RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"] # If Nginx is separate

# Gunicorn을 통한 Django 애플리케이션 실행 명령어
# Nginx와 Gunicorn을 별도 컨테이너로 분리하므로, 이 컨테이너는 Gunicorn만 실행합니다.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]

# Frontend (React) 빌드 결과물을 Django가 서빙하는 경우 (선택 사항)
# 일반적으로는 Nginx가 직접 React 빌드 결과물을 서빙합니다.
# COPY frontend/build /app/staticfiles_react/
# RUN python manage.py collectstatic --noinput
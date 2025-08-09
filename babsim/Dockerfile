# Python 기반 이미지 사용
FROM python:3.10-slim-bookworm

# 환경 변수 설정
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=config.settings

# 필요한 시스템 패키지 설치 (PostgreSQL client 등)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    gcc \
    # Add other necessary packages for your Python libraries if any
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . /app/

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
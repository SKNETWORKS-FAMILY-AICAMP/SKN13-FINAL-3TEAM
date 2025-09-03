# Python 3.10을 기반으로 이미지를 생성합니다.
FROM python:3.10-slim

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리를 설정합니다.
WORKDIR /embedding_server

# 필요한 라이브러리 목록을 복사합니다.
COPY requirements.txt .

# 라이브러리를 설치합니다.
# --no-cache-dir 옵션은 이미지 크기를 줄이는 데 도움이 됩니다.
RUN pip install --no-cache-dir -r requirements.txt

# 빌드 시점에 모델을 다운로드하여 이미지에 포함시킵니다.
COPY download.py .
RUN python download.py

# API 서버 코드를 복사합니다.
COPY main.py .

# 8000번 포트를 외부에 노출합니다.
EXPOSE 8000

# 서버를 실행합니다.
CMD uvicorn main:app --host 0.0.0.0 --port 8000
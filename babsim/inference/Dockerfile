# GPU 사용을 위해 NVIDIA CUDA 이미지를 기반으로 합니다.
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Python 및 기본 도구 설치
RUN apt-get update && apt-get install -y --no-install-recommends python3.10 python3-pip && rm -rf /var/lib/apt/lists/*
RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app

COPY ./inference/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY ./inference /app/
# 로컬에 다운받은 모델 폴더를 컨테이너 안으로 복사
COPY ./models /app/models 

# FastAPI 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

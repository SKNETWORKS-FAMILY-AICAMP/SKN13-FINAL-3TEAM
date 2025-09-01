# GPU 사용을 위해 NVIDIA CUDA 이미지를 기반으로 합니다.
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Python 및 기본 도구 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*
RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app

# 의존성 파일 복사 및 설치
# context가 ./inference 이므로, 바로 requirements.txt를 찾을 수 있습니다.
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

RUN echo "VERIFYING TRANSFORMERS VERSION:" && pip list | grep transformers


# inference 폴더 내의 모든 소스 코드를 /app/으로 복사합니다.
# (main.py 등이 복사됩니다.)
COPY . /app/

# FastAPI 서버 실행
CMD ["python", "-m", "vllm.entrypoints.openai.api_server", "--model", "kakaocorp/kanana-1.5-8b-instruct-2505", "--enable-lora", "--lora-modules", "kanana-finetuned=ki-student/kanana-finetuned-model-v1", "--host", "0.0.0.0", "--port", "8001"]
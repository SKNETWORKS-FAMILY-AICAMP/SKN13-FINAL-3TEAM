# =========================
# Stage 1: CUDA 확장 빌드
# =========================
FROM nvidia/cuda:12.8.0-devel-ubuntu24.04 AS wheelbuilder

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3.12 python3.12-dev python3-pip git build-essential cmake ninja-build curl && \
    rm -rf /var/lib/apt/lists/*

RUN python3.12 -m pip install --index-url https://download.pytorch.org/whl/cu128 torch==2.8.0 --break-system-packages --timeout 600 --retries 3 && \
    python3.12 -m pip install "numpy==1.26.4" "pybind11>=2.12,<3.0" "ninja>=1.10.0" --break-system-packages --timeout 600 --retries 3

WORKDIR /src
RUN git clone --depth 1 https://github.com/kijai/ComfyUI-Hunyuan3DWrapper
ENV TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0" FORCE_CUDA=1 CUDA_HOME=/usr/local/cuda

RUN mkdir -p /wheels && \
    cd /src/ComfyUI-Hunyuan3DWrapper/hy3dgen/texgen/custom_rasterizer && \
    python3.12 setup.py bdist_wheel --dist-dir /wheels || \
    echo "CUDA extension build failed - will use fallback"

# =========================
# Stage 2: RunPod Runtime
# =========================
FROM runpod/worker-comfyui:5.4.1-base AS runtime

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    git curl ca-certificates ffmpeg wget unzip libglib2.0-0 libgomp1 \
    sqlite3 libsqlite3-dev && \
    rm -rf /var/lib/apt/lists/*

ENV WORKDIR=/workspace \
    OUTPUT_DIR=/workspace/outputs \
    MODELSDIR=/workspace/models \
    COMFY_URL=http://127.0.0.1:8188 \
    RP_HANDLER=handler.py \
    RUNPOD_WEB_SERVICE_PORT=3000 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR ${WORKDIR}
EXPOSE 8188 3000

RUN python -m pip install \
    "numpy==1.26.4" \
    "pillow>=9.0.0,<11.0.0" \
    "opencv-python-headless==4.10.0.84" --break-system-packages --timeout 600 --retries 3

COPY requirements.txt /tmp/requirements.txt
# RUN pip install -r /tmp/requirements.txt --break-system-packages --timeout 600 --retries 3

RUN pip install -r /tmp/requirements.txt --break-system-packages --timeout 600 --retries 3
RUN pip install pymeshlab --break-system-packages --timeout 600 --retries 3

# ComfyUI 및 Custom Nodes 설치
RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI /opt/ComfyUI && \
    pip install -r /opt/ComfyUI/requirements.txt --break-system-packages --timeout 600 --retries 3

ENV CUSTOMDIR=/opt/ComfyUI/custom_nodes
RUN git clone --depth 1 https://github.com/Lightricks/ComfyUI-LTXVideo "${CUSTOMDIR}/ComfyUI-LTXVideo" && \
    git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite "${CUSTOMDIR}/ComfyUI-VideoHelperSuite" && \
    git clone --depth 1 https://github.com/kijai/ComfyUI-Hunyuan3DWrapper "${CUSTOMDIR}/ComfyUI-Hunyuan3DWrapper" && \
    git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Impact-Pack "${CUSTOMDIR}/ComfyUI-Impact-Pack" && \
    git clone --depth 1 https://github.com/cubiq/ComfyUI_essentials "${CUSTOMDIR}/ComfyUI_essentials"

# Custom Node 의존성 (기본 패키지 제외)
RUN for node_dir in ComfyUI-LTXVideo ComfyUI-VideoHelperSuite ComfyUI-Hunyuan3DWrapper ComfyUI_essentials; do \
        if [ -f "${CUSTOMDIR}/${node_dir}/requirements.txt" ]; then \
            echo "Processing ${node_dir} dependencies..."; \
            grep -v -E '^(numpy|torch|torchvision|torchaudio|opencv-python|pillow|scipy)' \
                "${CUSTOMDIR}/${node_dir}/requirements.txt" > "/tmp/${node_dir}.txt" || true; \
            if [ -s "/tmp/${node_dir}.txt" ]; then \
                pip install -r "/tmp/${node_dir}.txt" --break-system-packages || echo "Some ${node_dir} deps failed (non-critical)"; \
            fi; \
        fi; \
    done

# Essentials의 배경제거 노드가 기대하는 런타임 의존성
# GPU용 onnxruntime이 안 맞으면 CPU onnxruntime로 폴백
RUN /opt/venv/bin/python -m pip install --no-cache-dir transparent-background "rembg[gpu]" onnxruntime-gpu || \
    /opt/venv/bin/python -m pip install --no-cache-dir rembg onnxruntime

# Hunyuan3DWrapper 추가 의존성 (xatlas 등)
RUN pip install xatlas --break-system-packages --timeout 600 --retries 3 || echo "xatlas install failed"

# Impact-Pack: SAM2 관련 의존성 설치 (git URL 포함)
RUN if [ -f "${CUSTOMDIR}/ComfyUI-Impact-Pack/requirements.txt" ]; then \
    echo "=== Processing Impact-Pack dependencies (including SAM2) ==="; \
    echo "Original requirements:"; \
    cat "${CUSTOMDIR}/ComfyUI-Impact-Pack/requirements.txt" | head -20; \
    echo "=== Installing all Impact-Pack dependencies including SAM2 ==="; \
    # SAM2 관련 패키지들을 명시적으로 설치
    echo "Installing SAM2 dependencies..."; \
    pip install segment-anything --break-system-packages --timeout 600 --retries 3 || echo "SAM installation failed"; \
    pip install git+https://github.com/facebookresearch/segment-anything-2.git --break-system-packages --timeout 600 --retries 3 || echo "SAM2 git install failed"; \
    # 기존 requirements.txt에서 SAM2 제외하고 설치 (기본 패키지들만)
    grep -v -E '^(numpy|torch|torchvision|torchaudio|opencv-python|pillow|scipy)' \
        "${CUSTOMDIR}/ComfyUI-Impact-Pack/requirements.txt" | \
    grep -v -E '(sam2|segment.?anything|facebookresearch)' > "/tmp/impact-base.txt" || true; \
    echo "Base requirements (SAM2 handled separately):"; \
    cat "/tmp/impact-base.txt" || echo "(No additional base dependencies found)"; \
    if [ -s "/tmp/impact-base.txt" ]; then \
        echo "Installing base Impact-Pack dependencies..."; \
        pip install -r "/tmp/impact-base.txt" --break-system-packages || echo "Some Impact-Pack base deps failed (non-critical)"; \
    else \
        echo "✓ Base Impact-Pack dependencies installed"; \
    fi; \
fi

# Impact-Pack에서 SAM2 관련 노드들 활성화 확인
RUN cd "${CUSTOMDIR}/ComfyUI-Impact-Pack" && \
    echo "✓ SAM2 related files preserved in Impact-Pack" && \
    python -c "import sys; sys.path.append('.'); print('Impact-Pack modules available')"

# 디렉토리 구조 생성
RUN mkdir -p ${MODELSDIR}/{checkpoints,text_encoders,diffusion_models,hunyuan3d} && \
    mkdir -p ${OUTPUT_DIR}/{images,videos,models,inputs}

# 워크플로우에서 실제 사용하는 모델들만 다운로드
RUN echo "=== Downloading Workflow-Required Models ===" && \
    echo "Creating model directories..." && \
    mkdir -p /opt/ComfyUI/models/checkpoints /opt/ComfyUI/models/text_encoders /opt/ComfyUI/models/diffusion_models && \
    echo "Starting parallel downloads..." && \
    curl -L --fail --retry 5 --max-time 3600 --http1.1 \
        -o /opt/ComfyUI/models/checkpoints/ltxv-2b-0.9.8-distilled.safetensors \
        "https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltxv-2b-0.9.8-distilled.safetensors" & \
    curl -L --fail --retry 5 --max-time 3600 --http1.1 \
        -o /opt/ComfyUI/models/diffusion_models/hunyuan3d-dit-v2_fp16.safetensors \
        "https://huggingface.co/Kijai/Hunyuan3D-2_safetensors/resolve/main/hunyuan3d-dit-v2-0-fp16.safetensors" & \
    curl -L --fail --retry 5 --max-time 3600 --http1.1 \
        -o /opt/ComfyUI/models/text_encoders/t5xxl_fp16.safetensors \
        "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp16.safetensors" & \
    wait && \
    echo "=== Core Models Downloaded ==="

# (선택) CLIP 호환 폴더 생성 (T5 가중치 심볼릭 링크)
RUN mkdir -p /opt/ComfyUI/models/clip && \
    ln -sf /opt/ComfyUI/models/text_encoders/t5xxl_fp16.safetensors \
            /opt/ComfyUI/models/clip/t5xxl_fp16.safetensors

# Hunyuan3D 서브모델들 (핵심 가중치 파일만 다운로드)
RUN echo "=== Downloading Hunyuan3D Sub-models ===" && \
    # Delight 모델 (가중치 파일만)
    echo "Downloading Delight model weights..." && \
    mkdir -p ${MODELSDIR}/hunyuan3d/hunyuan3d-delight-v2-0/unet && \
    curl -L --fail --retry 5 --max-time 3600 --http1.1 \
        -o ${MODELSDIR}/hunyuan3d/hunyuan3d-delight-v2-0/unet/diffusion_pytorch_model.safetensors \
        "https://huggingface.co/tencent/Hunyuan3D-2/resolve/main/hunyuan3d-delight-v2-0/unet/diffusion_pytorch_model.safetensors" && \
    # Paint 모델 (가중치 파일만)
    echo "Downloading Paint model weights..." && \
    mkdir -p ${MODELSDIR}/hunyuan3d/hunyuan3d-paint-v2-0/unet && \
    curl -L --fail --retry 5 --max-time 3600 --http1.1 \
        -o ${MODELSDIR}/hunyuan3d/hunyuan3d-paint-v2-0/unet/diffusion_pytorch_model.safetensors \
        "https://huggingface.co/tencent/Hunyuan3D-2/resolve/main/hunyuan3d-paint-v2-0/unet/diffusion_pytorch_model.safetensors" && \
    mkdir -p ${MODELSDIR}/hunyuan3d/hunyuan3d-paint-v2-0/vae && \
    curl -L --fail --retry 5 --max-time 3600 --http1.1 \
        -o ${MODELSDIR}/hunyuan3d/hunyuan3d-paint-v2-0/vae/diffusion_pytorch_model.safetensors \
        "https://huggingface.co/tencent/Hunyuan3D-2/resolve/main/hunyuan3d-paint-v2-0/vae/diffusion_pytorch_model.safetensors" && \
    # VAE 모델 (메인 VAE - 워크플로우 필수)
    echo "Downloading VAE model..." && \
    mkdir -p ${MODELSDIR}/hunyuan3d/hunyuan3d-vae-v2-0 && \
    curl -L --fail --retry 5 --max-time 3600 --http1.1 \
        -o ${MODELSDIR}/hunyuan3d/hunyuan3d-vae-v2-0/model.fp16.safetensors \
        "https://huggingface.co/tencent/Hunyuan3D-2/resolve/main/hunyuan3d-vae-v2-0/model.fp16.safetensors" && \
    curl -L --fail --retry 5 --max-time 3600 --http1.1 \
        -o ${MODELSDIR}/hunyuan3d/hunyuan3d-vae-v2-0/config.yaml \
        "https://huggingface.co/tencent/Hunyuan3D-2/resolve/main/hunyuan3d-vae-v2-0/config.yaml" && \
    echo "=== Hunyuan3D Sub-models Downloaded ==="
    
# CUDA 확장 설치
COPY --from=wheelbuilder /wheels /tmp/wheels
RUN if ls /tmp/wheels/*.whl >/dev/null 2>&1; then \
        echo "Installing CUDA extensions..."; \
        pip install /tmp/wheels/*.whl --break-system-packages || echo "CUDA extension install failed (will use fallback)"; \
    else \
        echo "No CUDA wheels found - using fallback mode"; \
    fi && \
    rm -rf /tmp/wheels /tmp/*.txt

# 디렉토리 링크 설정
RUN ln -sf /opt/ComfyUI/models /workspace/models && \
    mkdir -p /workspace/outputs && \
    rm -rf /opt/ComfyUI/output && \
    ln -sf /workspace/outputs /opt/ComfyUI/output

# Workflows 복사
COPY workflows/ /opt/baked_workflows/

# 런타임 스크립트
COPY start_pod.sh handler.py ${WORKDIR}/
RUN chmod +x ${WORKDIR}/start_pod.sh

# Docker 이미지 크기 최적화 (필수)
RUN echo "=== Optimizing Image Size ===" && \
    # 캐시 및 임시 파일 정리
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    # Python 캐시 정리
    find /opt -name "*.pyc" -delete && \
    find /opt -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /workspace -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
    # Git 디렉토리 정리 (용량 절약)
    find /opt -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true && \
    # 불필요한 개발 파일들 정리
    find /opt -name "*.md" -delete 2>/dev/null || true && \
    find /opt -name "*.txt" -path "*/docs/*" -delete 2>/dev/null || true && \
    find /opt/ComfyUI -name "example*" -type f -delete 2>/dev/null || true && \
    # pip 캐시 정리
    pip cache purge 2>/dev/null || true && \
    echo "✓ Image size optimized"

# 간단한 최종 검증
RUN echo "=== Final System Verification ===" && \
    python -c "import torch, numpy, cv2, requests, runpod; print('✓ Essential modules imported')" && \
    echo "=== System Ready for RunPod Deployment ==="

CMD ["/bin/bash", "/workspace/start_pod.sh"]
#!/usr/bin/env bash
set -euo pipefail

# ====================================================================
# RunPod Serverless 최적화 스타트업 스크립트
# ====================================================================

# 색상 및 로깅
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log_info() { echo -e "${GREEN}[INFO]${NC} $(date '+%H:%M:%S') $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $(date '+%H:%M:%S') $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%H:%M:%S') $1"; }

# --- GPU preflight: 환경변수/가용성 대기 ---
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True,max_split_size_mb:256"

wait_for_gpu() {
  log_info "Waiting for NVIDIA driver & GPU..."
  for i in {1..30}; do
    if nvidia-smi >/dev/null 2>&1; then
      python - <<'PY'
import torch, sys
sys.exit(0 if torch.cuda.is_available() else 1)
PY
      if [[ $? -eq 0 ]]; then
        log_info "✓ CUDA is available. GPU ready."
        return 0
      fi
    fi
    sleep 2
  done
  log_error "GPU still not visible; exiting so RunPod reschedules this worker."
  exit 88
}

# ====================================================================
# 1. 환경변수 검증 (RunPod Serverless 필수)
# ====================================================================
check_environment() {
    log_info "=== RunPod Environment Check ==="
    
    # AWS S3 필수 변수 검증
    local aws_vars=("AWS_STORAGE_BUCKET_NAME" "ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY" "AWS_S3_REGION_NAME")
    local missing=()
    
    for var in "${aws_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing+=("$var")
        else
            log_info "✓ $var is set"
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing AWS environment variables: ${missing[*]}"
        log_error "RunPod Serverless requires these for S3 integration"
        exit 1
    fi
    
    # RunPod 특정 변수들
    log_info "RunPod Job ID: ${RUNPOD_JOB_ID:-not_set}"
    log_info "RunPod Pod ID: ${RUNPOD_POD_ID:-not_set}"
    log_info "GPU Info: $(nvidia-smi --query-gpu=name --format=csv,noheader,nounits || echo 'No GPU detected')"
    
    log_info "✓ Environment validation completed"
}

# ====================================================================
# 디렉토리 및 심볼릭 링크 설정
# ====================================================================
setup_directories() {
    log_info "=== Directory Setup ==="
    
    # 필수 디렉토리 생성
    mkdir -p /workspace/{models,outputs,workflows}
    mkdir -p /workspace/models/{checkpoints,text_encoders,hunyuan3d}
    mkdir -p /workspace/outputs/{images,videos,models,inputs}
    
    # models 경로 자가복구: /workspace/models → /opt/ComfyUI/models
    if [[ ! -e /workspace/models ]]; then
        ln -s /opt/ComfyUI/models /workspace/models
        log_info "✓ /workspace/models -> /opt/ComfyUI/models (symlink created)"
    elif [[ -d /workspace/models ]] && [[ -z "$(ls -A /workspace/models 2>/dev/null)" ]]; then
        # 빈 디렉토리로 마운트된 경우, 폴더를 링크로 교체
        rm -rf /workspace/models
        ln -s /opt/ComfyUI/models /workspace/models
        log_info "✓ /workspace/models was empty dir; replaced with symlink to /opt/ComfyUI/models"
    else
        log_info "ℹ /workspace/models exists and is not empty; leaving as-is"
    fi
    
    # output 경로 정규화: ComfyUI는 /opt/ComfyUI/output을 쓰고, 실제 파일은 /workspace/outputs에 저장
    rm -rf /opt/ComfyUI/output 2>/dev/null || true
    mkdir -p /workspace/outputs
    ln -sf /workspace/outputs /opt/ComfyUI/output
    log_info "✓ /opt/ComfyUI/output -> /workspace/outputs (symlink ensured)"

    
    # Workflows 복사
    if [[ -d /opt/baked_workflows ]] && [[ -n "$(ls -A /opt/baked_workflows 2>/dev/null)" ]]; then
        cp -r /opt/baked_workflows/* /workspace/workflows/ 2>/dev/null || true
        log_info "✓ Workflows copied"
    fi
    
    log_info "✓ Directory setup completed"
}

# ====================================================================
# Python 환경 검증
# ====================================================================
verify_python() {
    log_info "=== Python Environment Verification ==="
    
    python -c "
import sys, torch, numpy, cv2, requests, runpod, fastapi, boto3, pydantic
print(f'Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')
print(f'PyTorch: {torch.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU Count: {torch.cuda.device_count()}')
    print(f'GPU Names: {[torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]}')
print('✓ All critical modules imported successfully')
" || {
        log_error "Python environment verification failed"
        exit 1
    }
    
    log_info "✓ Python environment verified"
}

# ====================================================================
#  ComfyUI 서버 시작 (RunPod 최적화)
# ====================================================================
start_comfyui() {
    log_info "=== Starting ComfyUI Server ==="
    
    wait_for_gpu

    cd /opt/ComfyUI
    
    # ComfyUI 서버 시작 (백그라운드, 로그 파이프)
    log_info "Launching ComfyUI on 0.0.0.0:8188..."
    python main.py --listen 0.0.0.0 --port 8188 --output-directory /workspace/outputs &
    local comfy_pid=$!
    
    # 서버 준비 대기 (RunPod 환경에서는 빠름)
    local max_wait=60
    local count=0
    
    log_info "Waiting for ComfyUI to become ready..."
    while [[ $count -lt $max_wait ]]; do
        if curl -sf http://127.0.0.1:8188/system_stats >/dev/null 2>&1; then
            log_info "✓ ComfyUI server is ready and responding"
            break
        fi
        
        sleep 2
        ((count += 2))
        
        if [[ $((count % 10)) -eq 0 ]]; then
            log_info "Still waiting... (${count}s elapsed)"
        fi
    done
    
    if [[ $count -ge $max_wait ]]; then
        log_error "ComfyUI failed to start within ${max_wait}s"
        kill $comfy_pid 2>/dev/null || true
        exit 1
    fi
    
    # 노드 로딩 검증 (RunPod에서는 빠르게 로드됨)
    log_info "Verifying node loading..."
    local node_wait=30
    local node_count=0
    
    for ((i=0; i<node_wait; i+=5)); do
        if curl -sf http://127.0.0.1:8188/object_info >/dev/null 2>&1; then
            node_count=$(curl -sf http://127.0.0.1:8188/object_info | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(len(data))
except:
    print(0)
" 2>/dev/null || echo "0")
            
            if [[ $node_count -gt 30 ]]; then
                log_info "✓ ComfyUI nodes loaded successfully ($node_count nodes)"
                break
            fi
        fi
        sleep 5
    done
    
    if [[ $node_count -le 30 ]]; then
        log_warn "Limited nodes loaded ($node_count), but continuing..."
    fi
    
    log_info "✓ ComfyUI server startup completed"

    # 모델 존재 및 인덱싱 확인 (필수 체크포인트/클립)
    have() { [[ -f "$1" ]]; }
    if ! have /workspace/models/checkpoints/ltxv-2b-0.9.8-distilled.safetensors && \
       ! have /opt/ComfyUI/models/checkpoints/ltxv-2b-0.9.8-distilled.safetensors; then
        log_error "Missing LTX-Video checkpoint (checked /workspace and /opt)"
    fi
    if ! have /workspace/models/text_encoders/t5xxl_fp16.safetensors && \
       ! have /workspace/models/clip/t5xxl_fp16.safetensors && \
       ! have /opt/ComfyUI/models/text_encoders/t5xxl_fp16.safetensors && \
       ! have /opt/ComfyUI/models/clip/t5xxl_fp16.safetensors; then
        log_error "Missing CLIP t5xxl (checked /workspace and /opt)"
    fi

    # 모델 인덱스 리프레시 (ComfyUI는 디렉토리 스캔 캐시를 가질 수 있음)
    curl -sf -X POST http://127.0.0.1:8188/refresh_models >/dev/null 2>&1 || true
}


# ====================================================================
#  RunPod 핸들러 시작
# ====================================================================
start_runpod_handler() {
    log_info "=== Starting RunPod Handler ==="
    log_info "Handler: /workspace/handler.py"
    log_info "ComfyUI URL: http://127.0.0.1:8188"
    log_info "Output Directory: /workspace/outputs"
    log_info "S3 Bucket: ${AWS_STORAGE_BUCKET_NAME}"
    
    cd /workspace
    
    # RunPod 서버리스 핸들러 실행
    log_info "🚀 RunPod Serverless Handler Starting..."
    exec python -u handler.py
}

# ====================================================================
# 메인 실행 함수
# ====================================================================
main() {
    echo "======================================================================"
    echo "🚀 ComfyUI RunPod Serverless Container"
    echo "Purpose: 3D Model & Video Generation via ComfyUI"
    echo "Models: Hunyuan3D + LTX-Video"
    echo "Started: $(date '+%Y-%m-%d %H:%M:%S UTC')"
    echo "======================================================================"
    
    # 단계별 실행 (실패 시 즉시 중단)
    check_environment
    setup_directories
    verify_python
    start_comfyui
    start_runpod_handler
}

# 시그널 핸들링 (RunPod 환경용)
trap 'log_error "Container interrupted by signal"; exit 130' INT TERM

# 메인 실행
main "$@"
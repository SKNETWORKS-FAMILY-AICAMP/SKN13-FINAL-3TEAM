#!/usr/bin/env bash
set -euo pipefail

# -------- ENV / PATHS --------
WORKDIR="${WORKDIR:-/workspace}"
COMFY_DIR="${WORKDIR}/ComfyUI"
OUTPUT_DIR="${OUTPUT_DIR:-/workspace/outputs}"
MODELSDIR="${MODELSDIR:-/workspace/models}"
PORT="${PORT:-8188}"

echo "[start_pod] WORKDIR=${WORKDIR} OUTPUT_DIR=${OUTPUT_DIR} MODELSDIR=${MODELSDIR}"

# 1) 모델 부트스트랩 (부분 다운로드 + 링크 + 커스텀 확장 빌드)
echo "[start_pod] bootstrap..."
python "${WORKDIR}/bootstrap_models.py"

# 2) ComfyUI 실행
echo "[start_pod] launching ComfyUI..."
cd "${COMFY_DIR}"

# ComfyUI 런타임 옵션
# --listen 0.0.0.0 : 외부 접속 허용
# --port 8188       : 포트
# --output-directory: 결과 파일 기본 위치
# --disable-auto-launch: 브라우저 자동 오픈 끔
# --enable-cors     : REST 호출 편의
PYTHONUNBUFFERED=1 \
python -u main.py \
  --listen 0.0.0.0 \
  --port "${PORT}" \
  --output-directory "${OUTPUT_DIR}" \
  --disable-auto-launch \
  --enable-cors \
  2>&1 | tee "${OUTPUT_DIR}/comfyui.log" &
COMFY_PID=$!

# 3) 헬스체크(포트 열릴 때까지 대기)
echo "[start_pod] waiting for ComfyUI on :${PORT} ..."
for i in {1..120}; do
  if curl -fsS "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
    echo "[start_pod] ComfyUI is up."
    break
  fi
  sleep 2
done

# 4) 포그라운드 유지
echo "[start_pod] tailing logs..."
tail -f "${OUTPUT_DIR}/comfyui.log" &
TAIL_PID=$!

# 안전 종료 핸들링
cleanup() {
  echo "[start_pod] stopping..."
  kill ${COMFY_PID} || true
  kill ${TAIL_PID} || true
}
trap cleanup SIGTERM SIGINT

wait ${COMFY_PID}

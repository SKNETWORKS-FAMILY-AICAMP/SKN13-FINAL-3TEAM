# ===== Base =====
FROM runpod/worker-comfyui:5.4.1-base

# ---- 기본 ENV (Pod/Serverless 공통) ----
ENV WORKDIR=/workspace \
    CUSTOMDIR=/workspace/custom_nodes \
    MODELSDIR=/workspace/models \
    OUTPUT_DIR=/workspace/outputs \
    COMFY_URL=http://127.0.0.1:8188 \
    RP_HANDLER=handler.py \
    RUNPOD_WEB_SERVICE_PORT=3000

# ---- ComfyUI 설치 경로/포트 노출 ----
WORKDIR ${WORKDIR}
EXPOSE 8188 3000

# ---- 필수 디렉토리 ----
RUN mkdir -p ${CUSTOMDIR} ${MODELSDIR} ${OUTPUT_DIR}

ARG COMFY_REF=master
RUN if [ ! -d "${WORKDIR}/ComfyUI" ]; then \
      git clone --depth 1 -b ${COMFY_REF} https://github.com/comfyanonymous/ComfyUI ${WORKDIR}/ComfyUI ; \
    fi

# ===== 커스텀 노드 설치 =====
# 1) LTX-Video (영상 생성)
RUN if [ ! -d "${CUSTOMDIR}/ComfyUI-LTXVideo" ]; then \
      git clone --depth 1 https://github.com/Lightricks/ComfyUI-LTXVideo ${CUSTOMDIR}/ComfyUI-LTXVideo ; \
    fi
# 2) Hunyuan3D Wrapper (2D->3D)
RUN if [ ! -d "${CUSTOMDIR}/ComfyUI-Hunyuan3DWrapper" ]; then \
      git clone --depth 1 https://github.com/kijai/ComfyUI-Hunyuan3DWrapper ${CUSTOMDIR}/ComfyUI-Hunyuan3DWrapper ; \
    fi

# ===== 파이썬 의존성 =====
COPY requirements.txt /tmp/requirements.txt
RUN pip install -U pip wheel setuptools && \
    pip install -r /tmp/requirements.txt

# ===== 런타임 스크립트/워크플로 복사 =====
COPY workflows/ ${WORKDIR}/workflows/
COPY handler.py ${WORKDIR}/handler.py
COPY bootstrap_models.py ${WORKDIR}/bootstrap_models.py
COPY start_pod.sh ${WORKDIR}/start_pod.sh
COPY local_invoke.py ${WORKDIR}/local_invoke.py
COPY payload_3d.json ${WORKDIR}/payload_3d.json
COPY payload_vid.json ${WORKDIR}/payload_vid.json

RUN chmod +x ${WORKDIR}/start_pod.sh

CMD ["bash", "-lc", "python /workspace/bootstrap_models.py && echo '[bootstrap done] (set Command to /workspace/start_pod.sh for full ComfyUI run)'"]

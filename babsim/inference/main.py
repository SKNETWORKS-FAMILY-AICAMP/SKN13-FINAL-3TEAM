import asyncio
import logging
import os
import requests
import json
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# --- 설정 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("inference")

# --- vLLM API 설정 ---
# nginx를 통해 vLLM API에 접근 (포트 번호 불필요)
VLLM_API_BASE = os.getenv("VLLM_API_BASE", "http://nginx/vllm")  # nginx를 통한 vLLM API 접근
VLLM_MODEL_NAME = os.getenv("VLLM_MODEL_NAME", "kakaocorp/kanana-1.5-8b-instruct-2505")
VLLM_ADAPTER_NAME = os.getenv("VLLM_ADAPTER_NAME", "ki-student/kanana-finetuned-model-v1")  # LoRA 어댑터

# --- SSH 터널링 및 인증 설정 ---
SSH_TUNNEL_HOST = os.getenv("SSH_TUNNEL_HOST", None)  # SSH 호스트 (예: username@hostname)
SSH_TUNNEL_PORT = os.getenv("SSH_TUNNEL_PORT", "22")  # SSH 포트
SSH_PRIVATE_KEY_PATH = os.getenv("SSH_PRIVATE_KEY_PATH", None)  # SSH 개인키 경로
VLLM_API_KEY = os.getenv("VLLM_API_KEY", None)  # vLLM API 키 (필요한 경우)

# --- 핸들 저장소 ---
models = {}

# ---------------------- vLLM API 유틸리티 ----------------------
def _check_vllm_health() -> bool:
    """vLLM API 서버 상태 확인"""
    try:
        response = requests.get(f"{VLLM_API_BASE}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"vLLM API health check failed: {e}")
        return False

def _generate_with_vllm(prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
    """vLLM API를 사용하여 텍스트 생성 (LoRA 어댑터 지원)"""
    try:
        payload = {
            "model": VLLM_MODEL_NAME,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
            "adapter_name": VLLM_ADAPTER_NAME  # LoRA 어댑터 사용
        }
        
        # 인증 헤더 설정
        headers = {}
        if VLLM_API_KEY:
            headers["Authorization"] = f"Bearer {VLLM_API_KEY}"
        
        response = requests.post(
            f"{VLLM_API_BASE}/v1/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["text"]
        else:
            logger.error(f"vLLM API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="vLLM API 호출 실패")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"vLLM API request failed: {e}")
        raise HTTPException(status_code=500, detail="vLLM API 연결 실패")

def _chat_with_vllm(messages: list, max_tokens: int = 512, temperature: float = 0.7) -> str:
    """vLLM API를 사용하여 채팅 응답 생성 (LoRA 어댑터 지원)"""
    try:
        payload = {
            "model": VLLM_MODEL_NAME,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
            "adapter_name": VLLM_ADAPTER_NAME  # LoRA 어댑터 사용
        }
        
        # 인증 헤더 설정
        headers = {}
        if VLLM_API_KEY:
            headers["Authorization"] = f"Bearer {VLLM_API_KEY}"
        
        response = requests.post(
            f"{VLLM_API_BASE}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            logger.error(f"vLLM API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="vLLM API 호출 실패")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"vLLM API request failed: {e}")
        raise HTTPException(status_code=500, detail="vLLM API 연결 실패")

# ---------------------- 모델 초기화 (vLLM 사용) ----------------------
def _initialize_vllm_connection():
    """vLLM API 연결 초기화 및 상태 확인"""
    logger.info("=== vLLM API 연결 초기화 ===")
    
    if not _check_vllm_health():
        logger.warning("vLLM API 서버가 응답하지 않습니다. 환경변수 VLLM_API_BASE를 확인하세요.")
        logger.info(f"현재 설정된 VLLM_API_BASE: {VLLM_API_BASE}")
        logger.info(f"사용할 모델: {VLLM_MODEL_NAME}")
        return False
    
    logger.info("vLLM API 서버 연결 성공!")
    logger.info(f"API 엔드포인트: {VLLM_API_BASE}")
    logger.info(f"베이스 모델: {VLLM_MODEL_NAME}")
    logger.info(f"LoRA 어댑터: {VLLM_ADAPTER_NAME}")
    return True

# ---------------------- Lifespan ----------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global models
    logger.info("--- 서버 시작: 모델 로드를 시작합니다. ---")
    try:
        # vLLM API 연결 초기화
        if not _initialize_vllm_connection():
            raise RuntimeError("vLLM API 연결 실패. 환경변수 VLLM_API_BASE를 확인하세요.")

        # vLLM API 사용을 위한 모델 핸들 저장
        models["text_gen_model"] = _generate_with_vllm # 현재는 텍스트 생성만 지원
        models["text_gen_tokenizer"] = None # vLLM API는 토크나이저가 필요 없음

        logger.info("--- 텍스트 생성 모델(vLLM) 로드 완료 ---")
    except Exception as e:
        logger.error(f"모델 로딩 중 심각한 오류 발생: {e}", exc_info=True)
        models.clear()

    yield

    logger.info("--- 서버 종료: vLLM API 연결을 정리합니다. ---")
    models.clear()

app = FastAPI(lifespan=lifespan)

# ---------------------- 스키마 ----------------------
class TextGenerationRequest(BaseModel):
    prompt: str
    max_new_tokens: int = Field(default=512)
    temperature: Optional[float] = Field(default=0.7)
    top_p: Optional[float] = Field(default=0.9)
    top_k: Optional[int] = Field(default=50)
    repetition_penalty: Optional[float] = Field(default=1.2)

class TextGenerationResponse(BaseModel):
    generated_text: str

# ---------------------- 추론 (vLLM API 사용) ----------------------
def _generate_text_sync(prompt: str, generation_params: dict) -> str:
    """vLLM API를 사용하여 텍스트 생성"""
    try:
        # vLLM API 호출
        generated_text = _generate_with_vllm(
            prompt=prompt,
            max_tokens=generation_params.get("max_new_tokens", 512),
            temperature=generation_params.get("temperature", 0.7)
        )
        
        # 응답 텍스트 정리
        ans = generated_text.strip()
        
        # 프롬프트가 응답에 포함된 경우 제거
        if ans.startswith(prompt.strip()):
            ans = ans[len(prompt):].strip()
        
        # 특정 패턴 제거
        import re
        ans = re.sub(r'^당신은 자동차 디자인 트렌드.*?설명해주세요\.\s*', '', ans, flags=re.DOTALL).strip()
        if "당신은 자동차 디자인 전문 AI" in ans:
            ans = ans.replace("당신은 자동차 디자인 전문 AI", "").strip()
        
        return ans
        
    except Exception as e:
        logger.error(f"vLLM API 호출 중 오류 발생: {e}")
        raise e

# ---------------------- 엔드포인트 ----------------------
@app.get("/health")
async def health_check():
    if "text_gen_model" in models and models["text_gen_model"] is not None:
        return {"status": "ok", "message": "Inference server is running and vLLM API is connected."}
    raise HTTPException(status_code=503, detail="vLLM API is not ready or failed to connect.")

@app.post("/generate-text", response_model=TextGenerationResponse)
async def generate_text(request: TextGenerationRequest):
    if "text_gen_model" not in models:
        raise HTTPException(status_code=503, detail="vLLM API가 준비되지 않았습니다.")

    try:
        logger.info(f"Generating text for prompt: '{request.prompt[:100]}...'")
        generation_params = {
            "max_new_tokens": request.max_new_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "top_k": request.top_k,
            "repetition_penalty": request.repetition_penalty,
        }
        generated_text = await asyncio.to_thread(
            _generate_text_sync, request.prompt, generation_params
        )
        return TextGenerationResponse(generated_text=generated_text)
    except Exception as e:
        logger.error(f"Text generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred during text generation: {e}")

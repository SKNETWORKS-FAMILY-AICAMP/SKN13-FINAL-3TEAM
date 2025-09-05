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
# RunPod vLLM API에 직접 접근
VLLM_API_BASE = os.getenv("VLLM_API_BASE", "https://5tnwa7587h44rl-8001.proxy.runpod.net/")
VLLM_MODEL_NAME = os.getenv("VLLM_MODEL_NAME", "kakaocorp/kanana-1.5-8b-instruct-2505")
VLLM_ADAPTER_NAME = os.getenv("VLLM_ADAPTER_NAME", "ki-student/kanana-finetuned-model-v1")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", None)

# --- 핸들 저장소 ---
models = {}

# ---------------------- vLLM API 유틸리티 ----------------------
def _check_vllm_health() -> bool:
    """vLLM API 서버 상태 확인"""
    try:
        # 간단한 채팅 요청으로 API 상태 확인
        test_payload = {
            "model": VLLM_MODEL_NAME,
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 10
        }
        response = requests.post(f"{VLLM_API_BASE}/v1/chat/completions", json=test_payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"vLLM API health check failed: {e}")
        return False

def _generate_with_vllm(prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
    """vLLM API를 사용하여 텍스트 생성"""
    if not VLLM_API_BASE:
        raise HTTPException(status_code=500, detail="VLLM_API_BASE is not set in the .env file.")

    headers = {"Authorization": f"Bearer {VLLM_API_KEY}"} if VLLM_API_KEY else {}
    payload = {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }

    try:
        response = requests.post(f"{VLLM_API_BASE}/v1/completions", json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["text"]
    except requests.exceptions.RequestException as e:
        logger.error(f"vLLM API request failed: {e}")
        raise HTTPException(status_code=500, detail="vLLM API connection failed")

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
    logger.info("--- 서버 시작: vLLM API 연결을 시작합니다. ---")
    try:
        # vLLM API 연결 초기화
        if not _initialize_vllm_connection():
            logger.warning("vLLM API 연결 실패. Mock 응답 모드로 전환합니다.")
            # 연결 실패 시에도 서버는 계속 실행 (Mock 응답 제공)

        # vLLM API 사용을 위한 모델 핸들 저장
        models["text_gen_model"] = _generate_with_vllm
        models["chat_model"] = _chat_with_vllm
        models["vllm_connected"] = _check_vllm_health()

        logger.info("--- vLLM API 연결 준비 완료 ---")
    except Exception as e:
        logger.error(f"vLLM API 연결 중 심각한 오류 발생: {e}", exc_info=True)
        models["vllm_connected"] = False

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

class ChatRequest(BaseModel):
    messages: list
    max_tokens: int = 100
    temperature: float = 0.7

class ChatResponse(BaseModel):
    choices: list

# ---------------------- Mock 응답 생성 ----------------------
def _generate_mock_response(prompt: str) -> str:
    """vLLM API가 연결되지 않았을 때 사용할 Mock 응답"""
    prompt_lower = prompt.lower()
    
    if "현대자동차" in prompt_lower or "현대" in prompt_lower:
        if "철학" in prompt_lower:
            return """현대자동차의 철학은 '인간 중심의 자동차'를 추구하는 것입니다. 

주요 철학적 가치:
1. **인간 중심 설계**: 운전자와 승객의 편의성과 안전을 최우선으로 고려
2. **지속가능한 미래**: 친환경 기술과 지속가능한 모빌리티 솔루션 제공
3. **혁신과 창의성**: 첨단 기술과 창의적 디자인을 통한 새로운 가치 창출
4. **글로벌 시민**: 전 세계 고객의 다양한 니즈를 이해하고 반영

현대자동차는 단순한 이동수단을 넘어서, 사람들의 삶의 질을 향상시키는 동반자 역할을 하고자 합니다."""
        elif "디자인" in prompt_lower:
            return """현대자동차의 디자인 철학은 'Sensuous Sportiness'입니다.

핵심 디자인 원칙:
- **감성적 스포티함**: 역동적이면서도 우아한 비율과 선
- **미래지향적**: 혁신적이면서도 실용적인 디자인
- **브랜드 정체성**: 현대자동차만의 독특한 디자인 언어
- **사용자 경험**: 직관적이고 편리한 인터페이스

이러한 철학은 현대자동차의 모든 모델에 일관되게 적용되어 브랜드의 정체성을 강화하고 있습니다."""
        else:
            return "현대자동차에 대한 구체적인 질문을 해주시면 더 자세한 정보를 제공해드릴 수 있습니다."
    
    elif "자동차" in prompt_lower:
        return "자동차에 대한 질문을 해주셨네요. 현대자동차의 특정 모델이나 기술에 대해 더 구체적으로 질문해주시면 도움을 드릴 수 있습니다."
    
    else:
        return "안녕하세요! 현대자동차와 자동차 관련 질문에 대해 답변해드립니다. 구체적인 질문을 해주시면 더 정확한 정보를 제공해드릴 수 있습니다."

# ---------------------- 추론 (vLLM API 사용) ----------------------
def _generate_text_sync(prompt: str, generation_params: dict) -> str:
    """vLLM API를 사용하여 텍스트 생성"""
    try:
        # vLLM API 연결 상태 확인
        if not models.get("vllm_connected", False):
            logger.warning("vLLM API 연결되지 않음. Mock 응답 사용")
            return _generate_mock_response(prompt)
        
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
        # 오류 발생 시 Mock 응답으로 폴백
        return _generate_mock_response(prompt)

# ---------------------- 엔드포인트 ----------------------
@app.get("/health")
async def health_check():
    vllm_connected = models.get("vllm_connected", False)
    if vllm_connected:
        return {"status": "ok", "message": "Inference server is running and vLLM API is connected."}
    else:
        return {"status": "ok", "message": "Inference server is running in mock mode (vLLM API not connected)."}

@app.post("/generate-text", response_model=TextGenerationResponse)
async def generate_text(request: TextGenerationRequest):
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

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """채팅 완성 API (OpenAI 호환)"""
    
    try:
        # 마지막 메시지 추출
        if not request.messages:
            raise HTTPException(status_code=400, detail="메시지가 없습니다")
        
        last_message = request.messages[-1]["content"]
        
        # vLLM API 연결 상태 확인
        if not models.get("vllm_connected", False):
            logger.warning("vLLM API 연결되지 않음. Mock 응답 사용")
            response_content = _generate_mock_response(last_message)
        else:
            # vLLM API 호출
            response_content = _chat_with_vllm(
                messages=request.messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
        
        return ChatResponse(choices=[{
            "message": {
                "role": "assistant",
                "content": response_content
            },
            "finish_reason": "stop"
        }])
        
    except Exception as e:
        logger.error(f"Chat completion error: {e}", exc_info=True)
        # 오류 발생 시 Mock 응답으로 폴백
        response_content = _generate_mock_response(request.messages[-1]["content"] if request.messages else "안녕하세요")
        return ChatResponse(choices=[{
            "message": {
                "role": "assistant",
                "content": response_content
            },
            "finish_reason": "stop"
        }])

@app.get("/")
async def root():
    """루트 엔드포인트"""
    vllm_connected = models.get("vllm_connected", False)
    return {
        "message": "Simple Inference Server", 
        "status": "running",
        "vllm_connected": vllm_connected,
        "api_endpoint": VLLM_API_BASE
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
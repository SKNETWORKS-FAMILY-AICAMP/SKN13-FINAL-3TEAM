import asyncio
import logging
import os
import torch
import re
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

# --- 설정 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("inference")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {DEVICE}")

# --- HF Hub 환경변수 (우선) ---
HF_BASE_REPO = os.getenv("HF_BASE_REPO", None)      # 예: your-org/kanana-1.5-8b-instruct-2505
HF_BASE_REV  = os.getenv("HF_BASE_REV",  None)      # 예: main (없으면 None)
HF_ADPT_REPO = os.getenv("HF_ADPT_REPO", None)      # 예: your-org/kanana_finetuned_model
HF_ADPT_REV  = os.getenv("HF_ADPT_REV",  None)
HF_TOKEN     = os.getenv("HUGGINGFACE_TOKEN", None) 

# --- 로컬 경로 (폴백) ---
BASE_MODEL_PATH = os.getenv("BASE_MODEL_PATH", None)  # 예: /app/models/kanana-1.5-8b-instruct-2505
ADAPTER_PATH    = os.getenv("ADAPTER_PATH", None)     # 예: /app/models/kanana_finetuned_model

# --- 폴백 제어 스위치 ---
DISABLE_4BIT = os.getenv("DISABLE_4BIT", "false").lower() in ("1", "true", "yes")
DISABLE_8BIT = os.getenv("DISABLE_8BIT", "false").lower() in ("1", "true", "yes")

# --- 핸들 저장소 ---
models = {}

# ---------------------- 경로/레포 선택 유틸 ----------------------
def _src_base() -> str:
    """
    HF 레포 ID가 있으면 그걸 우선 사용, 없으면 로컬 경로를 사용.
    """
    src = HF_BASE_REPO or BASE_MODEL_PATH
    if not src:
        raise RuntimeError("No base model source provided. Set HF_BASE_REPO or BASE_MODEL_PATH.")
    return src

def _src_adapter() -> str:
    src = HF_ADPT_REPO or ADAPTER_PATH
    if not src:
        raise RuntimeError("No adapter source provided. Set HF_ADPT_REPO or ADAPTER_PATH.")
    return src

# ---------------------- 로더들 ----------------------
def _load_tokenizer() -> AutoTokenizer:
    src = _src_base()
    logger.info(f"Loading tokenizer from: {src} (rev={HF_BASE_REV})")
    tok = AutoTokenizer.from_pretrained(
        src,
        trust_remote_code=True,
        revision=HF_BASE_REV,
        token=HF_TOKEN
    )
    if tok.pad_token_id is None:
        tok.pad_token_id = tok.eos_token_id
        logger.warning("tokenizer.pad_token_id not set; defaulting to eos_token_id.")
    return tok

def _load_base_model_4bit() -> AutoModelForCausalLM:
    logger.info("Attempting 4-bit load with BitsAndBytesConfig(nf4, double-quant, bf16 compute).")
    bnb_cfg = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        _src_base(),
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        quantization_config=bnb_cfg,
        low_cpu_mem_usage=False,
        revision=HF_BASE_REV,
        token=HF_TOKEN
    )
    return model

def _load_base_model_8bit() -> AutoModelForCausalLM:
    logger.info("Attempting 8-bit load as fallback.")
    bnb_cfg = BitsAndBytesConfig(
        load_in_8bit=True,
        llm_int8_enable_fp32_cpu_offload=False,
    )
    model = AutoModelForCausalLM.from_pretrained(
        _src_base(),
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        device_map="auto",
        trust_remote_code=True,
        quantization_config=bnb_cfg,
        low_cpu_mem_usage=False,
        revision=HF_BASE_REV,
        token=HF_TOKEN
    )
    return model

def _load_base_model_fp16() -> AutoModelForCausalLM:
    logger.info("Attempting fp16/fp32 load as last resort.")
    model = AutoModelForCausalLM.from_pretrained(
        _src_base(),
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        device_map="auto",
        trust_remote_code=True,
        low_cpu_mem_usage=False,
        revision=HF_BASE_REV,
        token=HF_TOKEN
    )
    return model

def _apply_peft_adapter(base_model: AutoModelForCausalLM) -> PeftModel:
    src = _src_adapter()
    logger.info(f"Applying PEFT adapter from: {src} (rev={HF_ADPT_REV})")
    peft_model = PeftModel.from_pretrained(
        base_model,
        src,
        is_trainable=False,
        revision=HF_ADPT_REV,
        token=HF_TOKEN
    )
    return peft_model

def _safe_load_model_with_fallbacks():
    last_err = None

    if not DISABLE_4BIT:
        try:
            model = _load_base_model_4bit()
            logger.info("Base model loaded in 4-bit.")
            return model
        except Exception as e:
            last_err = e
            logger.warning(f"4-bit load failed: {e.__class__.__name__}: {e}")

    if not DISABLE_8BIT:
        try:
            model = _load_base_model_8bit()
            logger.info("Base model loaded in 8-bit.")
            return model
        except Exception as e:
            last_err = e
            logger.warning(f"8-bit load failed: {e.__class__.__name__}: {e}")

    try:
        model = _load_base_model_fp16()
        logger.info("Base model loaded in fp16/fp32.")
        return model
    except Exception as e:
        logger.error("All model load attempts failed.", exc_info=True)
        raise e if last_err is None else last_err

# ---------------------- Lifespan ----------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global models
    logger.info("--- 서버 시작: 모델 로드를 시작합니다. ---")
    try:
        tokenizer = _load_tokenizer()
        base_model = _safe_load_model_with_fallbacks()
        peft_model = _apply_peft_adapter(base_model)
        peft_model.eval()

        models["text_gen_model"] = peft_model
        models["text_gen_tokenizer"] = tokenizer

        logger.info("--- 텍스트 생성 모델(베이스+어댑터) 로드 완료 ---")
    except Exception as e:
        logger.error(f"모델 로딩 중 심각한 오류 발생: {e}", exc_info=True)
        models.clear()

    yield

    logger.info("--- 서버 종료: 모델을 메모리에서 해제합니다. ---")
    models.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

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

# ---------------------- 추론 ----------------------
def _generate_text_sync(prompt: str, generation_params: dict) -> str:
    tok = models["text_gen_tokenizer"]
    model = models["text_gen_model"]

    inputs = tok(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(**inputs, **generation_params)

    full_text = tok.decode(outputs[0], skip_special_tokens=True)

    ans = full_text
    if full_text.strip().startswith(prompt.strip()):
        ans = full_text[len(prompt):].strip()

    ans = re.sub(r'^당신은 자동차 디자인 트렌드.*?설명해주세요\.\s*', '', ans, flags=re.DOTALL).strip()
    if "당신은 자동차 디자인 전문 AI" in ans:
        ans = ans.replace("당신은 자동차 디자인 전문 AI", "").strip()

    return ans

# ---------------------- 엔드포인트 ----------------------
@app.get("/health")
async def health_check():
    if "text_gen_model" in models and models["text_gen_model"] is not None:
        return {"status": "ok", "message": "Inference server is running and model is loaded."}
    raise HTTPException(status_code=503, detail="Model is not ready or failed to load.")

@app.post("/generate-text", response_model=TextGenerationResponse)
async def generate_text(request: TextGenerationRequest):
    if "text_gen_model" not in models:
        raise HTTPException(status_code=503, detail="Model is not ready.")

    try:
        logger.info(f"Generating text for prompt: '{request.prompt[:100]}...'")
        generation_params = {
            "max_new_tokens": request.max_new_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "top_k": request.top_k,
            "repetition_penalty": request.repetition_penalty,
            "do_sample": True,
            "pad_token_id": models["text_gen_tokenizer"].pad_token_id,
            "eos_token_id": models["text_gen_tokenizer"].eos_token_id,
        }
        generated_text = await asyncio.to_thread(
            _generate_text_sync, request.prompt, generation_params
        )
        return TextGenerationResponse(generated_text=generated_text)
    except Exception as e:
        logger.error(f"Text generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred during text generation: {e}")

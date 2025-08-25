import asyncio
import logging
import os
import torch
import re
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# --- 설정 ---
logging.basicConfig(level=logging.INFO)

BASE_MODEL_PATH = os.getenv("BASE_MODEL_PATH", "/app/models/exaone_4.0_1.2b")
ADAPTER_PATH = os.getenv("ADAPTER_PATH", "/app/models/llm_finetuned_model")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logging.info(f"Using device: {DEVICE}")

models = {}

# --- FastAPI Lifespan 이벤트 (서버 시작 시 모델 로드) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global models
    logging.info("--- 서버 시작: 모델 로드를 시작합니다. ---")
    try:
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_PATH,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH, trust_remote_code=True)
        logging.info("Base model and tokenizer loaded successfully.")
        
        logging.info(f"Applying adapter from {ADAPTER_PATH}...")
        peft_model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
        
        models["text_gen_model"] = peft_model.eval()
        models["text_gen_tokenizer"] = tokenizer
        logging.info("--- 텍스트 생성 모델(베이스+어댑터) 로드 완료 ---")
    except Exception as e:
        logging.error(f"모델 로딩 중 심각한 오류 발생: {e}", exc_info=True)
        models.clear()
    yield
    logging.info("--- 서버 종료: 모델을 메모리에서 해제합니다. ---")
    models.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

app = FastAPI(lifespan=lifespan)

# --- Pydantic 모델 ---
class TextGenerationRequest(BaseModel):
    prompt: str
    max_new_tokens: int = Field(default=512)
    temperature: Optional[float] = Field(default=0.7)
    top_p: Optional[float] = Field(default=0.9)
    top_k: Optional[int] = Field(default=50)
    repetition_penalty: Optional[float] = Field(default=1.2)

class TextGenerationResponse(BaseModel):
    generated_text: str

# --- API 엔드포인트 ---
@app.get("/health")
async def health_check():
    if "text_gen_model" in models and models["text_gen_model"] is not None:
        return {"status": "ok", "message": "Inference server is running and model is loaded."}
    else:
        raise HTTPException(status_code=503, detail="Model is not ready or failed to load.")

def _generate_text_sync(prompt: str, generation_params: dict) -> str:
    tokenizer = models["text_gen_tokenizer"]
    model = models["text_gen_model"]
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
    
    with torch.no_grad():
        outputs = model.generate(**inputs, **generation_params)
    
    full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    assistant_marker = "### Assistant:"
    if assistant_marker in prompt:
         if assistant_marker in full_text:
             answer = full_text.split(assistant_marker)[-1].strip()
         elif full_text.strip().startswith(prompt.strip()):
             answer = full_text.strip()[len(prompt.strip()):].strip()
         else:
             answer = full_text
    else:
        answer = full_text

    answer = re.sub(r'^당신은 자동차 디자인 트렌드.*?설명해주세요\.\s*', '', answer, flags=re.DOTALL).strip()

    if "당신은 자동차 디자인 전문 AI" in answer:
        answer = answer.replace("당신은 자동차 디자인 전문 AI", "").strip()

    return answer

@app.post("/generate-text", response_model=TextGenerationResponse)
async def generate_text(request: TextGenerationRequest):
    if "text_gen_model" not in models:
        raise HTTPException(status_code=503, detail="Model is not ready.")
    try:
        logging.info(f"Generating text for prompt: '{request.prompt[:100]}...'")
        
        generation_params = {
            "max_new_tokens": request.max_new_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "top_k": request.top_k,
            "repetition_penalty": request.repetition_penalty,
            "do_sample": True,
            "pad_token_id": models["text_gen_tokenizer"].eos_token_id,
            "eos_token_id": models["text_gen_tokenizer"].eos_token_id,
        }
        
        generated_text = await asyncio.to_thread(
            _generate_text_sync, request.prompt, generation_params
        )
        return TextGenerationResponse(generated_text=generated_text)
    except Exception as e:
        logging.error(f"Text generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
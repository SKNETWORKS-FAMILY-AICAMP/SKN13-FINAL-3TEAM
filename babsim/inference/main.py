# inference/main.py
import logging
import os
import uuid
import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from diffusers import StableDiffusion3Pipeline
from transformers import AutoTokenizer, AutoModelForCausalLM

# --- 설정 ---
logging.basicConfig(level=logging.INFO)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logging.info(f"Using device: {DEVICE}")

SLLM_MODEL_PATH = "./models/EXAONE-4.0-1.2B"
TXT2IMG_MODEL_PATH = "./models/stable-diffusion-3.5-medium"
# 모델 바꾸고 실행

# 서버의 생명주기 동안 모델을 담아둘 글로벌 딕셔너리
models = {}

# --- FastAPI Lifespan 이벤트 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    서버가 시작될 때 모델을 로드하고, 서버가 종료될 때 메모리를 정리합니다.
    이 방식을 사용하면 매 요청마다 모델을 로드할 필요가 없어 응답 속도가 매우 빨라집니다.
    """
    logging.info(f"Using device: {DEVICE}")
    logging.info("--- SKIPPING MODEL LOAD FOR TEST ---") # 테스트를 위해 모델 로드를 건너뛴다는 로그

    # # 1. Text-to-Image 모델 로드 (Stable Diffusion)
    # logging.info(f"Loading Text-to-Image model from {TXT2IMG_MODEL_PATH}...")
    # txt2img_pipe = StableDiffusion3Pipeline.from_pretrained(
    #     TXT2IMG_MODEL_PATH, torch_dtype=torch.float16
    # )
    # models["text_to_image"] = txt2img_pipe.to(DEVICE)
    # logging.info("Text-to-Image model loaded successfully.")

    # # 2. Text Generation 모델 로드 (EXAONE)
    # logging.info(f"Loading Text Generation model from {SLLM_MODEL_PATH}...")
    # sllm_tokenizer = AutoTokenizer.from_pretrained(SLLM_MODEL_PATH)
    # sllm_model = AutoModelForCausalLM.from_pretrained(
    #     SLLM_MODEL_PATH,
    #     torch_dtype=torch.float16, # VRAM 사용량을 줄이기 위해 float16 사용
    #     low_cpu_mem_usage=True     # CPU 메모리 사용량 최적화
    # )
    # models["text_gen_tokenizer"] = sllm_tokenizer
    # models["text_gen_model"] = sllm_model.to(DEVICE)
    # logging.info("Text Generation model loaded successfully.")
    
    yield # 이 시점에서 FastAPI 애플리케이션이 요청을 받기 시작합니다.

    # --- 서버 종료 시 실행될 코드 ---
    logging.info("Clearing models at shutdown...")
    models.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logging.info("Shutdown complete.")

# FastAPI 앱에 lifespan 관리자 적용
app = FastAPI(lifespan=lifespan)

# --- 요청/응답 모델 ---
class TextGenerationRequest(BaseModel):
    prompt: str

class ImageGenerationRequest(BaseModel):
    prompt: str

# --- API 엔드포인트 ---
@app.get("/")
async def health_check():
    """서버가 정상적으로 실행 중인지 확인하는 엔드포인트"""
    return {"status": "ok", "message": "Inference server is running."}

@app.post("/generate-text")
async def generate_text(request: TextGenerationRequest):
    """미리 로드된 EXAONE 모델을 사용하여 텍스트를 생성합니다."""
    # try:
    #     logging.info(f"Generating text for prompt: '{request.prompt[:50]}...'")
    #     tokenizer = models.get("text_gen_tokenizer")
    #     model = models.get("text_gen_model")
    #     if tokenizer is None or model is None:
    #         raise HTTPException(status_code=503, detail="Model is not ready.")
            
    #     inputs = tokenizer(request.prompt, return_tensors="pt").to(DEVICE)
    #     outputs = model.generate(**inputs, max_length=100)
    #     generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    #     return {"generated_text": generated_text}

    # except Exception as e:
    #     logging.error(f"Text generation error: {e}")
    #     raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-image")
async def generate_image(request: ImageGenerationRequest):
    """미리 로드된 Stable Diffusion 모델을 사용하여 이미지를 생성합니다."""
    # try:
    #     logging.info(f"Generating image for prompt: '{request.prompt[:50]}...'")
    #     pipe = models.get("text_to_image")
    #     if pipe is None:
    #         raise HTTPException(status_code=503, detail="Model is not ready.")

    #     image = pipe(request.prompt).images[0]
        
    #     image_filename = f"{uuid.uuid4()}.png"
    #     save_dir = "/app/generated_images"
    #     os.makedirs(save_dir, exist_ok=True)
    #     image_path = os.path.join(save_dir, image_filename)
    #     image.save(image_path)
        
    #     logging.info(f"Image saved to {image_path}")
    #     return {"image_path": image_path}

    # except Exception as e:
    #     logging.error(f"Image generation error: {e}")
    #     raise HTTPException(status_code=500, detail=str(e))

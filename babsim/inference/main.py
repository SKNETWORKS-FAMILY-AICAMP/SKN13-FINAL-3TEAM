# inference/main.py
import logging
import os
import uuid
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from diffusers import StableDiffusion3Pipeline
from datetime import datetime

# --- 설정 ---
logging.basicConfig(level=logging.INFO)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logging.info(f"Using device: {DEVICE}")

SLLM_MODEL_PATH = "./models/EXAONE-4.0-1.2B"
TXT2IMG_MODEL_PATH = "./models/stable-diffusion-3.5-medium"

app = FastAPI()

# --- 요청/응답 모델 ---
class TextGenerationRequest(BaseModel):
    prompt: str

class ImageGenerationRequest(BaseModel):
    prompt: str

@app.post("/generate-image")
async def generate_image(request: ImageGenerationRequest):
    """Text-to-Image 모델을 로드하여 이미지를 생성하고, 메모리에서 해제합니다."""
    txt2img_pipe = None
    try:
        logging.info("Loading Text-to-Image model...")
        txt2img_pipe = StableDiffusion3Pipeline.from_pretrained(TXT2IMG_MODEL_PATH, torch_dtype=torch.float16)
        txt2img_pipe = txt2img_pipe.to(DEVICE)
        logging.info("Text-to-Image model loaded.")

        image = txt2img_pipe(request.prompt).images[0]
        
        image_filename = f"{uuid.uuid4()}.png"
        save_dir = "/app/generated_images"
        os.makedirs(save_dir, exist_ok=True)
        image_path = os.path.join(save_dir, image_filename)
        image.save(image_path)

        return {"image_path": image_path}

    except Exception as e:
        logging.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate image.")
    finally:
        # 작업 완료 후 모델을 메모리에서 해제하여 VRAM 확보
        logging.info("Unloading Text-to-Image model...")
        del txt2img_pipe
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logging.info("Text-to-Image model unloaded.")

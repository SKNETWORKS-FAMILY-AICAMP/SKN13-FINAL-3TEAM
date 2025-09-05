import asyncio
import logging
import os
import requests
import json
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inference")

# --- API Settings ---
VLLM_API_BASE = os.getenv("VLLM_API_URL") # .env 파일과 변수명 일치시킴
FLUX_API_URL = os.getenv("FLUX_API_URL")
VLLM_API_KEY = os.getenv("VLLM_API_KEY")

# --- LLM Instruction Prompts for Image Generation ---
PROMPT_2 = (
    "You are generating a highly detailed text-to-image prompt for a car design model. "
    "The goal is to create a realistic Hyundai concept car image that strictly maintains the correct automobile form "
    "(no human figures, no distorted objects, no unrelated content) with sharp outlines and complete body visible. "
    "The generated prompt should enforce the following constraints:\n" \
    "1. Viewpoint: clear 3/4 front view of the entire car, with proper perspective, proportions, and wheel alignment.\n" \
    "2. Body form: accurate automobile silhouette, well-defined roofline, hood, trunk, and greenhouse. " \
    "No missing parts, no cropped edges, no blurred boundaries.\n" \
    "3. Design language: incorporate Hyundai’s design philosophy (Sensuous Sportiness, Parametric Pixel details, " \
    "clean aerodynamic curves, sharp shoulder lines, taut body surfacing).\n" \
    "4. Exterior details: angular grille, distinctive headlights and taillights, sculpted hood, " \
    "aerodynamic side mirrors, flush door handles, sharp window line, short overhangs, proper dash-to-axle ratio.\n" \
    "5. Wheels and stance: 19-inch multi-spoke wheels, low-profile tires, wide stance, low beltline, sporty proportions.\n" \
    "6. Materials and finish: metallic paint, photorealistic reflections, no cartoon or abstract style.\n" \
    "7. Background: neutral studio lighting or soft outdoor daylight, with emphasis on car clarity and edge sharpness.\n" \
    "8. Negative constraints: absolutely no humans, text overlays, watermarks, distorted wheels, cropped body, " \
    "excessive background clutter, or unrealistic textures.\n" \
    "Generate a fluent English text description that integrates all these constraints naturally into one continuous prompt, " \
    "up to the maximum token limit, so the image model can produce a sharp, realistic, full-body Hyundai car design rendering."
)

NEGATIVE_PROMPT = (
    "cartoon, illustration, sketch, anime, cgi, hand-drawn, "
    "side view, top view, cropped, out of frame, truncated, incomplete, "
    "rotating wheel, extra wheels, extra doors, text, watermark, logo, "
    "outdoor, street, colored background, cut, clutter, "
    "reflection, shadow, frame, border, blurry, low quality"
)

NEGATIVE_PROMPT_2 = (
    "You are generating a negative prompt for a car design image model. "
    "The goal is to strictly forbid the generation of any elements that would distort, degrade, or distract "
    "from a clean, photorealistic Hyundai automobile rendering. "
    "List all forbidden aspects clearly, so the image generator avoids them completely.\n" \
    "1. No humans, human parts, faces, bodies, or figures inside or outside the car.\n" \
    "2. No cropped, cut-off, or incomplete vehicles; the full car body must always be visible.\n" \
    "3. No blurred, foggy, noisy, pixelated, low-resolution, or distorted edges.\n" \
    "4. No warped, melted, or deformed car shapes (wheels, roofline, hood, doors, headlights, etc.).\n" \
    "5. No double exposure, ghosting, duplicate wheels, overlapping body panels, or extra limbs.\n" \
    "6. No text, watermarks, logos, signatures, captions, or overlay graphics in the image.\n" \
    "7. No cartoon, sketch, anime, comic, abstract, or artistic styles; only photorealism is allowed.\n" \
    "8. No surreal or unrelated objects (people, animals, buildings, furniture, clouds inside the car, " \
    "random patterns, extra tires, floating shapes, unrealistic props).\n" \
    "9. No extreme fisheye, distorted wide-angle, or unnatural camera perspectives.\n" \
    "10. No excessive background clutter, distracting scenery, irrelevant items, or messy environments.\n" \
    "11. No incorrect lighting such as harsh glare, overexposed highlights, unrealistic neon, " \
    "or inconsistent shadows that break realism.\n" \
    "12. No wrong materials or textures: avoid plastic-like finish, muddy colors, watercolor style, " \
    "or artificial surfaces.\n" \
    "13. No cropped wheels, missing tires, distorted rims, or unaligned axles.\n" \
    "14. No incomplete rendering artifacts such as half-rendered doors, broken reflections, " \
    "or faded outlines near the car’s border.\n" \
    "15. No bizarre modifications (wings, rocket boosters, tanks, weapons, fantasy elements).\n" \
    "16. No duplicate or misplaced emblems; ensure the Hyundai logo appears only once in the correct position on the front of the car.\n" \
    "Generate a fluent, comprehensive negative prompt that integrates all these forbidden constraints into one " \
    "continuous text block, maximizing the token budget, to help the image model avoid any unrealistic, " \
    "distorted, or irrelevant outputs."
)

# --- vLLM API Utilities ---

def _generate_with_vllm(prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
    if not VLLM_API_BASE:
        raise HTTPException(status_code=500, detail="VLLM_API_URL is not set in the .env file.")

    headers = {"Authorization": f"Bearer {VLLM_API_KEY}"} if VLLM_API_KEY else {}
    payload = {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }

    # Runpod에 이미 모델이 로드되어 있으므로, model, adapter_name 파라미터는 보내지 않음.
    try:
        response = requests.post(f"{VLLM_API_BASE}/v1/completions", json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["text"]
    except requests.exceptions.RequestException as e:
        logger.error(f"vLLM API request failed: {e}")
        raise HTTPException(status_code=500, detail="vLLM API connection failed")

# --- Flux API Utility ---
def _call_flux_api(prompt: str, prompt_2: str = "", negative_prompt: str = "") -> str:
    if not FLUX_API_URL:
        raise HTTPException(status_code=500, detail="FLUX_API_URL is not set.")
    try:
        payload = {"prompt": prompt}
        if prompt_2:
            payload["prompt_2"] = prompt_2
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        logger.info(f"Calling Flux API with prompt: {prompt[:100]}... prompt_2: {prompt_2[:50]}... neg_prompt: {negative_prompt[:50]}...")
        response = requests.post(FLUX_API_URL, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()
        if "s3_url" not in data:
            raise ValueError("S3 URL not in Flux API response.")
        return data["s3_url"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Flux API request failed: {e}")
        raise HTTPException(status_code=500, detail="Flux API connection failed.")

app = FastAPI()

# --- Schemas ---
class ChecklistImageRequest(BaseModel):
    prompt: str

class ChecklistImageResponse(BaseModel):
    s3_url: str

# --- Endpoints ---
@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/generate_checklist_image", response_model=ChecklistImageResponse)
async def generate_checklist_image(request: ChecklistImageRequest):
    try:
        # 1. 메인 프롬프트 생성 (기존 로직)
        refinement_prompt_instruction = (
            f'Create a detailed, photorealistic image prompt for a futuristic concept car based on this keyword: "{request.prompt}". ' 
            f'Describe the scene, lighting, and key features in a single, concise English sentence.'
        )
        refined_prompt = await asyncio.to_thread(
            _generate_with_vllm, refinement_prompt_instruction, max_tokens=100
        )
        
        # 2. prompt_2 생성
        generated_prompt_2 = ""
        try:
            generated_prompt_2 = await asyncio.to_thread(
                _generate_with_vllm, PROMPT_2, max_tokens=500 # prompt_2는 더 길 수 있음
            )
        except Exception as e:
            logger.warning(f"Failed to generate prompt_2 using vLLM: {e}. Using empty string.")

        # 3. negative_prompt 생성 (실패 시 DEFAULT_NEGATIVE_PROMPT 사용)
        generated_negative_prompt = NEGATIVE_PROMPT
        try:
            generated_negative_prompt = await asyncio.to_thread(
                _generate_with_vllm, NEGATIVE_PROMPT_2, max_tokens=500 # negative_prompt도 더 길 수 있음
            )
        except Exception as e:
            logger.warning(f"Failed to generate negative_prompt using vLLM: {e}. Using default.")

        # 4. Flux 모델 호출
        s3_url = await asyncio.to_thread(
             _call_flux_api, 
             refined_prompt.strip(), 
             generated_prompt_2.strip(), 
             generated_negative_prompt.strip()
        )

        return ChecklistImageResponse(s3_url=s3_url)

    except Exception as e:
        logger.error(f"Checklist image generation error: {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
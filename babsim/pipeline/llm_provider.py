from __future__ import annotations
import os
import torch
from typing import Optional
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
from peft import PeftModel

def _env(path_key: str, default: Optional[str] = None) -> Optional[str]:
    p = os.getenv(path_key, default)
    return p if p and os.path.exists(p) else default

class _KananaChat:
    def __init__(self):
        # 로컬 모델 로딩 로직을 제거하여 앱 시작 시 에러 방지
        pass

    def _build_prompt(self, prompt: str) -> str:
        system = "당신은 현대자동차/자동차 지식에 특화된 한국어 어시스턴트입니다. 반드시 한국어로 답하세요."
        return f"[SYSTEM]\n{system}\n\n[USER]\n{prompt}\n\n[ASSISTANT]\n"

    @torch.inference_mode()
    def generate_response(self, prompt: str, max_length: int = 512) -> str:
        # 기존 로컬 추론 대신, vLLM 서버를 호출하는 함수를 사용
        return generate_vllm_response(prompt, max_length=max_length)

import requests
from django.conf import settings

def generate_vllm_response(prompt: str, max_length: int = 512) -> str:
    """
    RunPod의 vLLM API 서버를 호출하여 모델의 응답을 생성합니다.
    """
    api_url = settings.VLLM_API_URL
    model_name = settings.VLLM_MODEL_NAME

    headers = {"Content-Type": "application/json"}
    
    # OpenAI 호환 API 형식에 맞게 데이터 구성
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "당신은 현대자동차/자동차 지식에 특화된 한국어 어시스턴트입니다. 반드시 한국어로 답하세요."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_length,
        "temperature": 0.7,
    }

    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=120) # 120초 타임아웃
        response.raise_for_status()  # 200 OK가 아닌 경우 예외 발생

        result = response.json()
        content = result['choices'][0]['message']['content']
        return content.strip()

    except requests.exceptions.RequestException as e:
        # 네트워크 오류 또는 HTTP 오류 처리
        print(f"vLLM API 호출 오류: {e}")
        return "모델 응답을 가져오는 데 실패했습니다."
    except (KeyError, IndexError) as e:
        # 응답 JSON 구조가 예상과 다를 경우 처리
        print(f"vLLM API 응답 처리 오류: {e}")
        return "모델 응답을 처리하는 데 실패했습니다."


# kanana_llm_model = _KananaChat()

def generate_vllm_response(prompt: str, max_length: int = 512) -> str:
    """
    RunPod의 vLLM API 서버를 호출하여 모델의 응답을 생성합니다.
    """
    api_url = settings.VLLM_API_URL
    model_name = settings.VLLM_MODEL_NAME

    headers = {"Content-Type": "application/json"}
    
    # OpenAI 호환 API 형식에 맞게 데이터 구성
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "당신은 현대자동차/자동차 지식에 특화된 한국어 어시스턴트입니다. 반드시 한국어로 답하세요."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_length,
        "temperature": 0.7,
    }

    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=120) # 120초 타임아웃
        response.raise_for_status()  # 200 OK가 아닌 경우 예외 발생

        result = response.json()
        content = result['choices'][0]['message']['content']
        return content.strip()

    except requests.exceptions.RequestException as e:
        # 네트워크 오류 또는 HTTP 오류 처리
        print(f"vLLM API 호출 오류: {e}")
        return "모델 응답을 가져오는 데 실패했습니다."
    except (KeyError, IndexError) as e:
        # 응답 JSON 구조가 예상과 다를 경우 처리
        print(f"vLLM API 응답 처리 오류: {e}")
        return "모델 응답을 처리하는 데 실패했습니다."


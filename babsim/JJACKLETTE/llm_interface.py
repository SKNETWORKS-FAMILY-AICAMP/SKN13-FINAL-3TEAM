# JJACKLETTE/llm_interface.py (새 파일)

# JJACKLETTE/llm_interface.py

import torch
import logging
# from asgiref.sync import sync_to_async # <-- 이 줄 제거
from .apps import JjackletteConfig

logger = logging.getLogger(__name__)

# @sync_to_async 데코레이터 제거
def generate_response(user_input: str) -> str:
    """
    완전한 동기 방식으로 작동하는 LLM 응답 생성 함수
    """
    model = JjackletteConfig.model
    tokenizer = JjackletteConfig.tokenizer

    if not all([model, tokenizer]):
        return "죄송합니다. 챗봇 모델이 현재 준비되지 않았습니다."

    try:
        device = model.device
        inputs = tokenizer.encode(user_input, return_tensors="pt").to(device)

        with torch.no_grad():
            outputs = model.generate(
                inputs, 
                max_new_tokens=150, 
                do_sample=True, 
                temperature=0.7
            )

        response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response_text.replace(user_input, "").strip()

    except Exception as e:
        logger.error(f"LLM inference error: {e}", exc_info=True)
        return "답변 생성 중 오류가 발생했습니다."
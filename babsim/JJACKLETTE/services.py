import os
from django.conf import settings
import requests # Import requests library
import json # Import json library for handling JSON data



def get_vllm_response(user_query: str) -> str:
    """
    vLLM API를 사용하여 사용자 쿼리에 대한 응답을 생성합니다.
    """
    api_url = settings.VLLM_API_URL
    model_name = settings.VLLM_MODEL_NAME

    if not api_url or not model_name:
        print("VLLM_API_URL 또는 VLLM_MODEL_NAME이 설정되지 않았습니다.")
        return "VLLM API 설정이 완료되지 않았습니다."

    # vLLM OpenAI 호환 API의 chat/completions 엔드포인트 사용
    chat_completions_url = f"{api_url.rstrip('/')}/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
    }

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_query}
        ],
        "max_tokens": 500, # 응답 최대 토큰 수
        "temperature": 0.7, # 창의성 조절
    }

    try:
        response = requests.post(chat_completions_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생

        response_data = response.json()
        # 응답 구조에 따라 텍스트 추출
        if response_data and response_data.get("choices"):
            return response_data["choices"][0]["message"]["content"].strip()
        else:
            print(f"vLLM 응답 형식 오류: {response_data}")
            return "vLLM으로부터 유효한 응답을 받지 못했습니다."

    except requests.exceptions.RequestException as e:
        print(f"vLLM API 요청 중 오류 발생: {e}")
        return f"vLLM API 통신 오류: {e}"
    except json.JSONDecodeError as e:
        print(f"vLLM 응답 JSON 디코딩 오류: {e}")
        return "vLLM 응답을 처리하는 중 오류이 발생했습니다."
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")
        return "알 수 없는 오류가 발생했습니다."


def get_chatbot_response(user_query: str) -> str:
    """
    사용자 쿼리를 받아 vLLM 모델로부터 응답을 생성합니다.
    """
    # 기존 model 변수 대신 vLLM API 사용
    return get_vllm_response(user_query)
from typing import Dict, Any
import sys
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 파이프라인 루트 경로를 Python 경로에 추가
PIPELINE_ROOT = Path(__file__).parent.parent
sys.path.append(str(PIPELINE_ROOT))
from ..config import config

class IntentClassifier:
    """2단계 의도 분류 컴포넌트 (OpenAI GPT-4o 사용)"""
    
    def __init__(self):
        # config.py에서 프롬프트만 가져오기
        self.initial_prompt_template = config.INITIAL_INTENT_CLASSIFICATION_PROMPT
        self.image_generation_prompt_template = config.IMAGE_GENERATION_INTENT_CLASSIFICATION_PROMPT
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
    
    def _call_openai_api(self, prompt: str, max_tokens: int = 50) -> str:
        """OpenAI API를 호출하여 응답 생성"""
        if not self.openai_api_key:
            print("OPENAI_API_KEY가 설정되지 않았습니다. 기본값을 반환합니다.")
            return "image_generation"  # 기본값을 image_generation으로 변경
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "당신은 사용자 의도를 정확히 분류하는 AI입니다. 주어진 옵션 중에서 정확히 하나만 답변하세요."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.1  # 낮은 온도로 일관성 있는 분류
        }
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            print(f"OpenAI API 호출 실패: {e}")
            return "rag"  # 기본값
    
    def classify_initial_intent(self, user_query: str) -> str:
        """1단계: 사용자 쿼리의 초기 의도를 분류"""
        try:
            # 초기 의도 분류 프롬프트 생성
            prompt = self.initial_prompt_template.format(user_query=user_query)
            
            # OpenAI API를 사용하여 초기 의도 분류
            response = self._call_openai_api(prompt, max_tokens=20)
            
            # 응답 정제
            intent = self._extract_initial_intent(response)
            
            print(f"초기 의도 분류 결과: '{response}' -> '{intent}'")
            
            # 유효한 의도인지 확인
            valid_intents = ["rag", "image_generation", "image_modification", "general_conversation"]
            if intent in valid_intents:
                return intent
            else:
                # 기본값으로 general_conversation 반환
                print(f"유효하지 않은 의도 '{intent}', 기본값 'general_conversation' 반환")
                return "general_conversation"
        
        except Exception as e:
            print(f"초기 의도 분류 실패: {e}")
            return "general_conversation"
    
    def classify_image_generation_intent(self, user_query: str) -> str:
        """2단계: 이미지 생성 방식 분류"""
        try:
            # 이미지 생성 의도 분류 프롬프트 생성
            prompt = self.image_generation_prompt_template.format(user_query=user_query)
            
            # OpenAI API를 사용하여 이미지 생성 의도 분류
            response = self._call_openai_api(prompt, max_tokens=20)
            
            # 응답 정제
            intent = self._extract_image_generation_intent(response)
            
            print(f"이미지 생성 의도 분류 결과: '{response}' -> '{intent}'")
            
            # 유효한 의도인지 확인
            valid_intents = ["guided", "direct"]
            if intent in valid_intents:
                return intent
            else:
                # 기본값으로 guided 반환
                print(f"유효하지 않은 이미지 생성 의도 '{intent}', 기본값 'guided' 반환")
                return "guided"
        
        except Exception as e:
            print(f"이미지 생성 의도 분류 실패: {e}")
            return "guided"
    
    def _extract_initial_intent(self, response: str) -> str:
        """1단계 의도 추출"""
        response = response.strip().lower()
        
        if "image_modification" in response:
            return "image_modification"
        elif "image_generation" in response:
            return "image_generation"
        elif "general_conversation" in response:
            return "general_conversation"
        elif "rag" in response:
            return "rag"
        else:
            return "general_conversation"  # 기본값을 general_conversation으로 변경
    
    def _extract_image_generation_intent(self, response: str) -> str:
        """2단계 이미지 생성 의도 추출"""
        response = response.strip().lower()
        
        if "direct" in response:
            return "direct"
        elif "guided" in response:
            return "guided"
        else:
            return "guided"  # 기본값
    
    def classify_modification_intent(self, user_input: str) -> str:
        """이미지 수정 의도 분류"""
        prompt = f"""
사용자의 입력을 분석하여 이미지 수정 의도를 판단해주세요.

사용자 입력: "{user_input}"

다음 중 하나로 분류해주세요:
- modify: 이미지 수정을 원함 (색상 변경, 디자인 요소 추가/제거, 스타일 변경 등)
- no_modify: 이미지 수정을 원하지 않음 (아니오, 괜찮습니다, 수정 안함 등)

분류 결과만 답변해주세요:
"""
        
        response = self._call_openai_api(prompt, max_tokens=20)
        return self._extract_modification_intent(response)
    
    def _extract_modification_intent(self, response: str) -> str:
        """수정 의도 추출"""
        response = response.strip().lower()
        
        if "modify" in response:
            return "modify"
        else:
            return "no_modify"
    
    
# 전역 의도 분류기 인스턴스
intent_classifier = IntentClassifier()

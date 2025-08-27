from typing import Dict, Any
from ..config import config
from ..llm_provider import kanana_llm_model

class IntentClassifier:
    """의도 분류 컴포넌트"""
    
    def __init__(self):
        self.intent_classes = config.INTENT_CLASSES
        self.prompt_template = config.INTENT_CLASSIFICATION_PROMPT
    
    def classify_intent(self, user_query: str) -> str:
        """사용자 쿼리의 의도를 분류"""
        try:
            # 의도 분류 프롬프트 생성
            prompt = self.prompt_template.format(user_query=user_query)
            
            # LLM을 사용하여 의도 분류
            response = kanana_llm_model.generate_response(prompt, max_length=100)
            
            # 응답 정제
            intent = self._extract_intent(response)
            
            # 유효한 의도인지 확인
            if intent in self.intent_classes:
                return intent
            else:
                # 기본값으로 text_generation 반환
                return "text_generation"
        
        except Exception as e:
            print(f"의도 분류 실패: {e}")
            return "text_generation"
    
    def _extract_intent(self, response: str) -> str:
        """LLM 응답에서 의도 추출"""
        response = response.strip().lower()
        
        # 응답에서 의도 키워드 찾기
        if "text_generation" in response:
            return "text_generation"
        elif "image_modification" in response:
            return "image_modification"
        elif "이미지" in response or "수정" in response:
            return "image_modification"
        else:
            return "text_generation"
    
    def get_intent_description(self, intent: str) -> str:
        """의도에 대한 설명 반환"""
        return self.intent_classes.get(intent, "알 수 없는 의도")

# 전역 의도 분류기 인스턴스
intent_classifier = IntentClassifier()

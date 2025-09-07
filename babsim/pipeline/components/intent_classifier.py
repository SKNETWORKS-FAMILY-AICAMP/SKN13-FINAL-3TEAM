from typing import Dict, Any
import sys
import os
from pathlib import Path

# 파이프라인 루트 경로를 Python 경로에 추가
PIPELINE_ROOT = Path(__file__).parent.parent
sys.path.append(str(PIPELINE_ROOT))

from pipeline.config import config
from pipeline.llm_provider import kanana_llm_model

class IntentClassifier:
    """의도 분류 컴포넌트"""
    
    def __init__(self):
        self.intent_classes = config.INTENT_CLASSES
        self.prompt_template = config.INTENT_CLASSIFICATION_PROMPT
    
    def classify_intent(self, user_query: str) -> str:
        """2단계 의도 분류: Rule-based → LLM 재확인"""
        print(f"🎯 의도 분류 시작: '{user_query}'")
        
        try:
            # 1단계: Rule-based 분류
            rule_based_intent = self.classify_intent_rule_based(user_query)
            print(f"🔍 1단계 Rule-based 분류: {rule_based_intent}")
            
            # 2단계: LLM으로 재확인
            confirmed_intent = self._confirm_intent_with_llm(user_query, rule_based_intent)
            print(f"✅ 2단계 LLM 재확인: {confirmed_intent}")
            
            # 최종 결과 로깅
            if rule_based_intent == confirmed_intent:
                print(f"🎉 분류 일치: {confirmed_intent}")
            else:
                # 기본값으로 rag 반환
                return "rag"
        
        except Exception as e:
            print(f"의도 분류 실패: {e}")
            return "rag"
    
    def _extract_intent(self, response: str) -> str:
        """LLM 응답에서 의도 추출"""
        response = response.strip().lower()
        
        # 응답에서 의도 키워드 찾기
        if "rag" in response:
            return "rag"
        elif "general" in response:
            return "general"
        elif "안녕" in response or "하이" in response or "인사" in response:
            return "general"
        else:
            return "rag"
    
    def _confirm_intent_with_llm(self, user_query: str, rule_based_intent: str) -> str:
        """LLM으로 rule-based 결과를 재확인"""
        try:
            # 재확인 프롬프트 생성
            confirmation_prompt = f"""
다음 사용자 질문을 분석하고, 제시된 의도 분류가 적절한지 확인해주세요.

사용자 질문: {user_query}
Rule-based 분류 결과: {rule_based_intent}

의도 분류 옵션:
1. text_generation: 현대자동차나 자동차에 대한 지식 질문
2. image_generation: 이미지 생성, 그리기, 만들기 요청
3. 3D_generation: 3D 모델 생성, 3D 객체 만들기 요청
4. 4D_generation: 4D 모델 생성, 4D 객체 만들기 요청
5. image_modification: 이미지를 첨부하고 수정을 요청하는 질문

제시된 분류가 적절하다면 그대로 답변하고, 그렇지 않다면 올바른 의도를 답변해주세요.
의도만 간단히 답변해주세요 (text_generation, image_generation, 3D_generation, 4D_generation, image_modification 중 하나):
"""
            
            # LLM을 사용하여 재확인
            response = kanana_llm_model.generate_response(confirmation_prompt, max_length=50)
            
            # 응답에서 의도 추출
            confirmed_intent = self._extract_intent(response)
            
            # 유효한 의도인지 확인
            if confirmed_intent in self.intent_classes:
                return confirmed_intent
            else:
                # 유효하지 않으면 rule-based 결과 사용
                return rule_based_intent
                
        except Exception as e:
            print(f"LLM 재확인 실패: {e}")
            # 실패 시 rule-based 결과 사용
            return rule_based_intent

    def classify_intent_rule_based(self, user_query: str) -> str:
        """Rule-based 의도 분류 (LLM 없이 키워드 기반)"""
        query_lower = user_query.lower()
        
        # 4D 생성 키워드 (가장 구체적, 우선순위 높음)
        d4_keywords = ["4d", "4차원", "4차원모델", "4d모델", "4d 모델", "4차원 모델", "4d object", "4d object", "4차원 객체"]
        
        # 3D 생성 키워드
        d3_keywords = ["3d", "3차원", "3차원모델", "3d모델", "3d 모델", "3차원 모델", "3d object", "3d object", "3차원 객체"]
        
        # 이미지 수정 키워드
        modification_keywords = ["수정", "편집", "변경", "바꿔", "고쳐", "modify", "edit", "change", "조정", "개선"]
        
        # 이미지 생성 키워드 (일반적인 생성 요청)
        image_keywords = ["이미지", "그림", "그리기", "만들기", "생성", "draw", "image", "picture", "generate", "디자인"]
        image_creation_keywords = ["그려", "그려줘", "만들어", "만들어줘", "생성해", "생성해줘", "디자인해", "디자인해줘"]
        
        # 텍스트 질문 키워드 (현대차/자동차 관련)
        text_keywords = ["현대차", "현대자동차", "자동차", "차량", "모델", "스펙", "가격", "성능", "디자인", "기술", "질문", "알려줘", "설명"]
        
        # 4D 생성 체크 (가장 구체적)
        if any(keyword in query_lower for keyword in d4_keywords):
            return "4D_generation"
        
        # 3D 생성 체크
        elif any(keyword in query_lower for keyword in d3_keywords):
            return "3D_generation"
        
        # 이미지 수정 체크 (이미지 관련 + 수정 키워드)
        elif any(keyword in query_lower for keyword in modification_keywords) and any(keyword in query_lower for keyword in image_keywords):
            return "image_modification"
        
        # 이미지 생성 체크 (생성 키워드 + 이미지 관련)
        elif any(keyword in query_lower for keyword in image_keywords) or any(keyword in query_lower for keyword in image_creation_keywords):
            return "image_generation"
        
        # 텍스트 질문 체크 (현대차/자동차 관련 질문)
        elif any(keyword in query_lower for keyword in text_keywords):
            return "text_generation"
        
        # 기본값 (명확하지 않은 경우)
>>>>>>> Stashed changes
        else:
            return "rag"
    
    def get_intent_description(self, intent: str) -> str:
        """의도에 대한 설명 반환"""
        return self.intent_classes.get(intent, "알 수 없는 의도")
    
    def test_classification(self, test_queries: list) -> None:
        """의도 분류 테스트"""
        print("🧪 의도 분류 테스트 시작")
        print("=" * 50)
        
        for query in test_queries:
            print(f"\n📝 테스트 쿼리: '{query}'")
            result = self.classify_intent(query)
            print(f"🎯 최종 결과: {result}")
            print("-" * 30)

# 전역 의도 분류기 인스턴스
intent_classifier = IntentClassifier()

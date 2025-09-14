from typing import Dict, Any, List
import sys
import os
from pathlib import Path

# 파이프라인 루트 경로를 Python 경로에 추가
PIPELINE_ROOT = Path(__file__).parent.parent
sys.path.append(str(PIPELINE_ROOT))

from pipeline.config import config
from pipeline.llm_provider import kanana_llm_model

class ImageQueryGenerator:
    """이미지 생성 쿼리 생성 컴포넌트"""
    
    def __init__(self):
        self.car_prompt_template = self._get_car_prompt_template()
    
    def _get_car_prompt_template(self) -> str:
        """자동차 프롬프트 템플릿 반환"""
        return """
"Designed by Hyundai, {뷰포인트}, {차체 크기 등급} {차체 유형}, {형태}, 
{비율}, {차체 표면}, {전면부/측면부 요소}, {조명}, {휠/타이어}, 
{유리/그린하우스}, {공기역학/추가 요소}, {색상 & 마감}"
"""
    
    def generate_image_query(self, state) -> str:
        """state에서 chat_history를 가져와서 이미지 생성 쿼리 생성"""
        try:
            # state에서 chat_history 추출
            chat_history = state.get("chat_history", [])
            
            # 대화 기록에서 폼 정보 추출
            form_data = self._extract_form_data(chat_history)
            
            # 이미지 생성 쿼리 생성 프롬프트
            prompt = self._create_query_generation_prompt(form_data, chat_history)
            
            # LLM을 사용하여 쿼리 생성
            query = kanana_llm_model.generate_vllm_response_text(prompt, max_length=512)
            
            return query.strip()
        
        except Exception as e:
            print(f"이미지 쿼리 생성 실패: {e}")
            return "이미지 쿼리 생성에 실패했습니다."
    
    def generate_image_query_from_chat(self, chat_history: List[Dict[str, str]], desc: str = "") -> str:
        """chat_history와 desc를 이용하여 이미지 생성 쿼리 생성 (폼 데이터 없이)"""
        try:
            # 이미지 생성 쿼리 생성 프롬프트
            prompt = self._create_chat_based_query_prompt(chat_history, desc)
            
            # LLM을 사용하여 쿼리 생성
            query = kanana_llm_model.generate_vllm_response_text(prompt, max_length=512)
            
            return query.strip()
        
        except Exception as e:
            print(f"채팅 기반 이미지 쿼리 생성 실패: {e}")
            return "이미지 쿼리 생성에 실패했습니다."
    
    def _extract_form_data(self, chat_history: List[Dict[str, str]]) -> Dict[str, str]:
        """대화 기록에서 폼 데이터 추출"""
        form_data = {
            "뷰포인트": "",
            "차체 크기 등급": "",
            "차체 유형": "",
            "형태": "",
            "비율": "",
            "차체 표면": "",
            "전면부/측면부 요소": "",
            "조명": "",
            "휠/타이어": "",
            "유리/그린하우스": "",
            "공기역학/추가 요소": "",
            "색상 & 마감": ""
        }
        
        # 대화 기록에서 폼 필드 정보 추출
        for message in chat_history:
            content = message.get("content", "")
            
            # 각 필드별로 정보 추출
            if "뷰포인트" in content or "viewpoint" in content.lower():
                form_data["뷰포인트"] = self._extract_field_value(content, "뷰포인트")
            
            if "차체 크기" in content or "size" in content.lower():
                form_data["차체 크기 등급"] = self._extract_field_value(content, "차체 크기")
            
            if "차체 유형" in content or "body type" in content.lower():
                form_data["차체 유형"] = self._extract_field_value(content, "차체 유형")
            
            if "형태" in content or "form" in content.lower():
                form_data["형태"] = self._extract_field_value(content, "형태")
            
            if "비율" in content or "proportion" in content.lower():
                form_data["비율"] = self._extract_field_value(content, "비율")
            
            if "차체 표면" in content or "body surface" in content.lower():
                form_data["차체 표면"] = self._extract_field_value(content, "차체 표면")
            
            if "조명" in content or "light" in content.lower():
                form_data["조명"] = self._extract_field_value(content, "조명")
            
            if "휠" in content or "wheel" in content.lower():
                form_data["휠/타이어"] = self._extract_field_value(content, "휠")
            
            if "색상" in content or "color" in content.lower():
                form_data["색상 & 마감"] = self._extract_field_value(content, "색상")
        
        return form_data
    
    def _extract_field_value(self, content: str, field_name: str) -> str:
        """특정 필드의 값을 추출"""
        # 간단한 키워드 기반 추출
        keywords = {
            "뷰포인트": ["front view", "3/4 front view", "side view", "rear view"],
            "차체 크기": ["소형", "준중형", "중형", "대형", "small", "medium", "large"],
            "차체 유형": ["SUV", "세단", "쿠페", "해치백", "픽업", "밴"],
            "형태": ["two-box", "three-box"],
            "차체 표면": ["clean", "taut", "soft", "chamfers", "bulges"],
            "조명": ["LED", "halogen", "xenon", "modern", "classic"],
            "휠": ["alloy", "steel", "sport", "luxury"],
            "색상": ["red", "blue", "white", "black", "silver", "gray"]
        }
        
        field_keywords = keywords.get(field_name, [])
        for keyword in field_keywords:
            if keyword.lower() in content.lower():
                return keyword
        
        return ""
    
    def _create_query_generation_prompt(self, form_data: Dict[str, str], chat_history: List[Dict[str, str]]) -> str:
        """쿼리 생성 프롬프트 생성"""
        # 대화 기록 요약
        conversation_summary = self._summarize_conversation(chat_history)
        
        # 폼 데이터 요약
        form_summary = self._summarize_form_data(form_data)
        
        prompt = f"""
다음 대화와 폼 데이터를 바탕으로 Stable Diffusion용 자동차 이미지 생성 쿼리를 생성해주세요.

대화 요약:
{conversation_summary}

폼 데이터:
{form_summary}

템플릿:
{self.car_prompt_template}

위 템플릿을 사용하여 완성된 이미지 생성 쿼리를 생성해주세요. 
빈 필드는 적절한 기본값으로 채워주시고, 대화 내용에서 추출한 정보를 반영해주세요.
쿼리는 영어로 작성해주세요. 77 CLIP token 이내로 작성해주세요.

이미지 생성 쿼리:
"""
        return prompt
    
    def _summarize_conversation(self, chat_history: List[Dict[str, str]]) -> str:
        """대화 요약"""
        user_messages = [msg.get("content", "") for msg in chat_history if msg.get("role") == "user"]
        return " ".join(user_messages[-5:])  # 최근 5개 사용자 메시지만
    
    def _summarize_form_data(self, form_data: Dict[str, str]) -> str:
        """폼 데이터 요약"""
        summary_parts = []
        for field, value in form_data.items():
            if value:
                summary_parts.append(f"{field}: {value}")
        
        return "\n".join(summary_parts) if summary_parts else "폼 데이터가 없습니다."
    
    
    def _create_chat_based_query_prompt(self, chat_history: List[Dict[str, str]], desc: str = "") -> str:
        """채팅 기반 쿼리 생성 프롬프트 생성"""
        # 대화 기록 요약
        conversation_summary = self._summarize_conversation(chat_history)
        
        # 설명 추가
        desc_text = f"\n추가 설명: {desc}" if desc else ""
        
        prompt = f"""
다음 대화 내용을 바탕으로 Stable Diffusion용 자동차 이미지 생성 쿼리를 생성해주세요.

대화 요약:
{conversation_summary}
{desc_text}

템플릿:
{self.car_prompt_template}

위 템플릿을 사용하여 완성된 이미지 생성 쿼리를 생성해주세요.
대화 내용에서 자동차 디자인 관련 정보를 추출하여 반영하고, 빈 필드는 적절한 기본값으로 채워주세요.
쿼리는 영어로 작성해주세요. 77 CLIP token 이내로 작성해주세요.
단, 답변은 최대한 키워드 위주로만 작성해주세요.

이미지 생성 쿼리:
"""
        return prompt
    
    def generate_image_query_from_checklist(self, checklist_data: Dict[str, Any]) -> str:
        """체크리스트 데이터를 기반으로 이미지 생성 쿼리 생성"""
        try:
            print(f"🔍 [분기] 체크리스트 기반 이미지 쿼리 생성 시작")
            
            # 체크리스트 데이터를 텍스트로 변환
            query_parts = []
            
            # 필수 필드들
            if checklist_data.get('viewpoint'):
                query_parts.append(f"Viewpoint: {checklist_data['viewpoint']}")
            if checklist_data.get('body_type'):
                query_parts.append(f"Body type: {checklist_data['body_type']}")
            if checklist_data.get('color_finish'):
                query_parts.append(f"Color/Finish: {checklist_data['color_finish']}")
            
            # 선택 필드들
            optional_fields = ['size_class', 'proportions', 'surface', 'front_elements', 
                             'side_elements', 'lighting', 'glasshouse', 'aero', 'wheel']
            
            for field in optional_fields:
                if checklist_data.get(field) and checklist_data[field].strip():
                    query_parts.append(f"{field.replace('_', ' ').title()}: {checklist_data[field]}")
            
            # 쿼리 조합
            image_query = ", ".join(query_parts)
            print(f"🔍 생성된 이미지 쿼리: {image_query}")
            
            return image_query
            
        except Exception as e:
            print(f"❌ 체크리스트 이미지 쿼리 생성 실패: {e}")
            return "car design based on checklist"


# 전역 이미지 쿼리 생성기 인스턴스
image_query_generator = ImageQueryGenerator()

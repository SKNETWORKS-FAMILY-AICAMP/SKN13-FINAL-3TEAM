from __future__ import annotations
from typing import Dict, List, Optional
import sys
import os
from pathlib import Path

# 파이프라인 루트 경로를 Python 경로에 추가
PIPELINE_ROOT = Path(__file__).parent.parent
sys.path.append(str(PIPELINE_ROOT))

from pipeline.llm_provider import kanana_llm_model

REQUIRED_FIELDS = [
    "viewpoint", "body_type", "size_class", "proportions", "surface",
    "front_elements", "side_elements", "lighting", "glasshouse",
    "aero", "color_finish"
]

class ChecklistGenerator:
    def __init__(self):
        self.required_fields = REQUIRED_FIELDS
        self.field_descriptions = {
            "viewpoint": "시점 (앞면, 측면, 3/4 뷰 등)",
            "body_type": "차체 타입 (SUV, 세단, 쿠페, 해치백 등)",
            "size_class": "크기 분류 (소형, 중형, 대형 등)",
            "proportions": "비율 (전장, 전폭, 전고 비율)",
            "surface": "표면 처리 (곡선, 직선, 각진 형태)",
            "front_elements": "전면 요소 (그릴, 헤드라이트, 범퍼)",
            "side_elements": "측면 요소 (도어, 휠, 사이드 미러)",
            "lighting": "조명 (헤드라이트, 테일라이트, DRL)",
            "glasshouse": "유리창 (윈드실드, 사이드 윈도우, 선루프)",
            "aero": "공기역학 (스포일러, 디퓨저, 공기 흐름)",
            "color_finish": "색상 및 마감 (메탈릭, 펄, 매트 등)"
        }
        self.field_examples = {
            "viewpoint": "front 3/4 view, front view, side view, rear view",
            "body_type": "SUV, sedan, coupe, hatchback, crossover",
            "size_class": "compact, mid-size, full-size, luxury",
            "proportions": "long hood, short overhang, wide stance",
            "surface": "curved surfaces, sharp lines, flowing design",
            "front_elements": "large grille, LED headlights, sporty bumper",
            "side_elements": "flush door handles, large wheels, side skirts",
            "lighting": "LED DRL, matrix headlights, sequential turn signals",
            "glasshouse": "panoramic sunroof, black pillars, large windows",
            "aero": "active spoiler, air curtains, underbody panels",
            "color_finish": "metallic silver, pearl white, matte black"
        }

    def missing_fields(self, form_data: Dict[str, str]) -> List[str]:
        """누락된 필드 목록 반환"""
        return [f for f in self.required_fields if not form_data.get(f)]

    def next_question(self, missing: List[str]) -> str:
        """다음 질문 생성"""
        if not missing: 
            return "모든 정보가 수집되었습니다. 이미지 생성을 시작할까요?"
        
        # 우선순위 설정
        priority = ["viewpoint", "body_type", "color_finish", "size_class", "proportions"]
        missing.sort(key=lambda x: (x not in priority, priority.index(x) if x in priority else 99))
        target = missing[0]
        
        description = self.field_descriptions.get(target, target)
        examples = self.field_examples.get(target, "자유 입력")
        
        return f"이미지 생성을 위해 '{description}' 정보를 알려주세요.\n예시: {examples}"

    def extract_form_data(self, chat_history: List[Dict[str, str]]) -> Dict[str, str]:
        """대화 기록에서 폼 데이터 추출"""
        form_data = {}
        
        for message in chat_history:
            if message.get("role") == "user":
                content = message.get("content", "").lower()
                
                # 각 필드에 대한 키워드 매칭
                for field in self.required_fields:
                    if self._is_field_mentioned(content, field):
                        form_data[field] = message.get("content", "")
        
        return form_data

    def _is_field_mentioned(self, content: str, field: str) -> bool:
        """특정 필드가 언급되었는지 확인"""
        field_keywords = {
            "viewpoint": ["시점", "뷰", "view", "앞면", "측면", "3/4", "front", "side"],
            "body_type": ["차체", "타입", "body", "suv", "세단", "sedan", "쿠페", "coupe"],
            "size_class": ["크기", "size", "소형", "중형", "대형", "compact", "mid-size"],
            "proportions": ["비율", "proportion", "전장", "전폭", "전고"],
            "surface": ["표면", "surface", "곡선", "직선", "curved", "sharp"],
            "front_elements": ["전면", "front", "그릴", "헤드라이트", "grille", "headlight"],
            "side_elements": ["측면", "side", "도어", "휠", "door", "wheel"],
            "lighting": ["조명", "lighting", "라이트", "light", "led"],
            "glasshouse": ["유리", "glass", "윈도우", "window", "선루프", "sunroof"],
            "aero": ["공기역학", "aero", "스포일러", "spoiler", "디퓨저", "diffuser"],
            "color_finish": ["색상", "color", "마감", "finish", "메탈릭", "metallic"]
        }
        
        keywords = field_keywords.get(field, [])
        return any(keyword in content for keyword in keywords)

    def generate_follow_up_with_checklist(self, user_query: str, response: str, form_data: Dict[str, str]) -> str:
        """체크리스트 기반 후속 질문 생성"""
        try:
            missing_fields = self.missing_fields(form_data)
            
            if not missing_fields:
                return "모든 정보가 수집되었습니다. 이미지 생성을 시작할까요?"
            
            # LLM을 사용하여 자연스러운 후속 질문 생성
            prompt = f"""
다음 대화에서 사용자에게 자연스럽게 다음 정보를 요청하는 질문을 생성해주세요.

사용자 질문: {user_query}
어시스턴트 답변: {response}

누락된 정보: {', '.join(missing_fields)}
다음 우선순위: {missing_fields[0] if missing_fields else '없음'}

자연스럽고 친근한 후속 질문을 생성해주세요 (한 문장):
"""
            
            follow_up = kanana_llm_model.generate_response(prompt, max_length=150)
            return follow_up.strip()
            
        except Exception as e:
            print(f"체크리스트 기반 후속 질문 생성 실패: {e}")
            return self.next_question(missing_fields)

    def get_completion_status(self, form_data: Dict[str, str]) -> Dict[str, any]:
        """완성도 상태 반환"""
        missing = self.missing_fields(form_data)
        completed = len(self.required_fields) - len(missing)
        total = len(self.required_fields)
        percentage = (completed / total) * 100
        
        return {
            "completed": completed,
            "total": total,
            "percentage": percentage,
            "missing_fields": missing,
            "is_complete": len(missing) == 0
        }

checklist_generator = ChecklistGenerator()
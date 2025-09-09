from __future__ import annotations
from typing import Dict, List, Optional, Any
import sys
import os
import json
import re
from pathlib import Path
from pipeline.llm_provider import kanana_llm_model

# 파이프라인 루트 경로를 Python 경로에 추가
PIPELINE_ROOT = Path(__file__).parent.parent
sys.path.append(str(PIPELINE_ROOT))

# 필수 요소 (우선순위 높음)
REQUIRED_FIELDS = [
    "viewpoint", "body_type", "color_finish"
]

# 선택 요소 (우선순위 낮음)
OPTIONAL_FIELDS = [
    "size_class", "proportions", "surface",
    "front_elements", "side_elements", "lighting", "glasshouse",
    "aero", "wheel" # 휠 추가
]

# 전체 필드
ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS

class ChecklistGenerator:
    def __init__(self):
        self.required_fields = REQUIRED_FIELDS
        self.optional_fields = OPTIONAL_FIELDS
        self.all_fields = ALL_FIELDS
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
            "color_finish": "색상 및 마감 (메탈릭, 펄, 매트 등)",
            "wheel": "휠 디자인 (휠 모양, 크기, 색상 등)"
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
            "color_finish": "metallic silver, pearl white, matte black",
            "wheel": "spoke wheels, turbine-style wheels, large black wheels"
        }

    def missing_fields(self, form_data: Dict[str, str]) -> List[str]:
        """누락된 필드 목록 반환 (필수 요소 우선)"""
        missing_required = [f for f in self.required_fields if not form_data.get(f)]
        missing_optional = [f for f in self.optional_fields if not form_data.get(f)]
        return missing_required + missing_optional
    
    def missing_required_fields(self, form_data: Dict[str, str]) -> List[str]:
        """누락된 필수 필드만 반환"""
        return [f for f in self.required_fields if not form_data.get(f)]
    
    def missing_optional_fields(self, form_data: Dict[str, str]) -> List[str]:
        """누락된 선택 필드만 반환"""
        return [f for f in self.optional_fields if not form_data.get(f)]

    def next_question(self, missing: List[str], form_data: Dict[str, str] = None) -> str:
        """다음 질문 생성 (단계별 진행)"""
        if not missing: 
            return "🎉 모든 정보가 수집되었습니다! 이미지 생성을 시작할까요?"
        
        if form_data is None:
            form_data = {}
        
        # 필수 요소가 남아있으면 필수 요소부터
        missing_required = self.missing_required_fields(form_data)
        if missing_required:
            target = missing_required[0]
            is_required = True
        else:
            # 필수 요소가 모두 채워졌으면 선택 요소
            target = missing[0]
            is_required = False
        
        description = self.field_descriptions.get(target, target)
        examples = self.field_examples.get(target, "자유 입력")
        
        # 진행 상황 표시
        completed = len(self.all_fields) - len(self.missing_fields(form_data))
        total = len(self.all_fields)
        progress = f"({completed}/{total})"
        
        if is_required:
            return f"📋 **필수 정보** {progress}\n\n'{description}'을 선택해주세요!\n\n💡 예시: {examples}\n\n이 정보는 이미지 생성에 꼭 필요합니다."
        else:
            return f"📋 **추가 정보** {progress}\n\n'{description}'에 대해 알려주세요.\n\n💡 예시: {examples}\n\n(선택사항이므로 건너뛰셔도 됩니다)"

    def extract_form_data(self, chat_history: List[Dict[str, str]]) -> Dict[str, str]:
        """대화 기록에서 폼 데이터 추출"""
        form_data = {}
        
        for message in chat_history:
            if message.get("role") == "user":
                # 여기서는 단순히 키워드 매칭이 아닌, 대화 기록 전체를 LLM에 전달하여 추출
                # 그러나 이 함수는 pipeline에서 사용하지 않으므로 (auto_fill_from_description을 직접 사용)
                # 현재 로직을 유지해도 무방합니다.
                pass
        
        return form_data
    
    def auto_fill_from_description(self, user_query: str) -> Dict[str, str]:
        """사용자 설명에서 자동으로 체크리스트 채우기 (Kanana LLM 기반)"""
        try:
            # Kanana LLM을 사용한 자동 채우기 시도
            llm_filled_data = self._auto_fill_with_kanana_llm(user_query)
            if llm_filled_data:
                print(f"Kanana LLM 자동 채우기 결과: {llm_filled_data}")
                return llm_filled_data
        except Exception as e:
            print(f"Kanana LLM 자동 채우기 실패: {e}")
        
        # LLM 실패 시 키워드 기반 폴백
        return self._auto_fill_with_keywords(user_query)
    
    def _auto_fill_with_kanana_llm(self, user_query: str) -> Dict[str, str]:
        """Kanana LLM을 사용한 정교한 자동 채우기"""
        prompt = f"""다음 사용자 설명에서 자동차 디자인 정보를 추출해주세요:

사용자 설명: "{user_query}"

다음 필드들을 JSON 형태로 추출해주세요:
- viewpoint: 시점 (front view, side view, rear view, 3/4 view 중 하나)
- body_type: 차체 타입 (SUV, sedan, coupe, hatchback, crossover 중 하나)
- size_class: 크기 분류 (compact, mid-size, full-size, luxury 중 하나)
- color_finish: 색상 (red, blue, black, white, silver, gold, metallic, pearl, matte 등)
- proportions: 비율 (long hood, short overhang, wide stance 등)
- surface: 표면 (curved surfaces, sharp lines, flowing design 등)
- front_elements: 전면 요소 (large grille, LED headlights, sporty bumper 등)
- side_elements: 측면 요소 (flush door handles, large wheels, side skirts 등)
- lighting: 조명 (LED DRL, matrix headlights, sequential turn signals 등)
- glasshouse: 유리창 (panoramic sunroof, black pillars, large windows 등)
- aero: 공기역학 (active spoiler, air curtains, underbody panels 등)
- wheel: 휠 (spoke wheels, turbine-style wheels, large black wheels 등)

추출할 수 없는 정보는 빈 문자열("")로 표시하세요.
반드시 다음 JSON 형식으로만 답변하세요:
{{"viewpoint": "", "body_type": "", "size_class": "", "color_finish": "", "proportions": "", "surface": "", "front_elements": "", "side_elements": "", "lighting": "", "glasshouse": "", "aero": "", "wheel": ""}}"""

        try:
            response = kanana_llm_model.generate_response(prompt, max_length=200, temperature=0.2)
            print(f"Kanana LLM 응답: {response}")
            
            # JSON 부분만 추출 (중첩된 중괄호도 처리)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                try:
                    parsed_data = json.loads(json_str)
                    
                    # 빈 값이 아닌 것만 반환
                    filtered_data = {k: v for k, v in parsed_data.items() if v and str(v).strip()}
                    print(f"파싱된 데이터: {filtered_data}")
                    return filtered_data
                except json.JSONDecodeError as e:
                    print(f"JSON 파싱 오류: {e}")
                    print(f"원본 응답: {response}")
                    return {}
            else:
                print("JSON 형식을 찾을 수 없음")
                print(f"원본 응답: {response}")
                return {}
                
        except Exception as e:
            print(f"Kanana LLM JSON 파싱 실패: {e}")
            return {}
    
    def _auto_fill_with_keywords(self, user_query: str) -> Dict[str, str]:
        """키워드 기반 폴백 자동 채우기"""
        form_data = {}
        query_lower = user_query.lower()
        
        # 자동 매칭 로직
        auto_fill_rules = {
            "viewpoint": {
                "front": "front view",
                "side": "side view", 
                "rear": "rear view",
                "3/4": "3/4 view",
                "앞면": "front view",
                "측면": "side view",
                "후면": "rear view",
                "옆면": "side view",
                "정면": "front view"
            },
            "body_type": {
                "suv": "SUV",
                "세단": "sedan",
                "sedan": "sedan",
                "쿠페": "coupe",
                "coupe": "coupe",
                "해치백": "hatchback",
                "hatchback": "hatchback",
                "크로스오버": "crossover",
                "crossover": "crossover"
            },
            "color_finish": {
                "빨간": "red",
                "red": "red",
                "파란": "blue", 
                "blue": "blue",
                "검은": "black",
                "black": "black",
                "흰": "white",
                "white": "white",
                "은색": "silver",
                "silver": "silver",
                "금색": "gold",
                "gold": "gold",
                "메탈릭": "metallic",
                "metallic": "metallic",
                "펄": "pearl",
                "pearl": "pearl",
                "매트": "matte",
                "matte": "matte"
            }
        }
        
        for field, rules in auto_fill_rules.items():
            for keyword, value in rules.items():
                if keyword in query_lower:
                    form_data[field] = value
                    break
        
        return form_data

    def _is_field_mentioned(self, content: str, field: str) -> bool:
        """특정 필드가 언급되었는지 확인"""
        field_keywords = {
            "viewpoint": ["시점", "뷰", "view", "앞면", "측면", "3/4", "front", "side", "옆면"],
            "body_type": ["차체", "타입", "body", "suv", "세단", "sedan", "쿠페", "coupe", "해치백"],
            "size_class": ["크기", "size", "소형", "중형", "대형", "compact", "mid-size"],
            "proportions": ["비율", "proportion", "전장", "전폭", "전고"],
            "surface": ["표면", "surface", "곡선", "직선", "curved", "sharp"],
            "front_elements": ["전면", "front", "그릴", "헤드라이트", "grille", "headlight"],
            "side_elements": ["측면", "side", "도어", "휠", "door", "wheel"],
            "lighting": ["조명", "lighting", "라이트", "light", "led"],
            "glasshouse": ["유리", "glass", "윈도우", "window", "선루프", "sunroof"],
            "aero": ["공기역학", "aero", "스포일러", "spoiler", "디퓨저", "diffuser"],
            "color_finish": ["색상", "color", "마감", "finish", "메탈릭", "metallic"],
            "wheel": ["휠", "wheel"]
        }
        
        keywords = field_keywords.get(field, [])
        return any(keyword in content for keyword in keywords)

    def generate_follow_up_with_checklist(self, user_query: str, last_response: str, form_data: Dict[str, str]) -> str:
        """체크리스트 기반 후속 질문 생성"""
        try:
            missing_fields = self.missing_fields(form_data)
            
            if not missing_fields:
                return "모든 정보가 수집되었습니다. 이미지 생성을 시작할까요?"
            
            # LLM을 사용하여 자연스러운 후속 질문 생성
            prompt = f"""
다음 대화에서 사용자에게 자연스럽게 다음 정보를 요청하는 질문을 생성해주세요.

사용자 질문: {user_query}
어시스턴트 답변: {last_response}

누락된 정보: {', '.join(missing_fields)}
다음 우선순위: {missing_fields[0] if missing_fields else '없음'}

자연스럽고 친근한 후속 질문을 생성해주세요(한문장):
"""
            follow_up = kanana_llm_model.generate_response(prompt, max_length=150, temperature=0.7)
            
            # LLM 응답이 부자연스러울 경우 폴백 질문 사용
            if not follow_up or len(follow_up) < 10:
                return self.next_question(missing_fields, form_data)
            
            return follow_up.strip()
            
        except Exception as e:
            print(f"체크리스트 기반 후속 질문 생성 실패: {e}")
            return self.next_question(missing_fields, form_data)

    def get_completion_status(self, form_data: Dict[str, any]) -> Dict[str, any]:
        """완성도 상태 반환"""
        missing_all = self.missing_fields(form_data)
        missing_required = self.missing_required_fields(form_data)
        missing_optional = self.missing_optional_fields(form_data)
        
        completed_all = len(self.all_fields) - len(missing_all)
        completed_required = len(self.required_fields) - len(missing_required)
        completed_optional = len(self.optional_fields) - len(missing_optional)
        
        total_all = len(self.all_fields)
        total_required = len(self.required_fields)
        total_optional = len(self.optional_fields)
        
        percentage_all = (completed_all / total_all) * 100 if total_all > 0 else 0
        percentage_required = (completed_required / total_required) * 100 if total_required > 0 else 0
        
        return {
            "completed_all": completed_all,
            "total_all": total_all,
            "percentage_all": percentage_all,
            "completed_required": completed_required,
            "total_required": total_required,
            "percentage_required": percentage_required,
            "completed_optional": completed_optional,
            "total_optional": total_optional,
            "missing_fields": missing_all,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "is_required_complete": len(missing_required) == 0,
            "is_complete": len(missing_all) == 0
        }
    
    def get_next_question(self, form_data: Dict[str, Any]) -> str:
        """
        다음에 물어볼 질문을 생성합니다.
        우선순위: 필수 필드 > 선택 필드
        """
        try:
            # 누락된 필드 확인
            missing_required = self.missing_required_fields(form_data)
            missing_optional = self.missing_optional_fields(form_data)
            
            # 필수 필드가 있으면 필수 필드부터
            if missing_required:
                next_field = missing_required[0]
                field_desc = self.field_descriptions.get(next_field, next_field)
                examples = self.field_examples.get(next_field, "")
                
                if examples:
                    return f"다음으로 {field_desc}에 대해 알려주세요.\n\n예시: {examples}\n\n어떤 {field_desc}를 원하시나요?"
                else:
                    return f"다음으로 {field_desc}에 대해 알려주세요.\n\n어떤 {field_desc}를 원하시나요?"
            
            # 필수 필드가 모두 채워졌으면 선택 필드
            elif missing_optional:
                next_field = missing_optional[0]
                field_desc = self.field_descriptions.get(next_field, next_field)
                examples = self.field_examples.get(next_field, "")
                
                if examples:
                    return f"추가로 {field_desc}에 대해 알려주세요. (선택사항)\n\n예시: {examples}\n\n어떤 {field_desc}를 원하시나요?"
                else:
                    return f"추가로 {field_desc}에 대해 알려주세요. (선택사항)\n\n어떤 {field_desc}를 원하시나요?"
            
            # 모든 필드가 채워졌으면
            else:
                return "모든 정보를 수집했습니다! 이제 이미지를 생성하겠습니다. 🎨"
                
        except Exception as e:
            print(f"다음 질문 생성 실패: {e}")
            return "다음 조건을 알려주세요."

checklist_generator = ChecklistGenerator()
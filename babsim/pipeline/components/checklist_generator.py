from __future__ import annotations
from typing import Dict, List, Optional, Any
import sys
import os
import json
import re
from pathlib import Path
# 파이프라인 루트 경로를 Python 경로에 추가
PIPELINE_ROOT = Path(__file__).parent.parent
sys.path.append(str(PIPELINE_ROOT))
from ..llm_provider import kanana_llm_model

# 필수 요소 (우선순위 높음)
REQUIRED_FIELDS = [
    "viewpoint", "body_type", "color_finish"
]

# 선택 요소 (우선순위 낮음)
OPTIONAL_FIELDS = [
    "body_classification", "proportions", "surfacing",
    "fascia", "lighting", "glasshouse",
    "aero", "wheel"
]

# 전체 필드
ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS

class ChecklistGenerator:
    def __init__(self):
        self.required_fields = REQUIRED_FIELDS
        self.optional_fields = OPTIONAL_FIELDS
        self.all_fields = ALL_FIELDS
        self.field_descriptions = {
    "viewpoint": "📐 차량을 바라보는 시점 (예: 정면(front view), 측면(side view), 후면(rear view), 또는 3/4 사선 뷰). "
                 "시점에 따라 차량의 전체 비율과 디자인 요소가 강조되는 방식이 달라집니다. "
                 "예: '3/4 front view'는 차량 앞부분과 측면을 동시에 보여주는 전형적인 카탈로그용 시점입니다.",

    "body_type": "🚗 차체 유형 (예: SUV, 세단, 쿠페, 해치백, 크로스오버, 픽업트럭 등). "
                 "차체 유형은 전체적인 실루엣과 비율을 결정하며, 차량의 용도와 성격(스포티, 패밀리, 럭셔리 등)에 큰 영향을 줍니다.",

    "body_classification": "🏗️ 차체 분류 (Body Classification) - 차량 크기 등급 (예: 소형(Compact), 준중형(Mid-size), 중형(Standard), 대형(Full-size), 럭셔리(Luxury)). "
                          "차량의 크기 등급은 전반적인 비율, 실내 공간, 휠 크기 등에 반영되며 시장 포지셔닝을 보여줍니다.",

    "proportions": "⚖️ 비율 & 자세 (Proportions & Stance) - 차체 비율 및 자세 (예: 긴 보닛(long hood), 짧은 오버행(short overhang), 넓은 차폭(wide stance), 낮은 차체(low profile)). "
                   "프로포션은 자동차의 첫인상을 좌우하며, 안정감·스포티함·고급스러움 등을 표현합니다.",

    "surfacing": "🎨 차체 표면 (Body Surfacing) - 차체 표면 처리 방식 (예: 유려한 곡선(curved surfaces), 날카로운 직선(sharp lines), 각진 구조(boxy shape)). "
                 "서페이스는 빛 반사와 그림자 형성을 통해 차량의 감각적 매력을 만들어냅니다.",

    "fascia": "🔧 전면부 & 측면부 요소 (Fascia & Profile) - 차량 전면부와 측면부의 주요 디자인 요소 (예: 라디에이터 그릴, 헤드라이트 형태, 범퍼 디자인, 도어 라인, 플러시 도어 핸들, 사이드 미러 형태, 휠 아치, 캐릭터 라인). "
              "전면 및 측면 요소는 브랜드 아이덴티티와 첫인상을 결정하는 가장 중요한 부분입니다.",

    "lighting": "💡 조명 (Lighting) - 조명 디자인 (예: LED 헤드램프, 매트릭스 헤드램프, 픽셀형 DRL, 테일램프, 턴시그널 패턴). "
                "조명은 야간 주행 안전성을 넘어, 차량만의 시그니처 아이덴티티를 표현하는 핵심 요소입니다.",

    "glasshouse": "🪟 글래스하우스 (Glasshouse) - 차량 유리창 비율과 형태 (예: 루프라인, 윈드실드 각도, 사이드 윈도우 크기, 파노라마 선루프). "
                  "글래스하우스는 실내 개방감과 외부에서 보이는 세련됨을 동시에 좌우합니다.",

    "aero": "🚀 공기역학 & 추가 요소 (Aero/Add-ons) - 공기역학적 요소 (예: 리어 스포일러, 디퓨저, 액티브 에어 플랩, 공기 커튼, 언더바디 패널). "
            "공기저항(Cd) 계수를 줄여 성능과 연비를 향상시키며, 스포티한 이미지를 강화합니다.",

    "color_finish": "🎨 차체 색상 및 마감 (예: 메탈릭 실버, 펄 화이트, 매트 블랙, 글로시 레드, 투톤 컬러). "
                    "페인트 마감은 차량의 개성을 표현하는 가장 직관적인 요소로, 고급감·스포티함·트렌디함을 결정합니다.",

    "wheel": "⚙️ 휠 디자인 (예: 스포크 휠, 터빈 휠, 에어로 커버 휠, 대구경 블랙 휠). "
             "휠 크기와 디자인은 차량의 스탠스와 퍼포먼스 이미지를 크게 좌우합니다."
}

        self.field_examples = {
            "viewpoint": "front 3/4 view, front view, side view, rear view",
            "body_type": "SUV, sedan, coupe, hatchback, crossover",
            "body_classification": "compact, mid-size, full-size, luxury",
            "proportions": "long hood, short overhang, wide stance",
            "surfacing": "curved surfaces, sharp lines, flowing design",
            "fascia": "large grille, LED headlights, sporty bumper, flush door handles, side skirts",
            "lighting": "LED DRL, matrix headlights, sequential turn signals",
            "glasshouse": "panoramic sunroof, black pillars, large windows",
            "aero": "active spoiler, air curtains, underbody panels",
            "color_finish": "metallic silver, pearl white, matte black",
            "wheel": "spoke wheels, turbine-style wheels, large black wheels"
        }

    def missing_fields(self, form_data: Dict[str, str]) -> List[str]:
        """누락된 필드 목록 반환 (필수 요소 우선, 빈 값 또는 '-' 제외)"""
        missing_required = [f for f in self.required_fields if not form_data.get(f) == "-" or not form_data.get(f)]
        missing_optional = [f for f in self.optional_fields if not form_data.get(f) == "-" or not form_data.get(f)]
        return missing_required + missing_optional
    
    def missing_required_fields(self, form_data: Dict[str, str]) -> List[str]:
        """누락된 필수 필드만 반환 (빈 값 또는 '-' 제외)"""
        return [f for f in self.required_fields if not form_data.get(f) == "-" or not form_data.get(f)]
    
    def missing_optional_fields(self, form_data: Dict[str, str]) -> List[str]:
        """누락된 선택 필드만 반환 (빈 값 또는 '-' 제외)"""
        return [f for f in self.optional_fields if not form_data.get(f) == "-" or not form_data.get(f)]

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
            return f"📋 현재 채워진 **필수 정보** {progress}\n\n'{description}'을 선택해주세요!\n\n💡 예시: {examples}\n\n이 정보는 이미지 생성에 꼭 필요합니다."
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
    
    def auto_fill_from_description(self, user_query: str, current_field: str = None) -> Dict[str, str]:
        """사용자 설명에서 자동으로 체크리스트 채우기 (Kanana LLM 기반)"""
        try:
            # Kanana LLM을 사용한 자동 채우기 시도
            llm_filled_data = self._auto_fill_with_kanana_llm(user_query, current_field)
            if llm_filled_data:
                print(f"Kanana LLM 자동 채우기 결과: {llm_filled_data}")
                return llm_filled_data
        except Exception as e:
            print(f"Kanana LLM 자동 채우기 실패: {e}")
        
        # LLM 실패 시 키워드 기반 폴백
        return self._auto_fill_with_keywords(user_query)
    
    def _auto_fill_with_kanana_llm(self, user_query: str, current_field: str = None) -> Dict[str, str]:
        """Kanana LLM을 사용한 정교한 자동 채우기 - 특정 필드만 추출"""
        
        # 필드별 프롬프트 생성
        if current_field == "body_type":
            prompt = f"""다음 사용자 설명에서 자동차 디자인 정보를 추출해주세요:

사용자 설명: "{user_query}"

다음 필드를 JSON 형태로 추출해주세요:
- body_type: 차체 타입 (SUV, sedan, coupe, hatchback, crossover 중 하나)

추출할 수 없는 정보는 빈 문자열("")로 표시하세요.
반드시 다음 JSON 형식으로만 답변하세요:
{{"body_type": ""}}"""

        elif current_field == "viewpoint":
            prompt = f"""다음 사용자 설명에서 자동차 디자인 정보를 추출해주세요:

사용자 설명: "{user_query}"

다음 필드를 JSON 형태로 추출해주세요:
- viewpoint: 시점 (front view, side view, rear view, 3/4 view 중 하나)

추출할 수 없는 정보는 빈 문자열("")로 표시하세요.
반드시 다음 JSON 형식으로만 답변하세요:
{{"viewpoint": ""}}"""

        elif current_field == "body_classification":
            prompt = f"""다음 사용자 설명에서 자동차 디자인 정보를 추출해주세요:

사용자 설명: "{user_query}"

다음 필드들을 JSON 형태로 추출해주세요:
- car_size: 크기 등급 (소형/준중형/중형/대형 등)
- car_boxes: 형태 (two-box/three-box 등)

추출할 수 없는 정보는 빈 문자열("")로 표시하세요.
반드시 다음 JSON 형식으로만 답변하세요:
{{"body_classification": {{"car_size": "", "car_boxes": ""}}}}"""

        elif current_field == "proportions":
            prompt = f"""다음 사용자 설명에서 자동차 디자인 정보를 추출해주세요:

사용자 설명: "{user_query}"

다음 필드들을 JSON 형태로 추출해주세요:
- wheelbase: 휠베이스 (short/long 등)
- track_width: 트랙 (narrow/wide 등)
- overhang: 오버행 (front short/rear long 등)
- stance: 자세 (upright/low/aggressive 등)
- dash_to_axle: 대시-투-액슬 (short/long 등)
- beltline: 벨트라인 (low/high 등)
- greenhouse_size: 그린하우스 (large/small 등)

추출할 수 없는 정보는 빈 문자열("")로 표시하세요.
반드시 다음 JSON 형식으로만 답변하세요:
{{"proportions": {{"wheelbase": "", "track_width": "", "overhang": "", "stance": "", "dash_to_axle": "", "beltline": "", "greenhouse_size": ""}}}}"""

        elif current_field == "surfacing":
            prompt = f"""다음 사용자 설명에서 자동차 디자인 정보를 추출해주세요:

사용자 설명: "{user_query}"

다음 필드를 JSON 형태로 추출해주세요:
- surfacing: 표면 처리 (Clean, Taut, Soft, Chamfers, Bulges, Strong shoulder line 중 하나)

추출할 수 없는 정보는 빈 문자열("")로 표시하세요.
반드시 다음 JSON 형식으로만 답변하세요:
{{"surfacing": ""}}"""

        elif current_field == "fascia":
            prompt = f"""다음 사용자 설명에서 자동차 디자인 정보를 추출해주세요:

사용자 설명: "{user_query}"

다음 필드들을 JSON 형태로 추출해주세요:
- grille_type: 그릴 (parametric/mesh/slats 등)
- air_intake: 흡기구 (large/small 등)
- bumper_style: 범퍼 (sporty/rugged 등)
- hood_style: 후드 (clamshell/sculpted 등)
- door_handles: 도어 핸들 (flush/pull type 등)

추출할 수 없는 정보는 빈 문자열("")로 표시하세요.
반드시 다음 JSON 형식으로만 답변하세요:
{{"fascia": {{"grille_type": "", "air_intake": "", "bumper_style": "", "hood_style": "", "door_handles": ""}}}}"""

        elif current_field == "lighting":
            prompt = f"""다음 사용자 설명에서 자동차 디자인 정보를 추출해주세요:

사용자 설명: "{user_query}"

다음 필드들을 JSON 형태로 추출해주세요:
- drl_type: DRL (pixel DRL/strip DRL 등)
- headlight_type: 헤드램프 (LED/matrix/projector 등)
- taillight_type: 테일램프 (full-width/vertical/horizontal 등)
- light_shape: 형상 (slim/parametric/pixelated 등)

추출할 수 없는 정보는 빈 문자열("")로 표시하세요.
반드시 다음 JSON 형식으로만 답변하세요:
{{"lighting": {{"drl_type": "", "headlight_type": "", "taillight_type": "", "light_shape": ""}}}}"""

        elif current_field == "glasshouse":
            prompt = f"""다음 사용자 설명에서 자동차 디자인 정보를 추출해주세요:

사용자 설명: "{user_query}"

다음 필드들을 JSON 형태로 추출해주세요:
- window_line: 윈도 라인
- window_trim: 윈도 트림 (chrome/black 등)
- side_mirror: 사이드 미러 (body-color/gloss black 등)
- pillar_treatment: 필러 처리

추출할 수 없는 정보는 빈 문자열("")로 표시하세요.
반드시 다음 JSON 형식으로만 답변하세요:
{{"glasshouse": {{"window_line": "", "window_trim": "", "side_mirror": "", "pillar_treatment": ""}}}}"""

        elif current_field == "aero":
            prompt = f"""다음 사용자 설명에서 자동차 디자인 정보를 추출해주세요:

사용자 설명: "{user_query}"

다음 필드를 JSON 형태로 추출해주세요:
- aero: 공기역학 & 추가 요소 (Splitter, Vents, Roof rails, Roof spoiler 중 하나)

추출할 수 없는 정보는 빈 문자열("")로 표시하세요.
반드시 다음 JSON 형식으로만 답변하세요:
{{"aero": ""}}"""

        elif current_field == "color_finish":
            prompt = f"""다음 사용자 설명에서 자동차 디자인 정보를 추출해주세요:

사용자 설명: "{user_query}"

다음 필드들을 JSON 형태로 추출해주세요:
- body_color: 차체 색상 (metallic teal, titanium gray 등)
- wheel_design: 휠 디자인 (multi-spoke, Y-spoke, turbine 등)
- roof_color: 루프 대비 색상 (black, silver 등)
- trim_accent: 트림 악센트 (chrome/gloss black/satin 등)

추출할 수 없는 정보는 빈 문자열("")로 표시하세요.
반드시 다음 JSON 형식으로만 답변하세요:
{{"color_finish": {{"body_color": "", "wheel_design": "", "roof_color": "", "trim_accent": ""}}}}"""

        else:
            # 기본값: 모든 필드 추출
            prompt = f"""다음 사용자 설명에서 자동차 디자인 정보를 추출해주세요:

사용자 설명: "{user_query}"

다음 필드들을 JSON 형태로 추출해주세요:
- viewpoint: 시점 (front view, side view, rear view, 3/4 view 중 하나)
- body_type: 차체 타입 (SUV, sedan, coupe, hatchback, crossover 중 하나)
- body_classification: 차체 분류 (compact, mid-size, full-size, luxury 중 하나)
- color_finish: 색상 (red, blue, black, white, silver, gold, metallic, pearl, matte 등)
- proportions: 비율 (long hood, short overhang, wide stance 등)
- surfacing: 표면 (curved surfaces, sharp lines, flowing design 등)
- fascia: 전면부 & 측면부 요소 (large grille, LED headlights, sporty bumper, flush door handles, side skirts 등)
- lighting: 조명 (LED DRL, matrix headlights, sequential turn signals 등)
- glasshouse: 유리창 (panoramic sunroof, black pillars, large windows 등)
- aero: 공기역학 (active spoiler, air curtains, underbody panels 등)
- wheel: 휠 (spoke wheels, turbine-style wheels, large black wheels 등)

추출할 수 없는 정보는 빈 문자열("")로 표시하세요.
반드시 다음 JSON 형식으로만 답변하세요:
{{"viewpoint": "", "body_type": "", "body_classification": "", "color_finish": "", "proportions": "", "surfacing": "", "fascia": "", "lighting": "", "glasshouse": "", "aero": "", "wheel": ""}}"""

        try:
            response = kanana_llm_model.generate_vllm_response_text(prompt, max_length=200, temperature=0.1)
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
            "body_classification": {
                "소형": "compact",
                "compact": "compact",
                "준중형": "mid-size",
                "mid-size": "mid-size",
                "중형": "full-size",
                "full-size": "full-size",
                "대형": "luxury",
                "luxury": "luxury"
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
            "body_classification": ["크기", "size", "소형", "중형", "대형", "compact", "mid-size", "분류", "classification"],
            "proportions": ["비율", "proportion", "전장", "전폭", "전고", "자세", "stance"],
            "surfacing": ["표면", "surface", "곡선", "직선", "curved", "sharp", "서페이싱"],
            "fascia": ["전면", "front", "그릴", "헤드라이트", "grille", "headlight", "측면", "side", "도어", "door", "프로파일", "profile"],
            "lighting": ["조명", "lighting", "라이트", "light", "led"],
            "glasshouse": ["유리", "glass", "윈도우", "window", "선루프", "sunroof", "글래스하우스"],
            "aero": ["공기역학", "aero", "스포일러", "spoiler", "디퓨저", "diffuser", "추가요소", "add-ons"],
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
            follow_up = kanana_llm_model.generate_vllm_response_streaming(prompt, max_length=150)
            
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
                return f"""이제부터 이미지 생성을 위해 체크리스트를 AI 어시스턴트와 함께 채워보겠습니다.\n\n 
                관련 정보에 대한 디자인 트랜드나 지식에 대해 알고 싶으시다면 무엇이든 질문해주세요!\n\n
                {next_field}에 대해 알려주세요.\n\n{field_desc}\n\n예시: {examples}"""
            # 필수 필드가 모두 채워졌으면 선택 필드
            elif missing_optional:
                next_field = missing_optional[0]
                field_desc = self.field_descriptions.get(next_field, next_field)
                examples = self.field_examples.get(next_field, "")
                return f"이제 필수 요소들은 모두 채워졌습니다.\n\n추가로 {next_field}에 대해 알려주세요.\n\n{field_desc}\n\n예시: {examples}"
               
            # 모든 필드가 채워졌으면
            else:
                return "모든 정보를 수집했습니다! 이제 이미지를 생성하겠습니다. 🎨"
                
        except Exception as e:
            print(f"다음 질문 생성 실패: {e}")
            return "다음 조건을 알려주세요."

checklist_generator = ChecklistGenerator()
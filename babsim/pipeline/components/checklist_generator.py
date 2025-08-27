from __future__ import annotations
from typing import Dict, List

REQUIRED_FIELDS = [
    "viewpoint", "body_type", "size_class", "proportions", "surface",
    "front_elements", "side_elements", "lighting", "glasshouse",
    "aero", "color_finish"
]

class ChecklistGenerator:
    def missing_fields(self, form_data: Dict[str, str]) -> List[str]:
        return [f for f in REQUIRED_FIELDS if not form_data.get(f)]

    def next_question(self, missing: List[str]) -> str:
        if not missing: return ""
        priority = ["viewpoint","body_type","color_finish"]
        missing.sort(key=lambda x: (x not in priority, priority.index(x) if x in priority else 99))
        target = missing[0]
        examples = {
            "viewpoint": "front 3/4, front view, side view",
            "body_type": "SUV, sedan, coupe, hatchback",
            "color_finish": "glossy black, matte silver, pearl white"
        }
        return f"이미지 생성을 위해 '{target}' 정보를 알려주세요. 예: {examples.get(target,'자유 입력')}"

checklist_generator = ChecklistGenerator()
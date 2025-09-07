"""
콘텐츠 생성 라우터 컴포넌트
의도에 따라 image/3D/4D 생성으로 분기
"""

from typing import Dict, Any
from .base_state import PipelineState


def route_content_generation(state: PipelineState) -> str:
    """
    의도에 따라 콘텐츠 생성 타입을 결정
    """
    intent = state.get("intent", "text_generation")
    
    if intent == "image_generation":
        return "image"
    elif intent == "3D_generation":
        return "3D"
    elif intent == "4D_generation":
        return "4D"
    else:
        return "text"


def content_generation_router(state: PipelineState) -> PipelineState:
    """
    콘텐츠 생성 라우터 (실제로는 라우팅만 수행)
    """
    # 이 노드는 실제 작업을 하지 않고 라우팅만 수행
    # 실제 생성은 각각의 generator 노드에서 수행
    return state

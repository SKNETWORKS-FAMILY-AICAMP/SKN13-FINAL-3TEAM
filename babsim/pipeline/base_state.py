"""
파이프라인 상태 정의
순환 import 문제를 해결하기 위해 별도 파일로 분리
"""

from typing import TypedDict, Dict, Any, List, Optional
from uuid import uuid4


class PipelineState(TypedDict, total=False):
    user_query: str
    initial_intent: str
    response: str
    chat_history: List[Dict[str, str]]
    messages_summarized: bool
    image_query: str
    is_form_complete: bool
    completion_status: Dict[str, Any]
    checklist_data: Dict[str, Any]
    pipeline_step: str
    current_field: Optional[str]
    waiting_node: Optional[str]
    modification_request: Optional[str]
    generated_image: Optional[str]
    image_generation_status: Optional[str]
    image_type: Optional[str]
    error: Optional[str]
    answer_type: Optional[str]
    s3_url: Optional[str]
    session_id: Optional[uuid4]
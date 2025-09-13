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
    image_mode: str
    is_form_complete: bool
    completion_status: Dict[str, Any]
    checklist_data: Dict[str, Any]
    pipeline_step: str
    current_field: Optional[str]    # 질문중인 필드, 11개
    current_field_conversation: Optional[str]
    waiting_node: Optional[str]
    modification_request: Optional[str]
    generated_image: Optional[str]
    image_generation_status: Optional[str]
    generation_type: Optional[str]  # 프롬프트 - 이미지, 3D, 4D 구분용 (기존 image_type)
    error: Optional[str]
    answer_type: Optional[str]
    s3_url: Optional[str]  # 이미지 URL만
    s3_url_3d: Optional[str]  # 3D 모델 URL
    s3_url_4d: Optional[str]  # 4D 모델 URL
    session_id: Optional[uuid4]
    user_id: Optional[str]  # 사용자 ID
    available_images: Optional[List[Dict[str, Any]]]  # 선택 가능한 이미지 목록
    selected_image_info: Optional[Dict[str, Any]]  # 선택된 이미지 정보
    # RAG 처리 관련 필드들
    rewritten: Optional[bool]
    eval: Optional[Dict[str, Any]]
    route: Optional[str]
    # 스트리밍 관련 필드
    is_streaming: Optional[bool]
    streaming_id: Optional[str]  # StreamingHttpResponse ID
    is_loading: Optional[bool]
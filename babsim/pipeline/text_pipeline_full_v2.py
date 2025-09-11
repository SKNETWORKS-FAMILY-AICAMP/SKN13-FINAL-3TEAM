from __future__ import annotations
from typing import TypedDict, Dict, Any, List, Optional
from uuid import uuid4


from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt

from .base_state import PipelineState
from .components.intent_classifier import IntentClassifier
from .components.chat_manager import chat_manager
from .components.checklist_generator import checklist_generator
from .components.image_query_generator import ImageQueryGenerator
from .components.image_modifier import generate_new_image, modify_image
from .components.babsim_rag_adapter import BabsimRAGAdapter
from .components.image_generator import ImageGenerator
from .components.image_modifier import ImageModifier
from .llm_provider import kanana_llm_model


_classifier = IntentClassifier()
_querygen = ImageQueryGenerator()
_rag = BabsimRAGAdapter()
_image_generator = ImageGenerator()
_image_modifier = ImageModifier()


# 상태 정의는 base_state.py에서 import

# -----------------------------
# Utils
# -----------------------------
def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()

def _append_history(state: PipelineState, role: str, content: str) -> None:
    chat_history = state.get("chat_history") or []
    updated = chat_manager.add_message(chat_history=chat_history, role=role, content=content)
    state["chat_history"] = updated



# -----------------------------
# 0) Welcome prompt (HITL if classifier unsure)
# -----------------------------
WELCOME_TEXT = (
    "안녕하세요! 🚗 현대자동차 Prototype Lab에 오신 것을 환영합니다!\n\n"
    "저는 AI 어시스턴트로, 세 가지 주요 기능을 제공합니다:\n\n"
    "🎨 새로운 자동차 이미지 생성\n"
    "- 체크리스트 기반 단계별 가이드로 상세한 디자인 생성\n"
    "- 자유롭게 바로 이미지 생성\n\n"
    "🖼️ 이미지 수정\n"
    "- 기존 자동차 이미지를 업로드하여 원하는 부분을 수정\n"
    "- 색상, 디자인 요소, 스타일 변경 등\n\n"
    "📚 현대자동차 & 디자인 지식 질문\n"
    "- 현대자동차의 디자인 철학, 기술, 역사 등에 대한 전문 지식 제공\n\n"
    "어떤 것을 도와드릴까요?\n"
    "1️⃣ 새로운 자동차 이미지를 생성하고 싶으시다면 \"이미지 생성\"\n"
    "2️⃣ 기존 이미지를 수정하고 싶으시다면 \"이미지 수정\"\n"
    "3️⃣ 현대자동차나 디자인에 대해 질문이 있다면 \"질문\" 이라고 말씀해주세요."
)

def welcome_pick(state: PipelineState) -> PipelineState:
    """사용자에게 기능 선택을 요청"""
    # 사용자 입력이 있으면 state에 저장
    user_query = state.get("user_query", "")
    if user_query:
        print(f"[DEBUG] welcome_pick - 사용자 입력 받음: '{user_query}'")
        return {"user_query": user_query, "response": WELCOME_TEXT}
    
    # 사용자 입력이 없으면 interrupt로 요청
    user_query = interrupt({"query": WELCOME_TEXT})
    return {**user_query, "response": WELCOME_TEXT, "waiting_node": "welcome_pick"}

def process_welcome_input(state: PipelineState) -> PipelineState:
    """사용자의 welcome 입력을 처리하여 user_query에 저장"""
    # interrupt로 받은 사용자 입력을 user_query에 저장
    user_query = state.get("user_query", "")
    print(f"[DEBUG] process_welcome_input - user_query: '{user_query}'")
    if user_query:
        # user_query가 이미 있으면 그대로 전달
        return {"user_query": user_query}
    return {}

# 사용자한테 첫번째 의도 받고 분류
# -----------------------------
# 1) Initial intent classification + apply user pick
# -----------------------------
def classify_and_apply_intent(state: PipelineState) -> Dict[str, Any]:
    user_query = state.get("user_query", "")
    print(f"[DEBUG] classify_and_apply_intent - user_query: '{user_query}'")
    final_intent = _classifier.classify_initial_intent(user_query)
    print(f"[DEBUG] classify_and_apply_intent - final_intent: '{final_intent}'")
    return {"initial_intent": final_intent}


def route_top(state: PipelineState) -> str:
    it = _norm(state.get("initial_intent"))
    if it == "image_generation":
        return "image_generation"
    if it == "image_modification":
        return "image_modification"
    if it == "rag":
        return "rag"
    return "general_conversation"


# -----------------------------
# 2) General conversation
# -----------------------------
def handle_general_conversation(state: PipelineState) -> Dict[str, Any]:
    user_query = state.get("user_query", "")
    _append_history(state, "user", user_query)
    resp = chat_manager.generate_general_response(user_query=user_query, chat_history=state.get("chat_history"))
    _append_history(state, "assistant", resp)
    return {"response": resp}


# -----------------------------
# 3) RAG branch
# -----------------------------
def handle_rag(state: PipelineState) -> Dict[str, Any]:
    user_query = state.get("user_query", "")
    _append_history(state, "user", user_query)

    # Retrieve docs
    try:
        docs = _rag.search_relevant_documents(query=user_query, k=5) or []
    except Exception as e:
        docs = []
        print(f"[handle_rag] search failed: {e}")

    context_snippets = []
    for d in docs:
        # assume each doc has 'payload' or 'text' fields; keep robust
        txt = d.get("payload", {}).get("text") if isinstance(d, dict) else None
        if not txt:
            txt = str(d)
        context_snippets.append(txt)

    # Synthesize answer via LLM including context
    context_prefix = "다음은 관련 참고 컨텍스트입니다:\n" + "\n---\n".join(context_snippets[:3]) if context_snippets else ""
    merged_query = (context_prefix + "\n\n질문: " + user_query).strip()
    resp = chat_manager.generate_general_response(user_query=merged_query, chat_history=state.get("chat_history"))
    _append_history(state, "assistant", resp)
    return {"response": resp}


# -----------------------------
# 4) Image generation branch (guided/direct)
# -----------------------------

def image_mode(state: PipelineState) -> PipelineState:
    """이미지 생성 방식을 선택하도록 요청"""
    msg = (
        """이미지 생성을 시작하겠습니다! 🎨

어떤 방식으로 진행하시겠습니까?

1️⃣ **체크리스트 기반 단계별 가이드**
   - 11가지 카테고리를 차근차근 채워가며 상세한 디자인 생성

2️⃣ **직접 이미지 생성**
   - 원하는 디자인을 자유롭게 설명하면 바로 이미지 생성

- 체크리스트 기반: "체크리스트" 또는 "단계별"
- 바로 생성: "바로" 또는 "직접" """
    )
    user_query = interrupt({"query": msg})
    return {**user_query, "response": msg, "waiting_node": "image_mode"}

def apply_image_mode(state: PipelineState) -> Dict[str, Any]:
    # user_query에서 받은 사용자 입력을 LLM으로 분류
    user_input = state.get("user_query", "")
    mode = _classifier.classify_image_generation_intent(user_input)
    
    # 분류 결과를 상태에 저장
    state["image_mode"] = mode
    _append_history(state, "user", user_input)
    
    print(f"[apply_image_mode] 사용자 입력: '{user_input}' -> 분류 결과: '{mode}'")
    return {"image_mode": mode}

def route_image_mode(state: PipelineState) -> str:
    mode = state.get("image_mode", "guided")
    return mode


# Guided loop
def guided_prepare_question(state: PipelineState) -> Dict[str, Any]:
    """체크리스트 초기화 및 준비"""
    form_data = dict(state.get("checklist_data") or {})
    
    # 체크리스트 데이터가 없으면 초기화
    if not form_data:
        # 모든 필드를 빈 문자열로 초기화
        form_data = {field: "" for field in checklist_generator.all_fields}
        print(f"[DEBUG] 체크리스트 초기화: {form_data}")
    
    # 자동 채우기 시도 (사용자 쿼리가 있는 경우)
    user_query = state.get("user_query", "")
    if user_query and user_query not in ["guided", "direct"]:
        autofill = checklist_generator.auto_fill_from_description(user_query) or {}
        if autofill:
            form_data.update(autofill)
            print(f"[DEBUG] 자동 채우기 결과: {autofill}")

    missing_req = checklist_generator.missing_required_fields(form_data)
    missing_opt = checklist_generator.missing_optional_fields(form_data)
    
    print(f"[DEBUG] 누락된 필수 필드: {missing_req}")
    print(f"[DEBUG] 누락된 선택 필드: {missing_opt}")

    if not missing_req and not missing_opt:
        state["is_form_complete"] = True
        state["completion_status"] = checklist_generator.get_completion_status(form_data)
        return {"checklist_data": form_data, "pipeline_step": "guided_done"}

    # 첫 번째 누락된 필드를 current_field로 설정
    missing = missing_req if missing_req else missing_opt
    current_field = missing[0]
    
    print(f"[DEBUG] guided_prepare_question - current_field 설정: {current_field}")
    
    # 체크리스트 데이터와 current_field를 상태에 저장
    state["current_field"] = current_field
    state["waiting_node"] = "guided_next_category"
    return {"checklist_data": form_data, "current_field": current_field}


def guided_llm_chat(state: PipelineState) -> PipelineState:
    """LLM과의 자유로운 대화 처리"""
    user_input = (state.get("user_query") or "").strip()
    current_field = state.get("current_field", "")
    
    print(f"[DEBUG] guided_llm_chat - current_field: '{current_field}', user_input: '{user_input}'")
    print(f"[DEBUG] guided_llm_chat - 전체 state keys: {list(state.keys())}")
    print(f"[DEBUG] guided_llm_chat - 전체 state: {state}")
    
    # "질문 완료" 확인 -> 다음 카테고리의 llm 대화로 이동
    if user_input.lower() in ["질문 완료", "완료", "다음", "next"]:
        # LLM 대화 종료, 체크리스트 답변 요청으로 이동
        _append_history(state, "user", user_input)
        print(f"[DEBUG] guided_llm_chat - 질문 완료, guided_ask_answer로 이동")
        return {"pipeline_step": "guided_ask_answer", "current_field": current_field}
        
    if user_input.lower() in ["건너뛰기", "skip", "다음", "next"]:
        print(f"[DEBUG] guided_llm_chat - 건너뛰기 입력: '{user_input}'")
        return {"response": "선택 체크리스트를 건너뛰고 이미지 생성을 진행합니다.🎨", "pipeline_step": "build_query_from_history", "waiting_node": "guided_ask_answer"}
    else:
        # 사용자가 LLM에게 질문한 경우
        # Kanana LLM에게 질문
        kanana_response = kanana_llm_model.generate_response(
            user_input, 
            temperature=0.7, 
            max_length=300
        )
        
        # 대화 기록
        _append_history(state, "user", user_input)
        _append_history(state, "assistant", kanana_response)
        
        # 사용자에게 LLM 답변 표시하고 계속 대화 가능
        continue_message = f"{kanana_response}\n\n계속 질문하시거나 '질문 완료'를 입력해주세요."
        
        user_query=interrupt({"query": continue_message})
        return {**user_query, "response": continue_message, "pipeline_step": "guided_llm_chat", "waiting_node": "guided_llm_chat"}

def guided_record(state: PipelineState) -> Dict[str, Any]:
    """체크리스트 답변 저장 후 다음 카테고리로 이동"""
    field = state.get("current_field")
    user_input = (state.get("user_query") or "").strip()
    form = dict(state.get("checklist_data") or {})
    pipeline_step = state.get("pipeline_step", "")
    
    print(f"[DEBUG] guided_record - field: {field}, user_input: '{user_input}', pipeline_step: '{pipeline_step}'")
    
    if pipeline_step == "guided_ask_answer":
        # 체크리스트 답변을 받는 단계
        if field:
            # 체크리스트 답변 저장
            form[field] = user_input
            _append_history(state, "user", f"{field}: {user_input}")
            
            print(f"[DEBUG] 체크리스트 답변 저장: {field} = {user_input}")
            
            # 체크리스트 완성도 업데이트
            completion_status = checklist_generator.get_completion_status(form)
            print(f"[DEBUG] 체크리스트 완성도 업데이트: {completion_status}")
            
            return {
                "checklist_data": form, 
                "pipeline_step": "guided_next_category",
                "completion_status": completion_status
            }
        else:
            # LLM 대화 단계 (guided_llm_chat에서 처리됨)
            return {"checklist_data": form, "pipeline_step": "guided_recorded"}
    else:
        # 다른 pipeline_step인 경우 - 답변 저장하지 않음
        print(f"[DEBUG] pipeline_step이 'guided_ask_answer'가 아님: '{pipeline_step}'")
    return {"checklist_data": form, "pipeline_step": "guided_recorded"}

def guided_ask_answer(state: PipelineState) -> PipelineState:
    """체크리스트 답변 요청"""
    current_field = state.get("current_field", "")
    user_input = (state.get("user_query") or "").strip()
    form_data = dict(state.get("checklist_data") or {})
    
    print(f"[DEBUG] guided_ask_answer - current_field: {current_field}, user_input: '{user_input}'")
    
    # "건너뛰기" 확인
    if user_input.lower() in ["건너뛰기", "skip", "다음", "next"]:
        print(f"[DEBUG] guided_ask_answer - 건너뛰기 입력: '{user_input}'")
        return {"response": "선택 체크리스트를 건너뛰고 이미지 생성을 진행합니다.🎨", "pipeline_step": "build_query_from_history", "waiting_node": "guided_ask_answer"}
    
    if current_field:
        # 체크리스트 질문 생성
        missing_req = checklist_generator.missing_required_fields(form_data)
        missing_opt = checklist_generator.missing_optional_fields(form_data)
        missing = missing_req if missing_req else missing_opt
        
        if missing and missing[0] == current_field:
            question = checklist_generator.next_question(missing, form_data)
            
            # LLM 대화를 바탕으로 한 답변 요청
            answer_request = f"위의 대화를 바탕으로 {current_field}에 대한 답변을 입력해주세요:\n{question}"
            
            user_query = interrupt({"query": answer_request})
            return {**user_query, "response": answer_request, "pipeline_step": "guided_ask_answer", "current_field": current_field, "waiting_node": "guided_ask_answer"}
    
    return {"response": "다음 단계로 진행합니다."}

def guided_next_category(state: PipelineState) -> PipelineState:
    """다음 체크리스트 카테고리로 이동"""
    form_data = dict(state.get("checklist_data") or {})
    user_input = (state.get("user_query") or "").strip()
    
    # "건너뛰기" 확인
    if user_input.lower() in ["건너뛰기", "skip", "다음", "next"]:
        print(f"[DEBUG] guided_next_category - 건너뛰기 입력: '{user_input}'")
        return {"response": "체크리스트를 건너뛰고 이미지 생성을 진행합니다. 🎨", "pipeline_step": "build_query_from_history", "waiting_node": "guided_next_category"}
    
    # 필수 필드부터 확인
    missing_req = checklist_generator.missing_required_fields(form_data)
    
    if missing_req:
        # 아직 필수 필드가 남아있음
        current_field = missing_req[0]
        
        # 체크리스트 시작 안내 (첫 번째 질문인 경우)
        if len(form_data) == 0 or all(v == "" for v in form_data.values()):
            intro_message = f"이제 체크리스트를 하나씩 채워보겠습니다!\n\n첫 번째 카테고리: {current_field}\n\n{current_field}에 대해 자유롭게 질문하세요!\n현대자동차 디자인 전문가 AI가 답변해드립니다.\n\n질문이 끝나시면 '질문 완료'라고 입력해주세요."
        else:
            intro_message = f"다음 카테고리: {current_field}\n\n{current_field}에 대해 자유롭게 질문하세요!\n현대자동차 디자인 전문가 AI가 답변해드립니다.\n\n질문이 끝나시면 '질문 완료'라고 입력해주세요."
        
        print(f"[DEBUG] guided_next_category - current_field 설정: {current_field}")
        
        # 체크리스트 완성도 업데이트
        completion_status = checklist_generator.get_completion_status(form_data)
        print(f"[DEBUG] 체크리스트 완성도 업데이트: {completion_status}")
        
        # interrupt로 사용자 입력을 받음
        user_query = interrupt({"query": intro_message})
        return {
            **user_query,
            "response": intro_message, 
            "pipeline_step": "guided_llm_chat", 
            "current_field": current_field,
            "completion_status": completion_status,
            "waiting_node": "guided_next_category"
        }
    
    else:
        # 필수 필드가 모두 채워짐 - 선택 필드 확인
        missing_opt = checklist_generator.missing_optional_fields(form_data)
        
        if missing_opt:
            # 선택 필드가 남아있음 - 사용자에게 선택권 제공
            current_field = missing_opt[0]
            
            optional_message = f"필수 질문이 모두 완료되었습니다! 🎉\n\n선택 질문도 채우시겠습니까?\n\n필수 정보로 충분하다면, '건너뛰기'를 입력해주세요.\n\n다음 선택 카테고리: {current_field}\n\n{current_field}에 대해 자유롭게 질문하세요!\n현대자동차 디자인 전문가 AI가 답변해드립니다.\n\n질문이 끝나시면 '질문 완료'라고 입력해주세요."
            
            print(f"[DEBUG] guided_next_category - 선택 필드 current_field 설정: {current_field}")
            
            # interrupt로 사용자 입력을 받음
            user_query = interrupt({"query": optional_message})
            return {
                **user_query,
                "response": optional_message, 
                "pipeline_step": "guided_llm_chat", 
                "current_field": current_field,
                "waiting_node": "guided_next_category"
            }
        else:
            # 모든 질문 완료
            print(f"[DEBUG] guided_next_category - 모든 질문 완료")
            return {"response": "체크리스트가 모두 완료되었습니다! 🎉 이제 이미지 생성을 시작하겠습니다.", "pipeline_step": "build_query_from_history", "waiting_node": "guided_next_category"}

def guided_continue_or_done(state: PipelineState) -> str:
    form = state.get("checklist_data") or {}
    done = checklist_generator.get_completion_status(form).get("is_complete", False) \
           or (checklist_generator.missing_required_fields(form) == [] and checklist_generator.missing_optional_fields(form) == [])
    return "done" if done else "continue"

def build_query_from_history(state: PipelineState) -> Dict[str, Any]:
    # 이미지 쿼리 생성
    image_query = _querygen.generate_image_query(state)
    
    print(f"🔍 [분기] generate_image_query 결과: {image_query[:100]}...")
    return {**state, "image_query": image_query}

# Direct
def direct_prompt(state: PipelineState) -> Dict[str, Any]:
    p = (
        "원하는 자동차 디자인을 자유롭게 상세히 적어주세요.\n"
        "예) '중형 SUV, 3/4 front, 긴 휠베이스, 짧은 오버행, 깨끗한 바디, parametric grille, pixel DRL, 대형 알로이 휠, 파노라믹 글라스 루프, 매트 실버'"
    )
    state["response"] = p
    _append_history(state, "assistant", p)
    return {}

def direct_freeform(state: PipelineState) -> PipelineState:
    """자유형식 입력을 요청"""
    question = state.get("response") or "자유기술을 입력하세요."
    user_query=interrupt({"query": question})
    return {**user_query, "response": question, "waiting_node": "direct_freeform"}

def direct_record_and_build_query(state: PipelineState) -> Dict[str, Any]:
    # user_query에서 받은 사용자 입력을 사용
    desc = (state.get("user_query") or "").strip()
    if desc:
        _append_history(state, "user", desc)
    query = _querygen.generate_image_query(chat_history=state.get("chat_history") or [])
    state["image_query"] = query
    return {}


# Generate
def run_image_generation(state: PipelineState) -> Dict[str, Any]:
    """
    ImageGenerator 인스턴스를 사용하여 이미지 생성
    """
    print("🔍 [분기] generate_image 실행")
    
    # 이미지 생성
    response, s3_url = _image_generator.generate_image(state)
    
    # 멀티턴을 위해 대화 기록 업데이트
    updated = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
    updated = chat_manager.add_message(updated, "assistant", response)
    
    print(f"🔍 [분기] generate_image 결과: {response[:100]}")
    return {**state, "chat_history": updated, "response": response, "s3_url": s3_url}

def ask_modify(state: PipelineState) -> PipelineState:
    """이미지 수정 여부를 GPT-4o로 판단"""
    user_input = (state.get("user_query") or "").strip()
    
    # 사용자 입력이 있으면 GPT-4o로 판단
    if user_input:
        modify_intent = _classifier.classify_modification_intent(user_input)
        print(f"[DEBUG] ask_modify - 수정 의도 판단: '{modify_intent}'")
        
        if modify_intent == "modify":
            # 수정을 원함 - 수정 사항을 state에 저장
            return {
                "response": "이미지 수정을 진행하겠습니다.", 
                "pipeline_step": "modify_image",
                "modification_request": user_input  # 수정 사항 저장
            }
        else:
            # 수정을 원하지 않음
            return {"response": "3D 및 4D 시뮬레이션을 진행하겠습니다.", "pipeline_step": "3d_generation"}
    
    # 사용자 입력이 없으면 질문
    question = "이미지를 수정하시겠습니까? 수정 사항을 말씀해주시거나, '아니오'라고 답해주세요."
    user_query = interrupt({"query": question})
    return {**user_query, "response": question, "waiting_node": "ask_modify"}
# 이미지 수정
def modify_image(state: PipelineState) -> PipelineState:
    """
    ImageModifier 인스턴스를 사용하여 이미지 수정
    """
    print("🔍 [분기] modify_image 실행")
    
    # 수정 사항을 state에 추가
    modification_request = state.get("modification_request", "")
    print(f"🔍 [분기] 수정 사항: {modification_request}")
    
    # 이미지 수정을 위한 state 준비
    modify_state = {**state, "user_query": modification_request}
    
    # 이미지 수정
    response, s3_url = _image_modifier.modify_image(modify_state)
    
    # 멀티턴을 위해 대화 기록 업데이트
    updated = chat_manager.add_message(state.get("chat_history", []), "user", modification_request)
    updated = chat_manager.add_message(updated, "assistant", response)
    
    print(f"🔍 [분기] modify_image 결과: {response[:100]}")
    return {**state, "chat_history": updated, "response": response, "s3_url": s3_url}

def run_3d_generation(state: PipelineState) -> PipelineState:
    """3D 모델 생성"""
    print("🔍 [분기] 3D 생성 실행")
    
    # 3D 생성 로직 (실제 구현 필요)
    response = "3D 모델 생성이 완료되었습니다! 🎯"
    
    # 멀티턴을 위해 대화 기록 업데이트
    updated = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
    updated = chat_manager.add_message(updated, "assistant", response)
    
    return {**state, "chat_history": updated, "response": response}

def run_4d_generation(state: PipelineState) -> PipelineState:
    """4D 모델 생성"""
    print("🔍 [분기] 4D 생성 실행")
    
    # 4D 생성 로직 (실제 구현 필요)
    response = "4D 모델 생성이 완료되었습니다! 🚀"
    
    # 멀티턴을 위해 대화 기록 업데이트
    updated = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
    updated = chat_manager.add_message(updated, "assistant", response)
    
    return {**state, "chat_history": updated, "response": response}

# -----------------------------
# 5) Image modification branch
# -----------------------------
def mod_intro(state: PipelineState) -> Dict[str, Any]:
    text = (
        "이미지 수정 모드입니다.\n"
        "1) 수정할 자동차 이미지의 URL을 붙여넣어 주세요 (또는 업로드 후 접근 가능한 링크를 제공해 주세요).\n"
        "2) 어떤 부분을 어떻게 수정할지 간단히 설명해 주세요 (예: 색상 변경, DRL 스타일 변경, 휠 디자인 교체 등)."
    )
    state["response"] = text
    _append_history(state, "assistant", text)
    return {}

def mod_image_url(state: PipelineState) -> PipelineState:
    """수정할 이미지 URL을 요청"""
    question = state.get("response") or "수정할 이미지 URL을 입력하세요."
    user_query=interrupt({"query": question})
    return {**user_query, "response": question, "waiting_node": "mod_image_url"}

def store_mod_image(state: PipelineState) -> Dict[str, Any]:
    # user_query에서 받은 사용자 입력을 사용
    url = (state.get("user_query") or "").strip()
    if url:
        # image_modifier.modify_image expects 'input_image' in state (commonly)
        state["input_image"] = url
        _append_history(state, "user", f"[이미지 URL] {url}")
    return {}

def mod_instruction(state: PipelineState) -> PipelineState:
    """수정 지시사항을 요청"""
    question = "어떤 부분을 어떻게 수정할까요? 예: '픽셀 DRL로 변경하고, 바디 컬러는 매트 실버'"
    user_query=interrupt({"query": question})
    return {**user_query, "response": question, "waiting_node": "mod_instruction"}

def store_mod_instruction(state: PipelineState) -> Dict[str, Any]:
    # user_query에서 받은 사용자 입력을 사용
    desc = (state.get("user_query") or "").strip()
    if desc:
        _append_history(state, "user", desc)
        # Use same generator to build an edit-friendly prompt from the conversation
        image_query = _querygen.generate_image_query(state)
    
    print(f"🔍 [분기] generate_image_query 결과: {image_query[:100]}...")
    return {**state, "image_query": image_query}

def run_image_modification(state: PipelineState) -> Dict[str, Any]:
    if not state.get("input_image"):
        return {"error": "input_image가 비어 있습니다."}
    if not state.get("image_query"):
        return {"error": "image_query가 비어 있습니다."}
    out = modify_image(dict(state))
    for k in ["s3_url", "generated_image", "image_generation_status", "image_type", "response", "error"]:
        if k in out: state[k] = out[k]
    if not state.get("response"):
        msg = state.get("s3_url") or state.get("generated_image") or "이미지 수정 완료"
        state["response"] = f"이미지 수정이 완료되었습니다! 🛠️\n\n결과: {msg}"
    return {}


# -----------------------------
# Finalize
# -----------------------------
def finalize(state: PipelineState) -> Dict[str, Any]:
    return {"response": state.get("response") or state.get("image_query") or "완료되었습니다."}


# -----------------------------
# Graph assembly
# -----------------------------
def create_text_pipeline():
    g = StateGraph(PipelineState)

    # Welcome -> pick
    g.add_node("welcome_pick", welcome_pick)                     # HITL A
    g.add_node("process_welcome_input", process_welcome_input)
    g.add_node("classify_and_apply_intent", classify_and_apply_intent)

    # Routing branches
    g.add_node("handle_general_conversation", handle_general_conversation)
    g.add_node("handle_rag", handle_rag)

    # Image generation
    g.add_node("image_mode", image_mode)                         # HITL B
    g.add_node("apply_image_mode", apply_image_mode)
    g.add_node("guided_prepare_question", guided_prepare_question)
    g.add_node("guided_llm_chat", guided_llm_chat)               # HITL C.1 (LLM 대화)
    g.add_node("guided_record", guided_record)
    g.add_node("guided_ask_answer", guided_ask_answer)            # HITL C.5 (ask for actual answer)
    g.add_node("guided_next_category", guided_next_category)     # 다음 카테고리로 이동
    g.add_node("build_query_from_history", build_query_from_history)
    g.add_node("direct_prompt", direct_prompt)
    g.add_node("direct_freeform", direct_freeform)               # HITL D
    g.add_node("direct_record_and_build_query", direct_record_and_build_query)
    g.add_node("run_image_generation", run_image_generation)
    g.add_node("ask_modify", ask_modify)
    g.add_node("modify_image", modify_image)
    g.add_node("run_3d_generation", run_3d_generation)
    g.add_node("run_4d_generation", run_4d_generation)

    # Image modification
    g.add_node("mod_intro", mod_intro)
    g.add_node("mod_image_url", mod_image_url)                   # HITL E
    g.add_node("store_mod_image", store_mod_image)
    g.add_node("mod_instruction", mod_instruction)               # HITL F
    g.add_node("store_mod_instruction", store_mod_instruction)
    g.add_node("run_image_modification", run_image_modification)

    # Final
    g.add_node("finalize", finalize)

    # Edges
    g.set_entry_point("welcome_pick")
    g.add_edge("welcome_pick", "process_welcome_input")
    g.add_edge("process_welcome_input", "classify_and_apply_intent")

    g.add_conditional_edges(
        "classify_and_apply_intent",
        route_top,
        {
            "image_generation": "image_mode",
            "image_modification": "mod_intro",
            "rag": "handle_rag",
            "general_conversation": "handle_general_conversation",
        },
    )

    # General / RAG end
    g.add_edge("handle_general_conversation", "finalize")
    g.add_edge("handle_rag", "finalize")

    # Image generation path
    g.add_edge("image_mode", "apply_image_mode")
    g.add_conditional_edges(
        "apply_image_mode",
        route_image_mode,
        {
            "guided": "guided_prepare_question",
            "direct": "direct_prompt",
        },
    )
    g.add_edge("guided_prepare_question", "guided_next_category")  # 바로 다음 카테고리로 이동
    g.add_conditional_edges(
        "guided_llm_chat",
        lambda s: "ask_answer" if s.get("pipeline_step") == "guided_ask_answer" else ("build_query" if s.get("pipeline_step") == "build_query_from_history" else "llm_chat"),
        {
            "llm_chat": "guided_llm_chat",  # 계속 LLM 대화
            "ask_answer": "guided_ask_answer",  # 체크리스트 답변 요청
            "build_query": "build_query_from_history",  # 쿼리 생성으로 이동
        },
    )
    g.add_conditional_edges(
        "guided_record",
        lambda s: "next_category" if s.get("pipeline_step") == "guided_next_category" else ("done" if guided_continue_or_done(s) == "done" else "continue"),
        {
            "next_category": "guided_next_category",  # 바로 다음 카테고리로 이동
            "continue": "guided_next_category",  # 다음 카테고리로 이동
            "done": "build_query_from_history",
        },
    )
    g.add_conditional_edges(
        "guided_ask_answer",
        lambda s: "record" if s.get("user_query") and s.get("user_query").strip() else "ask",
        {
            "ask": "guided_ask_answer",  # 계속 답변 요청
            "record": "guided_record",   # 답변 저장 후 기록
        },
    )
    g.add_conditional_edges(
        "guided_next_category",
        lambda s: "build_query" if s.get("pipeline_step") == "build_query_from_history" else "llm_chat",
        {
            "llm_chat": "guided_llm_chat",  # LLM 대화 시작
            "build_query": "build_query_from_history",  # 쿼리 생성으로 이동
        },
    )
    g.add_edge("direct_prompt", "direct_freeform")
    g.add_edge("direct_freeform", "direct_record_and_build_query")
    g.add_edge("build_query_from_history", "run_image_generation")
    g.add_edge("direct_record_and_build_query", "run_image_generation")
    g.add_edge("run_image_generation", "ask_modify")
    
    # ask_modify에서 라우팅
    g.add_conditional_edges(
        "ask_modify",
        lambda s: "modify" if s.get("pipeline_step") == "modify_image" else "3d_generation",
        {
            "modify": "modify_image",
            "3d_generation": "run_3d_generation",
        },
    )
    
    # modify_image 후 3D/4D 생성으로 이동
    g.add_edge("modify_image", "run_3d_generation")
    g.add_edge("run_3d_generation", "run_4d_generation")
    g.add_edge("run_4d_generation", "finalize")

    # Image modification path
    g.add_edge("mod_intro", "mod_image_url")
    g.add_edge("mod_image_url", "store_mod_image")
    g.add_edge("store_mod_image", "mod_instruction")
    g.add_edge("mod_instruction", "store_mod_instruction")
    g.add_edge("store_mod_instruction", "run_image_modification")
    g.add_edge("run_image_modification", "finalize")

    g.add_edge("finalize", END)
    
    # checkpointer를 사용하여 상태 보존
    checkpointer = InMemorySaver()
    return g.compile(checkpointer=checkpointer)

# 파이프라인 그래프 생성 및 export
all_pipeline = create_text_pipeline()

# if __name__ == "__main__":
#     app = create_text_pipeline()
#     config = {"configurable": {"thread_id": "test_thread"}}
    
#     print("=== 전체 체크리스트 플로우 테스트 (11개 카테고리) ===")
    
#     try:
#         # 체크리스트 필드 정의 (필수 + 선택)
#         checklist_fields = [
#             "viewpoint", "body_type", "size_class", "color_finish", "proportions",
#             "surface", "front_elements", "side_elements", "lighting", "glasshouse", "aero"
#         ]
        
#         # 체크리스트 답변 정의
#         checklist_answers = {
#             "viewpoint": "전면 뷰",
#             "body_type": "세단",
#             "size_class": "중형차",
#             "color_finish": "메탈릭 실버",
#             "proportions": "균형잡힌 비율",
#             "surface": "매끄러운 표면",
#             "front_elements": "현대적 그릴",
#             "side_elements": "우아한 라인",
#             "lighting": "LED 헤드라이트",
#             "glasshouse": "큰 사이드 윈도우",
#             "aero": "공기역학적 디자인"
#         }
        
#         step = 0
        
#         # 첫 번째 실행 (welcome까지)
#         result = app.invoke({"user_query": "이미지를 생성해줘"}, config=config)
#         step += 1
#         print(f"Step {step}: {result.get('response')}")
        
#         # interrupt 확인
#         if '__interrupt__' in result:
#             print(f"Interrupt 발생: {result['__interrupt__'][-1].value['query']}")
            
#             # 두 번째 실행 (기능 선택)
#             human_command = Command(resume={"user_query": "이미지 생성"})
#             result = app.invoke(human_command, config=config)
#             step += 1
#             print(f"Step {step}: {result.get('response')}")
            
#             # interrupt 확인
#             if '__interrupt__' in result:
#                 print(f"Interrupt 발생: {result['__interrupt__'][-1].value['query']}")
                
#                 # 세 번째 실행 (이미지 생성 방식 선택)
#                 human_command = Command(resume={"user_query": "guided"})
#                 result = app.invoke(human_command, config=config)
#                 step += 1
#                 print(f"Step {step}: {result.get('response')}")
                
#                 # interrupt 확인 (첫 번째 카테고리 안내)
#                 if '__interrupt__' in result:
#                     print(f"Interrupt 발생: {result['__interrupt__'][-1].value['query']}")
                    
#                     # 첫 번째 카테고리만 테스트 (viewpoint)
#                     field = "viewpoint"
#                     print(f"\n--- {field.upper()} 카테고리 테스트 ---")
                    
#                     # LLM과 대화 시작 - 테스트용 자동 입력
#                     llm_input = f"{field}에 대해 설명해줘"
#                     print(f"\n[{field} 카테고리] LLM 입력: {llm_input}")
#                     human_command = Command(resume={"user_query": llm_input})
#                     result = app.invoke(human_command, config=config)
#                     step += 1
#                     print(f"Step {step} ({field} LLM 대화): {result.get('response')}")
                    
#                     # interrupt 확인 (LLM 답변 후 계속 대화)
#                     if '__interrupt__' in result:
#                         print(f"Interrupt 발생: {result['__interrupt__'][-1].value['query']}")
                        
#                         # 질문 완료
#                         human_command = Command(resume={"user_query": "질문 완료"})
#                         result = app.invoke(human_command, config=config)
#                         step += 1
#                         print(f"Step {step} ({field} 질문 완료): {result.get('response')}")
                        
#                         # interrupt 확인 (체크리스트 답변 요청)
#                         if '__interrupt__' in result:
#                             interrupt_query = result['__interrupt__'][-1].value['query']
#                             print(f"Interrupt 발생: {interrupt_query}")
#                             print(f"[DEBUG] 이 interrupt는 체크리스트 답변 요청입니다.")
                            
#                             # 체크리스트 답변 - 테스트용 자동 입력
#                             answer = "전면 뷰"
#                             print(f"\n[{field} 카테고리] 답변: {answer}")
#                             human_command = Command(resume={"user_query": answer})
#                             result = app.invoke(human_command, config=config)
#                             step += 1
#                             print(f"Step {step} ({field} 답변: {answer}): {result.get('response')}")
                            
#                             # 체크리스트 데이터 확인
#                             checklist_data = result.get('checklist_data', {})
#                             print(f"현재 체크리스트 데이터: {checklist_data}")
                            
#                             # 완료 상태 확인
#                             completion_status = checklist_generator.get_completion_status(checklist_data)
#                             print(f"완성도 상태: {completion_status}")
                            
#                             print("\n=== 첫 번째 카테고리 테스트 완료! ===")
#                         else:
#                             print(f"Step {step}에서 interrupt가 없습니다.")
#                     else:
#                         print(f"Step {step}에서 interrupt가 없습니다.")
#                 else:
#                     print(f"Step {step}에서 interrupt가 없습니다.")
#             else:
#                 print(f"Step {step}에서 interrupt가 없습니다.")
#         else:
#             print(f"Step {step}에서 interrupt가 없습니다.")
                            
#     except Exception as e:
#         print(f"테스트 중 오류 발생: {e}")
#         import traceback
#         traceback.print_exc()

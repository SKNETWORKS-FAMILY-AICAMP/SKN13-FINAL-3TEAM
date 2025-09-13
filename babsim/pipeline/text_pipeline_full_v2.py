from __future__ import annotations
from typing import TypedDict, Dict, Any, List, Optional
from uuid import uuid4


from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt

def safe_merge_user_query(user_query, **kwargs):
    """user_query를 안전하게 딕셔너리와 병합하는 함수"""
    if isinstance(user_query, dict):
        return {**user_query, **kwargs}
    else:
        # user_query가 딕셔너리가 아닌 경우 기본값으로 처리
        return {"user_query": str(user_query) if user_query is not None else "", **kwargs}

from .base_state import PipelineState
from .components.intent_classifier import IntentClassifier
from .components.chat_manager import chat_manager
from .components.checklist_generator import checklist_generator
from .components.image_query_generator import ImageQueryGenerator
from .components.babsim_rag_adapter import BabsimRAGAdapter
from .components.image_generator import ImageGenerator
from .components.image_modifier import ImageModifier
from .components.generator_3d import generator_3d
from .components.generator_4d import generator_4d
from .llm_provider import kanana_llm_model

# 전역 변수로 스트리밍 응답 저장 (LangGraph 상태 외부)
_streaming_responses = {}

# RAG 처리에 필요한 컴포넌트들 (추가 필요시 import)
# from .components.query_rewriter import QueryRewriter
# from .components.rag_generator import RAGGenerator  
# from .components.answer_evaluator import AnswerEvaluator


_classifier = IntentClassifier()
_querygen = ImageQueryGenerator()
_rag = BabsimRAGAdapter()
_image_generator = ImageGenerator()
_image_modifier = ImageModifier()

# RAG 컴포넌트들 (추가 필요시 초기화)
# query_rewriter = QueryRewriter()
# rag_generator = RAGGenerator()
# answer_evaluator = AnswerEvaluator()


# 상태 정의는 base_state.py에서 import

# -----------------------------
# Utils
# -----------------------------
def _norm(s: Optional[str]) -> str:
    # 디버깅: slice 객체 감지
    if not isinstance(s, str) and s is not None:
        print(f"⚠️ _norm에 slice 객체 감지: {type(s)} = {s}")
    try:
        if isinstance(s, str):
            return s.strip().lower()
        elif s is None:
            return ""
        else:
            # 다른 타입인 경우 문자열로 변환 시도
            return str(s).strip().lower()
    except:
        print("SSSSSSSSSSSS")

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
    print(f"[분기] welcome_pick 노드 접근")
    # 사용자 입력이 있으면 state에 저장
    user_query = state.get("user_query", "")
    if user_query:
        print(f"[처리] 사용자 입력 수신: '{user_query[:50]}...'")
        return {"user_query": user_query, "response": WELCOME_TEXT}
    # 사용자 입력이 없으면 interrupt로 요청 
    user_query = interrupt({"query": WELCOME_TEXT})
    print(f"[처리] 기능 선택 요청 메시지 전송")
    
    return safe_merge_user_query(user_query, response=WELCOME_TEXT)

def process_welcome_input(state: PipelineState) -> PipelineState:
    """사용자의 welcome 입력을 처리하여 user_query에 저장"""
    print(f"[분기] process_welcome_input 노드 접근")
    # interrupt로 받은 사용자 입력을 user_query에 저장
    user_query = state.get("user_query", "")
    if user_query:
        print(f"[처리] 사용자 입력 처리 완료: '{user_query[:50]}...'")
        # user_query가 이미 있으면 그대로 전달
        return {"user_query": user_query}
    print(f"[처리] 사용자 입력 없음")
    return {}

# 사용자한테 첫번째 의도 받고 분류
# -----------------------------
# 1) Initial intent classification + apply user pick
# -----------------------------
def classify_and_apply_intent(state: PipelineState) -> Dict[str, Any]:
    print(f"[분기] classify_and_apply_intent 노드 접근")
    user_query = state.get("user_query", "")
    final_intent = _classifier.classify_initial_intent(user_query)
    print(f"[처리] 의도 분류 완료: '{user_query[:30]}...' -> '{final_intent}'")
    
    # image_generation 경로로 갈 때 image_mode에서 interrupt 발생
    if final_intent == "image_generation":
        state["waiting_node"] = "image_mode"
    
    return {"initial_intent": final_intent}


def route_top(state: PipelineState) -> str:
    it = _norm(state.get("initial_intent"))
    print(f"[라우팅] route_top - 의도: '{it}'")
    if it == "image_generation":
        print(f"[라우팅] 이미지 생성 경로로 라우팅")
        return "image_generation"
    elif it == "image_modification":
        print(f"[라우팅] 이미지 수정 경로로 라우팅")
        return "image_modification"
    elif it == "rag":
        print(f"[라우팅] RAG 질문 경로로 라우팅")
        return "rag"
    else:
        # Interrupt 걸리기 전, 첫 방문 시
        if state["waiting_node"] != "route_top":
            interrupt({"is_loading": True, "generation_type": "text"})
        else:
            print(f"[라우팅] 일반 대화 경로로 라우팅")
            return "general_conversation"


# -----------------------------
# 2) General conversation
# -----------------------------
def handle_general_conversation(state: PipelineState) -> Dict[str, Any]:
    print(f"[분기] handle_general_conversation 노드 접근")
    user_query = state.get("user_query", "")
    _append_history(state, "user", user_query)
    
    # vLLM 텍스트 응답 사용
    response = kanana_llm_model.generate_vllm_response_text(
        user_query, 
        max_length=1024
    )
    
    print(f"[처리] 일반 대화 텍스트 응답 생성 완료")
    
    # 기존 스트리밍 코드 (주석처리)
    # streaming_response = kanana_llm_model.generate_vllm_response_streaming(
    #     user_query, 
    #     max_length=512
    # )
    # import uuid
    # streaming_id = str(uuid.uuid4())
    # _streaming_responses[streaming_id] = streaming_response
    # return {"streaming_id": streaming_id, "response": "[스트리밍 응답]", "is_streaming": True}
    
    return {"response": response}


# -----------------------------
# 3) RAG branch - 완전한 RAG 처리 로직
# -----------------------------

# 1) HyDE 재작성
def rewrite_query(state: PipelineState) -> PipelineState:
    """사용자 쿼리를 HyDE 방식으로 재작성"""
    print(f"[분기] rewrite_query 노드 접근")
    user_query = state.get("user_query", "")
    
    # 간단한 쿼리 확장 (실제 QueryRewriter가 있다면 사용)
    # rq, _ = query_rewriter.hyde_expand_and_rewrite(user_query)
    # 현재는 기본 쿼리 사용
    rq = user_query

    # 첫 방문 시, Interrupt 걸리기 이전
    if state["waiting_node"] != "rewrite_query":
        interrupt({"is_loading": True, "generation_type": "text"})
    else:    
        print(f"[처리] 쿼리 재작성 완료: '{user_query[:30]}...'")
        return {
            **state, 
            "user_query": rq or user_query, 
            "rewritten": True,
            "pipeline_step": "rewrite_query",
        }

# 2) RAG 응답 생성
def generate_rag_response(state: PipelineState) -> PipelineState:
    """RAG를 통한 응답 생성"""
    print(f"[분기] generate_rag_response 노드 접근")
    pipeline_step = state.get("pipeline_step", "")
    user_query = state.get("user_query", "")
    chat_history = state.get("chat_history", [])

    # Retrieve docs
    try:
        docs = _rag.search_relevant_documents(query=user_query, k=5) or []
        print(f"[처리] RAG 문서 검색 완료: {len(docs)}개 문서")
    except Exception as e:
        docs = []
        print(f"[처리] RAG 문서 검색 실패: {e}")

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
    
    # RAG 응답 생성 - vLLM 텍스트 응답 사용
    response = kanana_llm_model.generate_vllm_response_text(
        merged_query, 
        max_length=1024
    )
    
    chat_history = chat_manager.add_message(chat_history, "user", user_query)
    chat_history = chat_manager.add_message(chat_history, "assistant", response)
    
    print(f"[처리] RAG 텍스트 응답 생성 완료")
    
    # 기존 스트리밍 코드 (주석처리)
    # streaming_response = kanana_llm_model.generate_vllm_response_streaming(
    #     merged_query, 
    #     max_length=512
    # )
    # import uuid
    # streaming_id = str(uuid.uuid4())
    # _streaming_responses[streaming_id] = streaming_response
    # return {
    #     **state, 
    #     "streaming_id": streaming_id,
    #     "response": "[스트리밍 응답]", 
    #     "chat_history": chat_history, 
    #     "messages_summarized": False,
    #     "pipeline_step": "generate_rag_response",
    #     "is_streaming": True
    # }
    
    return {
        **state, 
        "response": response, 
        "chat_history": chat_history, 
        "messages_summarized": False,
        "pipeline_step": "generate_rag_response"
    }

# 3) 답변 평가
def evaluate_answer(state: PipelineState) -> PipelineState:
    """생성된 답변의 품질 평가"""
    print(f"[분기] evaluate_answer 노드 접근")
    pipeline_step = state.get("pipeline_step", "")
    user_query = state.get("user_query", "")
    response = state.get("response", "")
    
    # 간단한 평가 로직 (실제 AnswerEvaluator가 있다면 사용)
    # score = answer_evaluator.analyze(
    #     user_query=user_query, answer=response, context_hint=""
    # )
    
    # 현재는 기본 점수 설정
    score = {
        "relevance": 0.7,  # 관련성 점수
        "adequacy": 0.7,   # 적절성 점수
        "coherence": 0.7   # 일관성 점수
    }
    
    print(f"[처리] 답변 품질 평가 완료: 관련성={score['relevance']}, 적절성={score['adequacy']}, 일관성={score['coherence']}")
    return {**state, "eval": score}

# 4) 품질 평가 라우팅
def retry_or_accept(state: PipelineState) -> PipelineState:
    """평가 결과에 따른 라우팅 결정"""
    print(f"[분기] retry_or_accept 노드 접근")
    eval_data = state.get("eval", {})
    rel = float(eval_data.get("relevance", 0.0))
    ade = float(eval_data.get("adequacy", 0.0))
    THRESH = 0.55
    
    if rel < THRESH or ade < THRESH:
        # 첫 방문 시, Interrupt 걸리기 이전
        if state["waiting_node"] != "build_query_from_history":
            interrupt({"is_loading": True, "generation_type": "text"})
        else:
            print(f"[처리] 품질 부족 - LLM fallback으로 라우팅 (관련성={rel}, 적절성={ade})")
            return {**state, "route": "llm_fallback"}
    print(f"[처리] 품질 양호 - 최종화로 라우팅 (관련성={rel}, 적절성={ade})")
    return {**state, "route": "ok"}

# 5) LLM fallback 처리 (품질이 낮을 때)
def handle_llm_fallback(state: PipelineState) -> PipelineState:
    """RAG 품질이 낮을 때 LLM fallback 처리"""
    print(f"[분기] handle_llm_fallback 노드 접근")
    try:
        user_query = state.get("user_query", "")
        chat_history = state.get("chat_history", [])
        
        # vLLM 텍스트 응답 사용
        response = kanana_llm_model.generate_vllm_response_text(
            user_query, 
            max_length=1024
        )
        chat_history = chat_manager.add_message(chat_history, "user", user_query)
        chat_history = chat_manager.add_message(chat_history, "assistant", response)
        
        print(f"[처리] LLM fallback 텍스트 응답 생성 완료")
        
        # 기존 스트리밍 코드 (주석처리)
        # streaming_response = kanana_llm_model.generate_vllm_response_streaming(
        #     user_query, 
        #     max_length=512
        # )
        # import uuid
        # streaming_id = str(uuid.uuid4())
        # _streaming_responses[streaming_id] = streaming_response
        # return {
        #     **state, 
        #     "streaming_id": streaming_id,
        #     "response": "[스트리밍 응답]", 
        #     "chat_history": chat_history, 
        #     "messages_summarized": False,
        #     "is_streaming": True
        # }
        
        return {
            **state, 
            "response": response, 
            "chat_history": chat_history, 
            "messages_summarized": False
        }
    except Exception as e:
        print(f"[처리] LLM Fallback 응답 생성 실패: {e}")
        fallback_response = "죄송합니다. 현재 답변을 생성할 수 없습니다."
        chat_history = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        chat_history = chat_manager.add_message(chat_history, "assistant", fallback_response)
        return {
            **state, 
            "response": fallback_response, 
            "chat_history": chat_history, 
            "messages_summarized": False
        }

# 라우팅 함수 
def route_retry_ok(state: PipelineState) -> str:
    """평가 결과에 따른 라우팅"""
    print(f"[라우팅] route_retry_ok - 평가 결과 확인")
    route = state.get("route")
    result = "handle_llm_fallback" if route == "llm_fallback" else "finalize"
    print(f"[라우팅] 라우팅 결과: {result} (route: {route})")
    return result


# -----------------------------
# 4) Image generation branch (guided/direct)
# -----------------------------

def image_mode(state: PipelineState) -> PipelineState:
    """이미지 생성 방식을 선택하도록 요청"""
    print(f"[분기] image_mode 노드 접근")
    msg = (
        """이미지 생성을 시작하겠습니다! 🎨

어떤 방식으로 진행하시겠습니까?

1️⃣ **체크리스트 기반 단계별 가이드**
   - 11가지 카테고리를 차근차근 채워가며 상세한 디자인 생성

2️⃣ **직접 이미지 생성**
   - 원하는 디자인을 자유롭게 설명하면 바로 이미지 생성

- 체크리스트 기반: "체크리스트" 또는 "단계별"
- 바로 생성: "바로" 또는 "직접"
- 건너뛰기: "건너뛰기", "skip", "다음", "next" 를 통해 바로 이미지 생성"""
    )
    user_query = state.get("user_query", "")
    # image_mode 노드 첫 방문 시 
    if state.get("waiting_node", "") != "image_mode":
        interrupt({"query": msg})
    else:
        print(f"[처리] 이미지 생성 방식 선택 요청 메시지 전송")
        return {"user_query": user_query, "response": msg}
    

def apply_image_mode(state: PipelineState) -> Dict[str, Any]:
    print(f"[분기] apply_image_mode 노드 접근")
    # user_query에서 받은 사용자 입력을 LLM으로 분류
    user_input = state.get("user_query", "")
    mode = _classifier.classify_image_generation_intent(user_input)
    
    # 분류 결과를 상태에 저장
    _append_history(state, "user", user_input)
    
    print(f"[처리] 이미지 생성 방식 분류 완료: '{user_input[:30]}...' -> '{mode}'")
    return {"image_mode": mode}

def route_image_mode(state: PipelineState) -> str:
    print(f"[라우팅] route_image_mode - 전체 상태: {state}")
    mode = state.get("image_mode", "guided")
    print(f"[라우팅] route_image_mode - 선택된 방식: '{mode}'")
    
    if mode == "guided":
        print(f"[라우팅] 체크리스트 기반 가이드 경로로 라우팅")
    else:
        print(f"[라우팅] 직접 생성 경로로 라우팅")
    return mode


# Guided loop
def guided_prepare_question(state: PipelineState) -> Dict[str, Any]:
    """체크리스트 초기화 및 준비"""
    print(f"[분기] guided_prepare_question 노드 접근")
    form_data = dict(state.get("checklist_data") or {})
    
    # 체크리스트 데이터가 없으면 초기화
    if not form_data:
        # 모든 필드를 빈 문자열로 초기화
        form_data = {field: "" for field in checklist_generator.all_fields}
        print(f"[처리] 체크리스트 초기화 완료")
    
    # # 자동 채우기 시도 (사용자 쿼리가 있는 경우)
    # user_query = state.get("user_query", "")
    # if user_query and user_query not in ["guided", "direct"]:
    #     autofill = checklist_generator.auto_fill_from_description(user_query) or {}
    #     if autofill:
    #         form_data.update(autofill)
    #         print(f"[처리] 자동 채우기 완료: {len(autofill)}개 필드")

    missing_req = checklist_generator.missing_required_fields(form_data)
    missing_opt = checklist_generator.missing_optional_fields(form_data)
    
    print(f"[처리] 누락된 필수 필드: {missing_req}")
    print(f"[처리] 누락된 선택 필드: {missing_opt}")

    if not missing_req and not missing_opt:
        state["is_form_complete"] = True
        state["completion_status"] = checklist_generator.get_completion_status(form_data)
        print(f"[처리] 체크리스트 완료 - 이미지 생성으로 진행")
        return {"checklist_data": form_data, "pipeline_step": "guided_done"}

    # 첫 번째 누락된 필드를 current_field로 설정
    missing = missing_req if missing_req else missing_opt
    current_field = missing[0]
    
    print(f"[처리] 다음 질문 필드 설정: '{current_field}' (필수: {len(missing_req)}, 선택: {len(missing_opt)})")
    
    # 체크리스트 데이터와 current_field를 상태에 저장
    state["current_field"] = current_field
    return {"checklist_data": form_data, "current_field": current_field}

def guided_next_category(state: PipelineState) -> PipelineState:
    """다음 체크리스트 카테고리로 이동"""
    print(f"[분기] guided_next_category 노드 접근")
    form_data = dict(state.get("checklist_data") or {})
    user_query = (state.get("user_query") or "").strip()

    # 필수 필드부터 확인
    missing_req = checklist_generator.missing_required_fields(form_data)    
    print(f"[DEBUG] missing_req: {missing_req}")

    # 선택 필드 확인
    missing_opt = checklist_generator.missing_optional_fields(form_data)
    print(f"[DEBUG] missing_opt: {missing_opt}")

    # 첫 번째 누락된 필드를 current_field로 설정
    missing = missing_req if missing_req else missing_opt
    current_field = missing[0] if missing else ""
    print(f"[DEBUG] guided_next_category 에서 설정한 current_field : {current_field}")
    print(f"[DEBUG] form_data: {form_data}")

    # 노드 첫 방문이라면
    if state["waiting_node"] != "guided_next_category":
        # "건너뛰기" 확인
        if user_query.lower() in ["건너뛰기", "skip", "다음", "next"]:
            print(f"[처리] 건너뛰기 - 이미지 생성으로 진행")
            return {"response": "체크리스트를 건너뛰고 이미지 생성을 진행합니다. 🎨", "pipeline_step": "build_query_from_history"}
        
        if missing_req:
            
            # 체크리스트 시작 안내 (첫 번째 질문인 경우)
            field_description = checklist_generator.field_descriptions.get(current_field, "")
            
            if len(form_data) == 0 or all(v == "" for v in form_data.values()):
                intro_message = f"이제 체크리스트를 하나씩 채워보겠습니다!\n\n첫 번째 카테고리: {current_field}\n\n{field_description}\n\n{current_field}에 대해 자유롭게 질문하세요!\n현대자동차 디자인 전문가 AI가 답변해드립니다.\n\n질문이 끝나시면 '질문 완료'라고 입력해주세요.\n\n명령어:\n- 다음 질문: '질문 완료', '완료', '다음', 'next'\n- 이미지 생성: '건너뛰기', 'skip'"
            else:
                intro_message = f"다음 카테고리: {current_field}\n\n{field_description}\n\n{current_field}에 대해 자유롭게 질문하세요!\n현대자동차 디자인 전문가 AI가 답변해드립니다.\n\n질문이 끝나시면 '질문 완료'라고 입력해주세요.\n\n명령어:\n- 다음 질문: '질문 완료', '완료', '다음', 'next'\n- 이미지 생성: '건너뛰기', 'skip'"
            
            print(f"[처리] 다음 필수 필드 설정: '{current_field}'")
            
            # 체크리스트 완성도 업데이트
            completion_status = checklist_generator.get_completion_status(form_data)
            print(f"[처리] 체크리스트 완성도: {completion_status.get('completion_percentage', 0)}%")
            
            # interrupt로 사용자 입력을 받음 / 다음 카테고리 넘어갈 때 이전 체크리스트 프론트 반영
            interrupt({"query": intro_message, "checklist_data": form_data, "completion_status": completion_status})
            
        else:
            
            if missing_opt:
                
                optional_message = f"필수 질문이 모두 완료되었습니다! 🎉\n\n선택 질문도 채우시겠습니까?\n\n필수 정보로 충분하다면, '건너뛰기'를 입력해주세요.\n\n다음 선택 카테고리: {current_field}\n\n{current_field}에 대해 자유롭게 질문하세요!\n현대자동차 디자인 전문가 AI가 답변해드립니다.\n\n명령어:\n- 다음 질문: '질문 완료', '완료', '다음', 'next'\n- 이미지 생성: '건너뛰기', 'skip'"
                
                print(f"[처리] 다음 선택 필드 설정: '{current_field}'")
                
                # interrupt로 사용자 입력을 받음
                interrupt({"query": optional_message})
                
            else:
                # 모든 질문 완료
                print(f"[처리] 모든 질문 완료 - 이미지 생성으로 진행")
                return {"response": "체크리스트가 모두 완료되었습니다! 🎉 이제 이미지 생성을 시작하겠습니다.", "pipeline_step": "build_query_from_history"}
        
    # Interrupt 이후 돌아온 것이라면 "guided_llm_chat" 으로 / 이 경로가 챗봇 경로
    else:
        # current_field_conversation 초기화
        state["current_field_conversation"] = ""
        
        # 카테고리 자체 건너뛰기 - 요약없이 바로 다음 카테고리로
        if user_query.lower() in ["질문 완료", "완료", "다음", "next"]:
            # 현재 current_field에 대해 form_data를 "-"로 설정
            if current_field:
                form_data = state.get("checklist_data", {})
                form_data[current_field] = "-"
                print(f"[처리] 카테고리 건너뛰기: '{current_field}' = '-', form_data {form_data}")

                # 체크리스트 완성도 업데이트
                completion_status = checklist_generator.get_completion_status(form_data)

                return {
                    "pipeline_step": "guided_next_category",
                    "waiting_node": "",  # waiting_node 초기화 -> 다음 카테고리 처음부터 질문 시작 
                    "user_query": "",    # user_query 초기화 
                    "checklist_data": form_data,  # 업데이트된 체크리스트 데이터 반환
                    "completion_status": completion_status
                }

        if user_query.lower() in ["건너뛰기", "skip", "건너 뛰기"]:
            print(f"[처리] 건너뛰기 - 이미지 생성으로 진행")
            return {"response": "건너뛰어보겠습니다! 🎉 이제 이미지 생성을 시작하겠습니다.", "pipeline_step": "build_query_from_history"}


        # 첫 방문 시, Interrupt 걸리기 이전
        if state["waiting_node"] != "build_query_from_history":
            interrupt({"is_loading": True, "generation_type": "text"})
        else:
            return safe_merge_user_query(
                    user_query,
                    pipeline_step="guided_llm_chat", 
                    current_field=current_field,
                    waiting_node="guided_llm_chat", # 다시 들어왔을때 위 내용을 돌기 위해 
                )

def guided_llm_chat(state: PipelineState) -> PipelineState:
    """LLM과의 자유로운 대화 처리"""
    print(f"[분기] guided_llm_chat 노드 접근")
    user_query = (state.get("user_query") or "").strip()
    current_field = state.get("current_field", "")
    current_field_conversation = state.get("current_field_conversation", "")
    
    # print(f"[text_pipeline_full_v2.py] [DEBUG] guided_llm_chat - current_field: '{current_field}', user_input: '{user_input}'")
    # print(f"[text_pipeline_full_v2.py] [DEBUG] guided_llm_chat - 전체 state keys: {list(state.keys())}")
    # print(f"[text_pipeline_full_v2.py] [DEBUG] guided_llm_chat - 전체 state: {state}")
    print(f"[text_pipeline_full_v2.py] [DEBUG] 누적된 대화: {current_field_conversation}")
    # "질문 완료" 확인 -> 카테고리 요약으로
    if user_query.lower() in ["질문 완료", "완료", "다음", "next"]:
        # LLM 대화 종료, 체크리스트 답변 요청으로 이동
        _append_history(state, "user", user_query)
        print(f"[처리] 질문 완료 - 다음 체크리스트 항목으로 이동")
        return {"pipeline_step": "guided_ask_answer", "current_field": current_field}
        
    if user_query.lower() in ["건너뛰기", "skip", "다음", "next"]:
        print(f"[처리] 건너뛰기 - 이미지 생성으로 진행")
        return {"response": "선택 체크리스트를 건너뛰고 이미지 생성을 진행합니다.🎨", "pipeline_step": "build_query_from_history"}
    else:
        # 사용자가 LLM에게 질문한 경우
        print(f"[처리] LLM 질문 처리: '{user_query[:30]}...' (필드: '{current_field}')")
        
        # Kanana LLM에게 질문 - 텍스트 응답 사용
        response = kanana_llm_model.generate_vllm_response_text(
            user_query, 
            max_length=1024
        )
        
        # 대화 기록
        _append_history(state, "user", user_query)
        _append_history(state, "assistant", response)

        # current_field_conversation에 user_query 누적
        current_field_conversation = state.get("current_field_conversation", "") + f"\n사용자: {user_query}\nAI: {response}"

        return {"response": response, "current_field_conversation": current_field_conversation, "waiting_node": "guided_llm_chat"}
        
def guided_llm_chat_save(state: PipelineState) -> PipelineState:
    """current_field_conversation 저장을 위한 노드"""
    response = state.get("response", "")
    current_field_conversation = state.get("current_field_conversation", "")
    current_field = state.get("current_field", "")

    user_query = state.get("user_query")

    # Interrupt 이전
    if state["waiting_node"] != "guided_llm_chat_save":
        interrupt({"query": response, "current_field_conversation": current_field_conversation, "current_field": current_field})
    else:
        return {"user_query": user_query}

def guided_ask_answer(state: PipelineState) -> PipelineState:
    """체크리스트 답변 요청 - 사용자가 최종 요약"""
    print(f"[분기] guided_ask_answer 노드 접근")
    current_field = state.get("current_field", "")
    user_query = (state.get("user_query") or "").strip()
    form_data = dict(state.get("checklist_data") or {})
    
    # # "건너뛰기" 확인
    # if user_query.lower() in ["건너뛰기", "skip", "다음", "next"]:
    #     print(f"[처리] 건너뛰기 - 이미지 생성으로 진행")
    #     return {"response": "선택 체크리스트를 건너뛰고 이미지 생성을 진행합니다.🎨", "pipeline_step": "build_query_from_history"}
    if state["waiting_node"] != "guided_ask_answer":
        if current_field:
            # 체크리스트 질문 생성
            missing_req = checklist_generator.missing_required_fields(form_data)
            missing_opt = checklist_generator.missing_optional_fields(form_data)
            missing = missing_req if missing_req else missing_opt
            
            if missing and missing[0] == current_field:
                question = checklist_generator.next_question(missing, form_data)
                
                # LLM 대화를 바탕으로 한 답변 요청
                answer_request = f"위의 대화를 바탕으로 {current_field}에 대한 답변을 입력해주세요:\n{question}"
                
                print(f"[처리] 체크리스트 답변 요청: '{current_field}'")
                interrupt({"query": answer_request})
    else:
        # current_field_conversation에 user_query 누적
        current_field_conversation = state.get("current_field_conversation", "") + f"\n사용자: {user_query}"
        
        print(f"[처리] 다음 단계로 진행")
        return safe_merge_user_query(user_query, response="다음 단계로 진행합니다.", pipeline_step="guided_ask_answer", current_field=current_field, current_field_conversation=current_field_conversation)

def guided_record(state: PipelineState) -> Dict[str, Any]:
    """체크리스트 답변 저장 후 다음 카테고리로 이동"""
    print(f"[분기] guided_record 노드 접근")
    field = state.get("current_field")
    user_query = (state.get("user_query") or "").strip()
    form = dict(state.get("checklist_data") or {})
    pipeline_step = state.get("pipeline_step", "")
    
    if pipeline_step == "guided_ask_answer":
        # 체크리스트 답변을 받는 단계
        if field:
            # current_field_conversation을 사용하여 자동 추출 시도
            current_field_conversation = state.get("current_field_conversation", "")
            auto_filled_data = checklist_generator.auto_fill_from_description(current_field_conversation, field)
            print(f"[처리] 자동 추출된 데이터: {auto_filled_data}")
            
            # 현재 필드와 일치하는 데이터가 있으면 사용
            if field in auto_filled_data and auto_filled_data[field]:
                # 새로운 구조: {field: {sub_field1: value1, sub_field2: value2}}
                field_data = auto_filled_data[field]
                if isinstance(field_data, dict):
                    # 하위 필드들을 form에 병합
                    for sub_field, value in field_data.items():
                        if value and str(value).strip():
                            form[sub_field] = value
                            print(f"[처리] 자동 추출로 하위 필드 저장: '{sub_field}' = '{value[:30]}...'")
                else:
                    # 단일 값인 경우 (viewpoint, surfacing, aero 등)
                    form[field] = field_data
                    print(f"[처리] 자동 추출로 체크리스트 답변 저장: '{field}' = '{field_data[:30]}...'")
            else:
                # 자동 추출 실패 시 원래 사용자 입력 사용
                form[field] = user_query
                print(f"[처리] 수동 입력으로 체크리스트 답변 저장: '{field}' = '{user_query[:30]}...'")
            
            # 하위 필드들이 있는 경우 모든 하위 필드를 기록
            if field in auto_filled_data and auto_filled_data[field] and isinstance(auto_filled_data[field], dict):
                sub_fields = []
                for sub_field, value in auto_filled_data[field].items():
                    if value and str(value).strip():
                        sub_fields.append(f"{sub_field}: {value}")
                if sub_fields:
                    _append_history(state, "user", f"{field}: {', '.join(sub_fields)}")
                else:
                    _append_history(state, "user", f"{field}: {user_query}")
            else:
                _append_history(state, "user", f"{field}: {form[field]}")
            
            # 체크리스트 완성도 업데이트
            completion_status = checklist_generator.get_completion_status(form)
            print(f"[처리] 체크리스트 완성도 업데이트: {completion_status.get('completion_percentage', 0)}%")
            
            return {
                "checklist_data": form, 
                "pipeline_step": "guided_next_category",
                "completion_status": completion_status,
            }
        else:
            # LLM 대화 단계 (guided_llm_chat에서 처리됨)
            print(f"[처리] LLM 대화 단계 - 답변 저장하지 않음")
            return {"checklist_data": form, "pipeline_step": "guided_recorded"}
    else:
        # 다른 pipeline_step인 경우 - 답변 저장하지 않음
        print(f"[처리] 다른 단계 - 답변 저장하지 않음: '{pipeline_step}'")
    return {"checklist_data": form, "pipeline_step": "guided_recorded"}


def guided_continue_or_done(state: PipelineState) -> str:
    print(f"[라우팅] guided_continue_or_done - 체크리스트 완성도 확인")
    form = state.get("checklist_data") or {}
    done = checklist_generator.get_completion_status(form).get("is_complete", False) \
           or (checklist_generator.missing_required_fields(form) == [] and checklist_generator.missing_optional_fields(form) == [])
    result = "done" if done else "continue"
    print(f"[라우팅] 체크리스트 상태: {result}")
    return result

def build_query_from_history(state: PipelineState) -> Dict[str, Any]:
    print(f"[분기] build_query_from_history 노드 접근")
    # 임시 로딩창 - 노드 첫 입장 시 
    if state["waiting_node"] != "build_query_from_history":
        interrupt({"is_loading": True, "generation_type": "image"})
    else:
        # 이미지 쿼리 생성
        image_query = _querygen.generate_image_query(state)
        
        print(f"[처리] 이미지 쿼리 생성 완료: '{image_query[:50]}...'")
        return {**state, "image_query": image_query, "waiting_node": ""}

# Direct
def direct_prompt(state: PipelineState) -> Dict[str, Any]:
    print(f"[분기] direct_prompt 노드 접근")
    p = (
        "원하는 자동차 디자인을 자유롭게 상세히 적어주세요.\n"
        "예) '중형 SUV, 3/4 front, 긴 휠베이스, 짧은 오버행, 깨끗한 바디, parametric grille, pixel DRL, 대형 알로이 휠, 파노라믹 글라스 루프, 매트 실버'"
    )
    _append_history(state, "assistant", p)
    # 다음에 direct_freeform에서 interrupt 발생
    print(f"[처리] 직접 생성 안내 메시지 전송")
    return {"response": p}

def direct_freeform(state: PipelineState) -> PipelineState:
    """자유형식 입력을 요청"""
    print(f"[분기] direct_freeform 노드 접근")
    user_query = state.get("user_query", "")
    question = state.get("response") or "자유기술을 입력하세요."
    if state["waiting_node"] != "direct_freeform":
        interrupt({"query": question})
    else:
        print(f"[처리] 자유형식 입력 요청 메시지 전송")
        return safe_merge_user_query(user_query, response=question)

def direct_record_and_build_query(state: PipelineState) -> Dict[str, Any]:
    print(f"[분기] direct_record_and_build_query 노드 접근")
    # 임시 로딩창 - 노드 첫 입장 시 
    if state["waiting_node"] != "direct_record_and_build_query":
        interrupt({"is_loading": True, "generation_type": "image"})
    else:
        # user_query에서 받은 사용자 입력을 사용
        desc = (state.get("user_query") or "").strip()
        if desc:
            _append_history(state, "user", desc)
        # chat_history와 desc를 이용한 이미지 쿼리 생성 (폼 데이터 없이)
        chat_history = state.get("chat_history", [])
        desc = state.get("response", "")  # 현재 응답을 desc로 사용
        query = _querygen.generate_image_query_from_chat(chat_history=chat_history, desc=desc)
        state["image_query"] = query
        print(f"[처리] 직접 생성 쿼리 생성 완료: '{query[:50]}...'")
        return {**state, "image_query": query}


# Generate
def run_image_generation(state: PipelineState) -> Dict[str, Any]:
    """
    ImageGenerator 인스턴스를 사용하여 이미지 생성
    """
    print(f"[분기] run_image_generation 노드 접근")
    
    # 이미지 생성
    response, s3_url = _image_generator.generate_image(state)
    
    # 멀티턴을 위해 대화 기록 업데이트
    updated = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
    updated = chat_manager.add_message(updated, "assistant", response)
    
    print(f"[처리] 이미지 생성 완료: '{response[:50]}...' (S3: {s3_url if s3_url else 'None'}...)")
    return {**state, "chat_history": updated, "response": response, "s3_url": s3_url, "generation_type": "image"}

def ask_modify(state: PipelineState) -> PipelineState:
    """이미지 수정 / 3D 생성 / 4D 생성 여부를 GPT-4o로 판단"""
    print(f"[분기] ask_modify 노드 접근")
    user_input = (state.get("user_query") or "").strip()
    
    # Interrupt 를 통해 입력을 받아온 상태라면 
    if state["waiting_node"] == "ask_modify":
        # 사용자 입력이 있으면 GPT-4o로 판단
        if user_input:
            modify_intent = _classifier.classify_modification_intent(user_input)
            print(f"[처리] 수정 의도 판단: '{user_input[:30]}...' -> '{modify_intent}'")
            
            if modify_intent == "modify":
                # 수정을 원함 - 수정 사항을 state에 저장
                print(f"[처리] 이미지 수정 경로로 진행")
                return {
                    "response": "이미지 수정을 진행하겠습니다.", 
                    "pipeline_step": "modify_image",
                    "modification_request": user_input  # 수정 사항 저장
                }
            elif modify_intent == "3d_generation":
                # 3D 생성을 원함
                print(f"[처리] 3D 생성 경로로 진행")
                return {
                    "response": "3D 영상을 생성하겠습니다.",
                    "pipeline_step": "run_3d_generation",
                    "modification_request": user_input  # 3D / 4D 생성에 user input 사용할 수도..
                }
            elif modify_intent == "4d_generation":
                # 4D 생성을 원함
                print(f"[처리] 4D 생성 경로로 진행")
                return {
                    "response": "4D 영상을 생성하겠습니다.",
                    "pipeline_step": "run_4d_generation",
                    "modification_request": user_input
                }
            else:
                # 수정을 원하지 않음
                print(f"[처리] 수정 요청 없음 - 대화 종료")
                return {"response": "감사합니다. 여기까지 짹짹이였습니다 짹 >< 🐤", "pipeline_step": "finish"}
    else:
        # 사용자 입력이 없으면 질문
        question = "이미지를 수정하시겠습니까? 수정 사항을 말씀해주시거나, '아니오'라고 답해주세요.\n혹은 생성된 이미지를 이용해 3D 나 4D 에서의 확장된 경험을 맛보실 수도 있습니다."
        print(f"[처리] 수정 여부 질문 메시지 전송")
        interrupt({"query": question})
        
# 이미지 수정
def modify_image(state: PipelineState) -> PipelineState:
    """
    ImageModifier 인스턴스를 사용하여 이미지 수정 - 노드 X 함수 O
    """
    print(f"[분기] modify_image 노드 접근")
    
    # 수정 사항을 state에 추가
    modification_request = state.get("modification_request", "")
    print(f"[처리] 이미지 수정 요청: '{modification_request[:50]}...'")
    
    # 이미지 수정을 위한 state 준비
    modify_state = {**state, "user_query": modification_request}
    
    # 이미지 수정
    response, s3_url = _image_modifier.modify_image(modify_state)
    
    # 멀티턴을 위해 대화 기록 업데이트
    updated = chat_manager.add_message(state.get("chat_history", []), "user", modification_request)
    updated = chat_manager.add_message(updated, "assistant", response)
    
    print(f"[처리] 이미지 수정 완료: '{response[:50]}...' (S3: {s3_url[:30] if s3_url else 'None'}...)")
    return {**state, "chat_history": updated, "response": response, "s3_url": s3_url}

# -----------------------------
# 3D/4D Generation nodes
# -----------------------------

def ask_3d_4d_generation(state: PipelineState) -> PipelineState:
    """3D/4D 생성 확인 노드 - 이미지 표시와 함께 질문"""
    s3_url = state.get("s3_url", "")
    
    if not s3_url:
        state["response"] = "이미지 URL이 없습니다. 먼저 이미지를 생성해주세요."
        return state
    
    message = (
        f"🎨 생성된 이미지:\n\n"
        f"![생성된 이미지]({s3_url})\n\n"
        f"이 이미지로 3D 또는 4D 모델을 생성하시겠습니까?\n\n"
        f"1️⃣ **3D 모델 생성** - 정적 3D 모델\n"
        f"2️⃣ **4D 모델 생성** - 애니메이션이 포함된 3D 모델\n"
        f"3️⃣ **다른 이미지 선택** - 이전에 생성한 다른 이미지 사용\n"
        f"4️⃣ **다른 작업** - 이미지 수정이나 새로운 이미지 생성\n\n"
        f"원하는 옵션을 선택해주세요."
    )
    
    user_query = interrupt({"query": message})
    return safe_merge_user_query(user_query, response=message)

def route_3d_4d_choice(state: PipelineState) -> str:
    """3D/4D 선택 라우팅"""
    user_input = _norm(state.get("user_query", ""))
    
    if "3d" in user_input or "3D" in user_input or "정적" in user_input:
        return "run_3d_generation"
    elif "4d" in user_input or "4D" in user_input or "애니메이션" in user_input:
        return "run_4d_generation"
    elif "다른 이미지" in user_input or "이미지 선택" in user_input:
        return "select_other_image"
    elif "수정" in user_input or "modify" in user_input:
        return "modify_image"
    elif "새로운" in user_input or "생성" in user_input or "generate" in user_input:
        return "image_generation"
    else:
        # 기본적으로 3D 생성으로 라우팅
        return "run_3d_generation"

def select_other_image(state: PipelineState) -> PipelineState:
    """다른 이미지 선택 노드 - 세션의 이미지들 표시"""
    from JJACKLETTE.models import PromptLog, ChatSession
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # 현재 사용자 ID 가져오기 (세션에서)
    user_id = state.get("user_id")
    if not user_id:
        message = "사용자 정보를 찾을 수 없습니다. 다시 로그인해주세요."
        user_query = interrupt({"query": message})
        return safe_merge_user_query(user_query, response=message)
    
    try:
        # 사용자의 최근 세션들에서 이미지 타입의 결과들 조회
        user_sessions = ChatSession.objects.filter(user_id=user_id).order_by('-started_at')[:5]  # 최근 5개 세션
        
        image_results = []
        for session in user_sessions:
            # 각 세션에서 이미지 타입의 결과들 조회
            session_images = PromptLog.objects.filter(
                session=session,
                result_type='image',
                result_path__isnull=False
            ).exclude(result_path='').order_by('-created_at')[:3]  # 세션당 최근 3개
            
            for img in session_images:
                image_results.append({
                    'prompt_id': str(img.prompt_id),
                    'user_prompt': img.user_prompt[:50] + "..." if len(img.user_prompt) > 50 else img.user_prompt,
                    'result_path': img.result_path,
                    'created_at': img.created_at,
                    'session_title': session.session_title or f"세션 {session.started_at.strftime('%m/%d %H:%M')}"
                })
        
        # 최신순으로 정렬 (최근 10개만)
        image_results = sorted(image_results, key=lambda x: x['created_at'], reverse=True)[:10]
        
        if not image_results:
            message = "선택할 수 있는 이미지가 없습니다. 먼저 이미지를 생성해주세요."
            user_query = interrupt({"query": message})
            return safe_merge_user_query(user_query, response=message)
        
        # 이미지 목록 메시지 생성
        message_parts = ["📸 사용 가능한 이미지들:\n"]
        
        for i, img in enumerate(image_results, 1):
            message_parts.append(
                f"{i}️⃣ **{img['session_title']}**\n"
                f"프롬프트: {img['user_prompt']}\n"
                f"![이미지 {i}]({img['result_path']})\n"
            )
        
        message_parts.extend([
            f"\n이미지를 선택하거나 '다른 작업'을 선택해주세요.\n\n",
            f"- 이미지 선택: '1', '2', '3' 등 (번호 입력)\n",
            f"- 다른 작업: '다른 작업'"
        ])
        
        message = "".join(message_parts)
        
        # 선택된 이미지 정보를 상태에 저장
        state["available_images"] = image_results
        
        user_query = interrupt({"query": message})
        return safe_merge_user_query(user_query, response=message)
        
    except Exception as e:
        print(f"[분기] select_other_image 오류: {str(e)}")
        message = "이미지 목록을 불러오는 중 오류가 발생했습니다. 다시 시도해주세요."
        user_query = interrupt({"query": message})
        return safe_merge_user_query(user_query, response=message)

def apply_image_selection(state: PipelineState) -> Dict[str, Any]:
    """이미지 선택 적용"""
    user_input = _norm(state.get("user_query", ""))
    available_images = state.get("available_images", [])
    
    if "다른 작업" in user_input:
        return {"response": "다른 작업을 선택했습니다."}
    
    # 숫자 입력 확인 (1, 2, 3, ...)
    try:
        # 입력에서 숫자 추출
        import re
        numbers = re.findall(r'\d+', user_input)
        if numbers:
            selected_index = int(numbers[0]) - 1  # 0-based index
            
            if 0 <= selected_index < len(available_images):
                selected_image = available_images[selected_index]
                selected_url = selected_image['result_path']
                
                print(f"[분기] 사용자가 이미지 선택: {selected_index + 1}번 - {selected_url}")
                
                return {
                    "response": f"이미지 {selected_index + 1}번을 선택했습니다.",
                    "s3_url": selected_url,
                    "selected_image_info": selected_image
                }
            else:
                return {"response": f"잘못된 번호입니다. 1부터 {len(available_images)} 사이의 숫자를 입력해주세요."}
        else:
            return {"response": "번호를 입력해주세요. (예: 1, 2, 3)"}
            
    except (ValueError, IndexError) as e:
        print(f"[분기] apply_image_selection 오류: {str(e)}")
        return {"response": "잘못된 입력입니다. 번호를 입력해주세요."}

def route_to_other_tasks(state: PipelineState) -> str:
    """다른 작업으로 라우팅"""
    user_input = _norm(state.get("user_query", ""))
    
    if "수정" in user_input or "modify" in user_input:
        return "modify_image"
    elif "새로운" in user_input or "생성" in user_input or "generate" in user_input:
        return "image_generation"
    else:
        # 기본적으로 이미지 수정으로 라우팅
        return "modify_image"

def run_3d_generation(state: PipelineState) -> Dict[str, Any]:
    """3D 생성 노드"""
    print(f"[분기] run_3d_generation 노드 접근")
    
    s3_url = state.get("s3_url", "")
    if not s3_url:
        return {"error": "이미지 URL이 없습니다."}
    
    # 3D 생성기 사용
    result = generator_3d.generate_3d_model(s3_url)
    
    if "error" in result:
        return {"response": f"3D 생성 실패: {result['error']}"}
    
    # 결과를 상태에 저장
    state["s3_url_3d"] = result["s3_url_3d"]
    state["generation_type"] = result["generation_type"]
    
    return {
        "s3_url_3d": result["s3_url_3d"],
        "generation_type": result["generation_type"],
        "response": f"3D 모델이 생성되었습니다! 🎉\n\n3D 모델: {result['s3_url_3d']}",
        "waiting_node": "show_3d_4d_result"
    }

def run_4d_generation(state: PipelineState) -> Dict[str, Any]:
    """4D 생성 노드"""
    print(f"[분기] run_4d_generation 노드 접근")
    
    s3_url = state.get("s3_url", "")
    if not s3_url:
        return {"error": "이미지 URL이 없습니다."}
    
    # 4D 생성기 사용
    result = generator_4d.generate_4d_model(s3_url)
    
    if "error" in result:
        return {"response": f"4D 생성 실패: {result['error']}"}
    
    # 결과를 상태에 저장
    state["s3_url_4d"] = result["s3_url_4d"]
    state["generation_type"] = result["generation_type"]
    
    return {
        "s3_url_4d": result["s3_url_4d"],
        "generation_type": result["generation_type"],
        "response": f"4D 모델이 생성되었습니다! 🎉\n\n4D 모델: {result['s3_url_4d']}",
        "waiting_node": "show_3d_4d_result"
    }

def show_3d_4d_result(state: PipelineState) -> PipelineState:
    """3D/4D 결과 표시 및 후속 액션 노드"""
    generation_type = state.get("generation_type", "")
    s3_url_3d = state.get("s3_url_3d", "")
    s3_url_4d = state.get("s3_url_4d", "")
    
    if generation_type == "3d" and s3_url_3d:
        model_url = s3_url_3d
        model_type = "3D"
    elif generation_type == "4d" and s3_url_4d:
        model_url = s3_url_4d
        model_type = "4D"
    else:
        state["response"] = "생성된 모델이 없습니다."
        return state
    
    message = (
        f"🎉 {model_type} 모델 생성 완료!\n\n"
        f"![{model_type} 모델]({model_url})\n\n"
        f"다음 중 하나를 선택해주세요:\n\n"
        f"1️⃣ **{model_type} 재생성** - 다른 설정으로 다시 생성\n"
        f"2️⃣ **4D 생성** - 애니메이션 모델로 변환 (3D인 경우)\n"
        f"3️⃣ **다른 작업** - 이미지 수정이나 새로운 이미지 생성\n"
        f"4️⃣ **완료** - 작업 종료\n\n"
        f"원하는 옵션을 선택해주세요."
    )
    
    user_query = interrupt({"query": message})
    return safe_merge_user_query(user_query, response=message)

def route_3d_4d_result_choice(state: PipelineState) -> str:
    """3D/4D 결과 후속 액션 라우팅"""
    user_input = _norm(state.get("user_query", ""))
    generation_type = state.get("generation_type", "")
    
    if "재생성" in user_input or "다시" in user_input:
        if generation_type == "3d":
            return "run_3d_generation"
        else:
            return "run_4d_generation"
    elif "4d" in user_input or "4D" in user_input or "애니메이션" in user_input:
        return "run_4d_generation"
    elif "수정" in user_input or "modify" in user_input:
        return "modify_image"
    elif "새로운" in user_input or "생성" in user_input or "generate" in user_input:
        return "image_generation"
    elif "완료" in user_input or "finish" in user_input or "종료" in user_input:
        return "finish"
    else:
        # 기본적으로 완료로 라우팅
        return "finish"

# -----------------------------
# 5) Image modification branch
# -----------------------------
def mod_intro(state: PipelineState) -> Dict[str, Any]:
    "url 받기 / 생성된 s3_url 사용만 구현 - 기존 이미지 중 선택 미구현"
    print(f"[분기] mod_intro 노드 접근")
    text = (
        "이미지 수정 모드입니다.\n"
        "수정할 자동차 이미지의 URL을 붙여넣어 주세요 (또는 업로드 후 접근 가능한 링크를 제공해 주세요).\n"
        "혹은 이전에 생성된 이미지를 사용하기 위해서는 '계속' 이라고 입력해주세요."
    )
    _append_history(state, "assistant", text)
    print(f"[처리] 이미지 수정 모드 안내 메시지 전송")
    return {"response": text, "generation_type": ""}    # generation_type 초기화 -> 결과 계속 안뜨게

def mod_image_url(state: PipelineState) -> PipelineState:
    """수정할 이미지 URL을 요청"""
    print(f"[분기] mod_image_url 노드 접근")
    question = state.get("response") or "수정할 이미지 URL을 입력하세요."
    if state["waiting_node"] != "mod_image_url":
        interrupt({"query": question})
        print(f"[처리] 이미지 URL 입력 요청 메시지 전송")
    else:
        return safe_merge_user_query(state.get("user_query"), response=question)

def store_mod_image(state: PipelineState) -> Dict[str, Any]:
    print(f"[분기] store_mod_image 노드 접근")
    # user_query에서 받은 사용자 입력을 사용
    user_query = (state.get("user_query") or "").strip()
    if user_query == "계속":
        if not state.get("s3_url"):
            return {"error": "기존에 생성된 이미지가 존재하지 않습니다."}
        else:
            url = state.get("s3_url")
    elif user_query: # url 형식
        # image_modifier.modify_image expects 'input_image' in state (commonly)
        url = user_query
        _append_history(state, "user", f"[이미지 URL] {url}")
        print(f"[처리] 이미지 URL 저장 완료: '{url[:50]}...'")
    else:
        print(f"[처리] 이미지 URL 없음")
        return {"error": "올바르지 않은 URL 입니다."}
    return {"s3_url": url}

def mod_instruction(state: PipelineState) -> PipelineState:
    """수정 지시사항을 요청"""
    print(f"[분기] mod_instruction 노드 접근")
    question = (
        "이미지 수정을 시작하겠습니다 !\n"
        "어떤 부분을 어떻게 수정할지 간단히 설명해 주세요 (예: 색상 변경, DRL 스타일 변경, 휠 디자인 교체 등)."
    )
    if state["waiting_node"] != "mod_instruction":
        interrupt({"query": question})
        print(f"[처리] 수정 지시사항 입력 요청 메시지 전송")
    else:
        return safe_merge_user_query(state.get("user_query"), response=question)

def store_mod_instruction(state: PipelineState) -> Dict[str, Any]:
    print(f"[분기] store_mod_instruction 노드 접근")
    # user_query에서 받은 사용자 입력을 사용
    desc = (state.get("user_query") or "").strip()
    if desc:
        _append_history(state, "user", desc)
        # Use same generator to build an edit-friendly prompt from the conversation
        image_query = _querygen.generate_image_query(state)
        print(f"[처리] 수정 지시사항 저장 및 쿼리 생성 완료: '{image_query[:50]}...'")
    else:
        print(f"[처리] 수정 지시사항 없음")
        image_query = ""
    
    return {**state, "image_query": image_query}

def run_image_modification(state: PipelineState) -> Dict[str, Any]:
    print(f"[분기] run_image_modification 노드 접근")
    if not state.get("s3_url"):
        print(f"[처리] 오류: s3_url 비어 있습니다.")
        return {"error": "input_image가 비어 있습니다."}
    if not state.get("image_query"):
        print(f"[처리] 오류: image_query가 비어 있습니다.")
        return {"error": "image_query가 비어 있습니다."}
    
    if state["waiting_node"] != "run_image_modification":
        interrupt({"is_loading": True, "generation_type": "image"})
    else:
        print(f"[처리] 이미지 수정 실행 중...")
        out = modify_image(dict(state))
        for k in ["s3_url", "generated_image", "image_generation_status", "response", "error"]:
            if k in out: state[k] = out[k]
        if not state.get("response"):
            msg = state.get("s3_url") or state.get("generated_image") or "이미지 수정 완료"
            response = f"이미지 수정이 완료되었습니다! 🛠️\n\n결과: {msg}"
        print(f"[처리] 이미지 수정 완료")
        return {"response": response}


# -----------------------------
# Finalize
# -----------------------------
def finalize(state: PipelineState) -> Dict[str, Any]:
    print(f"[분기] finalize 노드 접근")
    response = state.get("response", "") or state.get("image_query", "") or "완료되었습니다."
    print(f"[처리] 최종 응답 반환: '{response}...'")
    return {"response": response}
    


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
    
    # RAG branch - 완전한 RAG 처리
    g.add_node("rewrite_query", rewrite_query)
    g.add_node("generate_rag_response", generate_rag_response)
    g.add_node("evaluate_answer", evaluate_answer)
    g.add_node("retry_or_accept", retry_or_accept)
    g.add_node("handle_llm_fallback", handle_llm_fallback)

    # Image generation
    g.add_node("image_mode", image_mode)                         # HITL B
    g.add_node("apply_image_mode", apply_image_mode)
    g.add_node("guided_prepare_question", guided_prepare_question)
    g.add_node("guided_llm_chat", guided_llm_chat)               # HITL C.1 (LLM 대화)
    g.add_node("guided_llm_chat_save", guided_llm_chat_save)
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
    # 3D/4D Generation nodes
    g.add_node("ask_3d_4d_generation", ask_3d_4d_generation)         # HITL G
    g.add_node("select_other_image", select_other_image)             # HITL H
    g.add_node("apply_image_selection", apply_image_selection)
    g.add_node("run_3d_generation", run_3d_generation)
    g.add_node("run_4d_generation", run_4d_generation)
    g.add_node("show_3d_4d_result", show_3d_4d_result)               # HITL I

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
            "rag": "rewrite_query",  # RAG는 rewrite_query부터 시작
            "general_conversation": "handle_general_conversation",
        },
    )

    # RAG branch - 완전한 RAG 처리 플로우
    g.add_edge("rewrite_query", "generate_rag_response")
    g.add_edge("generate_rag_response", "evaluate_answer")
    g.add_edge("evaluate_answer", "retry_or_accept")
    g.add_conditional_edges(
        "retry_or_accept",
        route_retry_ok,
        {
            "handle_llm_fallback": "handle_llm_fallback",
            "finalize": "finalize",
        },
    )
    g.add_edge("handle_llm_fallback", "finalize")

    # General conversation end
    g.add_edge("handle_general_conversation", "finalize")

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
    g.add_edge("guided_prepare_question", "guided_next_category")  # 다음 카테고리로 이동
    g.add_conditional_edges(
        "guided_next_category",
        lambda s: "build_query" if s.get("pipeline_step") == "build_query_from_history" else "llm_chat" if s.get("pipeline_step") == "guided_llm_chat" else "next_category",
        {
            "llm_chat": "guided_llm_chat",  # LLM 대화 시작
            "build_query": "build_query_from_history",  # 쿼리 생성으로 이동
            "next_category": "guided_next_category" # 다음 카테고리로 바로 이동
        },
    )
    g.add_conditional_edges(
        "guided_llm_chat",
        lambda s: "next_category" if s.get("pipeline_step") == "guided_ask_answer" else ("build_query" if s.get("pipeline_step") == "build_query_from_history" else "llm_chat"),
        {
            "llm_chat": "guided_llm_chat_save",  # 계속 LLM 대화
            "next_category": "guided_ask_answer",  # 체크리스트 답변 요청
            "build_query": "build_query_from_history",  # 쿼리 생성으로 이동
        },
    )
    g.add_edge("guided_llm_chat_save", "guided_llm_chat")
    # g.add_conditional_edges(
    #     "guided_ask_answer",
    #     lambda s: "record" if s.get("user_query") and s.get("user_query").strip() else "ask",
    #     {
    #         "ask": "guided_ask_answer",  # 계속 답변 요청
    #         "record": "guided_record",   # 답변 저장 후 기록
    #     },
    # )
    g.add_edge("guided_ask_answer", "guided_record")
    g.add_conditional_edges(
        "guided_record",
        lambda s: "next_category" if s.get("pipeline_step") == "guided_next_category" else ("done" if guided_continue_or_done(s) == "done" else "continue"),
        {
            "next_category": "guided_next_category",  # 바로 다음 카테고리로 이동
            "continue": "guided_next_category",  # 다음 카테고리로 이동
            "done": "build_query_from_history",
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
        lambda s: "modify" if s.get("pipeline_step") == "modify_image" else "3d_4d_ask" if s.get("pipeline_step") in ["run_3d_generation", "run_4d_generation"] else "finish",
        {
            "modify": "mod_intro",
            "3d_4d_ask": "ask_3d_4d_generation",
            "finish": "finalize"
        },
    )
    
    # 지속적인 modification (이미지 수정, 3D 및 4D 생성)
    g.add_edge("run_image_modification", "ask_modify")
    
    # 3D/4D Generation flow
    g.add_conditional_edges(
        "ask_3d_4d_generation",
        route_3d_4d_choice,
        {
            "run_3d_generation": "run_3d_generation",
            "run_4d_generation": "run_4d_generation", 
            "select_other_image": "select_other_image",
            "modify_image": "mod_intro",
            "image_generation": "image_mode"
        },
    )
    
    g.add_edge("select_other_image", "apply_image_selection")
    g.add_conditional_edges(
        "apply_image_selection",
        lambda s: "ask_3d_4d_generation" if "현재" in _norm(s.get("user_query", "")) else "modify_image",
        {
            "ask_3d_4d_generation": "ask_3d_4d_generation",
            "modify_image": "mod_intro"
        },
    )
    
    # 3D/4D 생성 후 결과 표시
    g.add_edge("run_3d_generation", "show_3d_4d_result")
    g.add_edge("run_4d_generation", "show_3d_4d_result")
    
    g.add_conditional_edges(
        "show_3d_4d_result",
        route_3d_4d_result_choice,
        {
            "run_3d_generation": "run_3d_generation",
            "run_4d_generation": "run_4d_generation",
            "modify_image": "mod_intro",
            "image_generation": "image_mode",
            "finish": "finalize"
        },
    )

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
    return g.compile(
        checkpointer=checkpointer,
        )

# 파이프라인 그래프 생성 및 export
all_pipeline = create_text_pipeline()
# pipeline/text_pipeline.py
from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END

from .components.intent_classifier import intent_classifier
from .components.rag_generator import rag_generator
from .components.chat_manager import chat_manager
from .components.image_query_generator import image_query_generator
from .components.image_generator import generate_image
from .components.3d_generator import generate_3d_model
from .components.4d_generator import generate_4d_model
from .components.content_router import content_generation_router, route_content_generation

from .components.query_rewriter import query_rewriter
from .components.answer_evaluator import answer_evaluator
from .components.checklist_generator import checklist_generator

class PipelineState(TypedDict, total=False):
    user_query: str
    intent: str
    chat_history: List[Dict[str, str]]
    response: str
    image_query: str
    is_form_complete: bool
    messages_summarized: bool
    rewritten: bool
    retried: bool
    eval: Dict[str, Any]
    completion_status: Dict[str, Any]

# 1) 의도 분류
def classify_intent(state: PipelineState) -> PipelineState:
    return {**state, "intent": intent_classifier.classify_intent(state["user_query"])}

# 2) HyDE 재작성
def rewrite_query(state: PipelineState) -> PipelineState:
    rq, _ = query_rewriter.hyde_expand_and_rewrite(state["user_query"])
    return {**state, "user_query": rq or state["user_query"], "rewritten": True}

# 3) RAG 응답 생성 (+히스토리 반영)
def generate_rag_response(state: PipelineState) -> PipelineState:
    user_query = state["user_query"]
    chat_history = state.get("chat_history", [])
    response = rag_generator.generate_response(user_query, chat_history)
    updated = chat_manager.add_message(chat_history, "user", user_query)
    updated = chat_manager.add_message(updated, "assistant", response)

    return {**state, "response": response, "chat_history": updated, "messages_summarized": False}

# 4) 답변 자체평가
def evaluate_answer(state: PipelineState) -> PipelineState:
    score = answer_evaluator.analyze(
        user_query=state["user_query"],
        answer=state.get("response", ""),
        context_hint="",
    )
    return {**state, "eval": score}

# 5) 재시도/확정
def retry_or_accept(state: PipelineState) -> PipelineState:
    rel = float(state.get("eval", {}).get("relevance", 0.0))
    ade = float(state.get("eval", {}).get("adequacy", 0.0))
    THRESH = 0.55
    if (rel < THRESH or ade < THRESH) and not state.get("retried"):
        return {**state, "retried": True, "route": "retry"}
    return {**state, "route": "ok"}

# 6) 폼 완성 확인
def check_form_completion(state: PipelineState) -> PipelineState:
    return {**state, "is_form_complete": chat_manager.is_form_complete(state.get("chat_history", []))}

# 7) 이미지 쿼리 생성
def generate_image_query(state: PipelineState) -> PipelineState:
    if not state.get("is_form_complete"):
        return state
    q = image_query_generator.generate_image_query(state.get("chat_history", []))
    resp = f"이미지 생성 쿼리가 완성되었습니다!\n\n{q}\n\n이 쿼리로 Stable Diffusion에서 이미지를 생성할 수 있습니다."
    return {**state, "image_query": q, "response": resp}

# 8) 대화 지속(체크리스트 기반 후속질문)
def continue_conversation(state: PipelineState) -> PipelineState:
    try:
        # 대화 기록에서 폼 데이터 추출
        form_data = checklist_generator.extract_form_data(state.get("chat_history", []))
        
        # 체크리스트 기반 후속 질문 생성
        followup = checklist_generator.generate_follow_up_with_checklist(
            state["user_query"], 
            state.get("response", ""), 
            form_data
        )
        
        # 완성도 상태 추가
        completion_status = checklist_generator.get_completion_status(form_data)
        
    except Exception as e:
        print(f"체크리스트 기반 대화 지속 실패: {e}")
        followup = "네, 계속해서 조건을 알려주세요."
        completion_status = {"completed": 0, "total": 11, "percentage": 0, "is_complete": False}

    updated = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
    updated = chat_manager.add_message(updated, "assistant", followup)
    return {**state, "response": followup, "chat_history": updated, "messages_summarized": False, "completion_status": completion_status}

# 일반 대화 처리
def handle_general_conversation(state: PipelineState) -> PipelineState:
    """일반 대화 처리 (인사, 간단한 질문 등)"""
    try:
        response = chat_manager.generate_general_response(
            state["user_query"], 
            state.get("chat_history", [])
        )
        
        updated = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        updated = chat_manager.add_message(updated, "assistant", response)
        
        return {**state, "response": response, "chat_history": updated, "messages_summarized": False}
        
    except Exception as e:
        print(f"일반 대화 처리 실패: {e}")
        fallback_response = "안녕하세요! 무엇을 도와드릴까요?"
        updated = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        updated = chat_manager.add_message(updated, "assistant", fallback_response)
        return {**state, "response": fallback_response, "chat_history": updated, "messages_summarized": False}

# 라우팅 함수들
def route_by_intent(state: PipelineState) -> str:
    intent = state.get("intent", "rag")
    if intent == "rag":
        return "rewrite_query"
    elif intent == "general":
        return "handle_general_conversation"
    else:
        return "rewrite_query"  # 기본값

def route_retry_ok(state: PipelineState) -> str:
    return "generate_rag_response" if state.get("route") == "retry" else "check_form_completion"


# 그래프 조립
def create_text_pipeline():
    g = StateGraph(PipelineState)

    g.add_node("classify_intent", classify_intent)
    g.add_node("rewrite_query", rewrite_query)
    g.add_node("generate_rag_response", generate_rag_response)
    g.add_node("evaluate_answer", evaluate_answer)
    g.add_node("retry_or_accept", retry_or_accept)
    g.add_node("check_form_completion", check_form_completion)
    g.add_node("generate_image_query", generate_image_query)
    g.add_node("content_router", content_generation_router)
    g.add_node("generate_image", generate_image)
    g.add_node("generate_3d_model", generate_3d_model)
    g.add_node("generate_4d_model", generate_4d_model)
    g.add_node("continue_conversation", continue_conversation)
    g.add_node("handle_general_conversation", handle_general_conversation)

    g.set_entry_point("classify_intent")
    g.add_conditional_edges("classify_intent", route_by_intent, {
        "rewrite_query": "rewrite_query",
        "handle_general_conversation": "handle_general_conversation",
    })
    g.add_edge("rewrite_query", "generate_rag_response")
    g.add_edge("generate_rag_response", "evaluate_answer")
    g.add_edge("evaluate_answer", "retry_or_accept")
    g.add_conditional_edges("retry_or_accept", route_retry_ok, {
        "generate_rag_response": "generate_rag_response",
        "check_form_completion": "check_form_completion",
    })
    g.add_conditional_edges("check_form_completion", lambda state: "generate_image_query" if state.get("is_form_complete") else "continue_conversation", {
        "generate_image_query": "generate_image_query",
        "continue_conversation": "continue_conversation",
    })
    g.add_edge("generate_image_query", END)
    g.add_edge("continue_conversation", END)
    g.add_edge("handle_general_conversation", END)
    return g.compile()

text_pipeline = create_text_pipeline()

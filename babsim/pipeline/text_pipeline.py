# pipeline/text_pipeline.py
from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END

from .components.intent_classifier import intent_classifier
from .components.rag_generator import rag_generator
from .components.chat_manager import chat_manager
from .components.image_query_generator import image_query_generator

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
        # TODO: image_query_generator의 폼 추출 함수를 노출해 실제 form_data로 교체
        form_data = {}
        missing = checklist_generator.missing_fields(form_data)
        followup = checklist_generator.next_question(missing) or "네, 계속해서 조건을 알려주세요."
    except Exception:
        followup = "네, 계속해서 조건을 알려주세요."

    updated = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
    updated = chat_manager.add_message(updated, "assistant", followup)
    return {**state, "response": followup, "chat_history": updated, "messages_summarized": False}

# (이미지 수정 의도는 임시 안내)
def handle_image_modification(state: PipelineState) -> PipelineState:
    msg = "이미지 수정 기능은 현재 개발 중입니다. 텍스트 기반 자동차 디자인 대화를 먼저 진행해보시겠어요?"
    updated = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
    updated = chat_manager.add_message(updated, "assistant", msg)
    return {**state, "response": msg, "chat_history": updated, "messages_summarized": False}

# 라우팅 함수들
def route_by_intent(state: PipelineState) -> str:
    return "rewrite_query" if state.get("intent") != "image_modification" else "handle_image_modification"

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
    g.add_node("continue_conversation", continue_conversation)
    g.add_node("handle_image_modification", handle_image_modification)

    g.set_entry_point("classify_intent")
    g.add_conditional_edges("classify_intent", route_by_intent, {
        "rewrite_query": "rewrite_query",
        "handle_image_modification": "handle_image_modification",
    })
    g.add_edge("rewrite_query", "generate_rag_response")
    g.add_edge("generate_rag_response", "evaluate_answer")
    g.add_edge("evaluate_answer", "retry_or_accept")
    g.add_conditional_edges("retry_or_accept", route_retry_ok, {
        "generate_rag_response": "generate_rag_response",
        "check_form_completion": "check_form_completion",
    })
    g.add_edge("check_form_completion", "generate_image_query")
    g.add_edge("check_form_completion", "continue_conversation")
    g.add_edge("generate_image_query", END)
    g.add_edge("continue_conversation", END)
    g.add_edge("handle_image_modification", END)
    return g.compile()

text_pipeline = create_text_pipeline()

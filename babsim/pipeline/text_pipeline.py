from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END

from .components.intent_classifier import intent_classifier
from .components.rag_generator import rag_generator
from .components.chat_manager import chat_manager
from .components.image_query_generator import image_query_generator
from .components.query_rewriter import query_rewriter
from .components.answer_evaluator import answer_evaluator
from .components.checklist_generator import ChecklistGenerator
from .components.image_generator import generate_image
from .components.image_modifier import modify_image
from .components import generator_3d
from .components import generator_4d


class PipelineState(TypedDict, total=False):
    user_query: str
    initial_intent: str
    image_generation_intent: str
    chat_history: List[Dict[str, str]]
    response: str
    image_query: str
    is_form_complete: bool
    messages_summarized: bool
    rewritten: bool
    retried: bool
    eval: Dict[str, Any]
    completion_status: Dict[str, Any]
    checklist_data: Dict[str, Any]
    pipeline_step: str


checklist_gen = ChecklistGenerator()


# 1) 초기 의도 분류
def classify_initial_intent(state: PipelineState) -> PipelineState:
    return {
        **state,
        "initial_intent": intent_classifier.classify_initial_intent(state["user_query"]),
        "pipeline_step": "classify_initial_intent",
    }


# 2) HyDE 재작성
def rewrite_query(state: PipelineState) -> PipelineState:
    rq, _ = query_rewriter.hyde_expand_and_rewrite(state["user_query"])
    return {
        **state,
        "user_query": rq or state["user_query"],
        "rewritten": True,
        "pipeline_step": "rewrite_query",
    }


# 3) RAG 응답 생성
def generate_rag_response(state: PipelineState) -> PipelineState:
    user_query = state["user_query"]
    chat_history = state.get("chat_history", [])
    response = rag_generator.generate_response(user_query, chat_history)
    chat_history = chat_manager.add_message(chat_history, "user", user_query)
    chat_history = chat_manager.add_message(chat_history, "assistant", response)
    return {
        **state,
        "response": response,
        "chat_history": chat_history,
        "messages_summarized": False,
        "pipeline_step": "generate_rag_response",
    }


# 4) 답변 평가
def evaluate_answer(state: PipelineState) -> PipelineState:
    score = answer_evaluator.analyze(
        user_query=state["user_query"], answer=state.get("response", ""), context_hint=""
    )
    return {**state, "eval": score}


# 5) 품질 평가 라우팅
def retry_or_accept(state: PipelineState) -> PipelineState:
    rel = float(state.get("eval", {}).get("relevance", 0.0))
    ade = float(state.get("eval", {}).get("adequacy", 0.0))
    THRESH = 0.55
    if rel < THRESH or ade < THRESH:
        return {**state, "route": "llm_fallback"}
    return {**state, "route": "ok"}




# 7) 이미지 쿼리 생성
def generate_image_query(state: PipelineState) -> PipelineState:
    if not state.get("is_form_complete"):
        return state
    q = image_query_generator.generate_image_query(state.get("chat_history", []))
    resp = f"이미지 생성 쿼리가 완성되었습니다!\n\n{q}\n\n이제 이미지를 생성하겠습니다..."
    return {**state, "image_query": q, "response": resp}


# 8) 대화 지속
def continue_conversation(state: PipelineState) -> PipelineState:
    try:
        # 현재 체크리스트 데이터 가져오기
        checklist_data = state.get("checklist_data", {})
        
        # 사용자의 최신 답변에서 정보 추출
        form_data = checklist_gen.extract_form_data([state["user_query"]])
        merged_form_data = {**checklist_data, **form_data}
        
        # 완료 상태 확인
        completion_status = checklist_gen.get_completion_status(merged_form_data)
        
        # 아직 완료되지 않았다면 다음 질문 생성
        if not completion_status.get("is_complete", False):
            # 다음에 물어볼 필드 찾기
            next_question = checklist_gen.get_next_question(merged_form_data)
            followup = next_question
        else:
            # 모든 정보가 수집되었다면 완료 메시지
            followup = "모든 정보를 수집했습니다! 이제 이미지를 생성하겠습니다. 🎨"
            
    except Exception as e:
        print(f"체크리스트 기반 대화 지속 실패: {e}")
        followup = "네, 계속해서 조건을 알려주세요."
        completion_status = {
            "completed": 0,
            "total": 11,
            "percentage": 0,
            "is_complete": False,
        }
        merged_form_data = state.get("checklist_data", {})

    chat_history = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
    chat_history = chat_manager.add_message(chat_history, "assistant", followup)

    return {
        **state,
        "response": followup,
        "chat_history": chat_history,
        "messages_summarized": False,
        "completion_status": completion_status,
        "checklist_data": merged_form_data,
        "is_form_complete": completion_status.get("is_complete", False),
    }


# LLM fallback 처리
def handle_llm_fallback(state: PipelineState) -> PipelineState:
    try:
        response = chat_manager.generate_general_response(
            state["user_query"], state.get("chat_history", [])
        )
        chat_history = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        chat_history = chat_manager.add_message(chat_history, "assistant", response)
        return {**state, "response": response, "chat_history": chat_history, "messages_summarized": False}
    except Exception as e:
        print(f"LLM Fallback 응답 생성 실패: {e}")
        fallback_response = "죄송합니다. 현재 답변을 생성할 수 없습니다."
        chat_history = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        chat_history = chat_manager.add_message(chat_history, "assistant", fallback_response)
        return {**state, "response": fallback_response, "chat_history": chat_history, "messages_summarized": False}


# 이미지 수정 처리
def handle_image_modification_request(state: PipelineState) -> PipelineState:
    """
    이미지 수정 요청을 처리하는 함수
    """
    try:
        # 이미지 수정 쿼리 생성
        modification_query = image_query_generator.generate_query(state["user_query"])
        response = f"이미지 수정을 시작합니다! 🎨\n\n수정 요청: {modification_query}\n\n기존 이미지를 기반으로 수정하겠습니다..."
        
        chat_history = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        chat_history = chat_manager.add_message(chat_history, "assistant", response)
        
        return {
            **state,
            "response": response,
            "chat_history": chat_history,
            "messages_summarized": False,
            "image_query": modification_query,
            "is_form_complete": True,
            "pipeline_step": "handle_image_modification_request",
        }
    except Exception as e:
        print(f"이미지 수정 요청 처리 실패: {e}")
        fallback_response = "죄송합니다. 이미지 수정 요청 처리 중 오류가 발생했습니다."
        chat_history = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        chat_history = chat_manager.add_message(chat_history, "assistant", fallback_response)
        return {**state, "response": fallback_response, "chat_history": chat_history, "messages_summarized": False}

# 직접 이미지 생성
def handle_direct_image_generation(state: PipelineState) -> PipelineState:
    try:
        image_query = image_query_generator.generate_query(state["user_query"])
        response = f"이미지 생성을 시작합니다! 🎨\n\n생성 쿼리: {image_query}\n\n이제 이미지를 생성하겠습니다..."
        chat_history = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        chat_history = chat_manager.add_message(chat_history, "assistant", response)
        return {
            **state,
            "response": response,
            "chat_history": chat_history,
            "messages_summarized": False,
            "image_query": image_query,
            "is_form_complete": True,
            "pipeline_step": "handle_direct_image_generation",
        }
    except Exception as e:
        print(f"직접 이미지 생성 실패: {e}")
        fallback_response = "죄송합니다. 이미지 생성 중 오류가 발생했습니다."
        chat_history = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        chat_history = chat_manager.add_message(chat_history, "assistant", fallback_response)
        return {**state, "response": fallback_response, "chat_history": chat_history, "messages_summarized": False}


# 바로 직접 이미지 생성 (기본값)
def handle_image_generation_question(state: PipelineState) -> PipelineState:
    """
    직접 이미지 생성 요청을 처리하는 함수. 이전의 handle_direct_image_generation의 역할을 대체하며,
    이미지 생성의 기본 진입점으로 사용됨.
    """
    try:
        image_query = image_query_generator.generate_query(state["user_query"])
        response = f"이미지 생성을 시작합니다! 🎨\n\n생성 쿼리: {image_query}\n\n이제 이미지를 생성하겠습니다..."
        chat_history = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        chat_history = chat_manager.add_message(chat_history, "assistant", response)
        return {
            **state,
            "response": response,
            "chat_history": chat_history,
            "messages_summarized": False,
            "image_query": image_query,
            "is_form_complete": True,
            "pipeline_step": "handle_image_generation_question",
        }
    except Exception as e:
        print(f"직접 이미지 생성 실패: {e}")
        fallback_response = "죄송합니다. 이미지 생성 중 오류가 발생했습니다."
        chat_history = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        chat_history = chat_manager.add_message(chat_history, "assistant", fallback_response)
        return {**state, "response": fallback_response, "chat_history": chat_history, "messages_summarized": False}


# 가이드형 이미지 생성 시작
def handle_guided_image_generation(state: PipelineState) -> PipelineState:
    try:
        # 체크리스트 데이터 초기화
        checklist_data = {}
        
        # 첫 번째 질문 생성 (시점부터 시작)
        first_question = checklist_gen.get_next_question(checklist_data)
        
        response = f"""이미지 생성을 시작하겠습니다! 🎨

체크리스트 기반으로 단계별로 진행하겠습니다.

{first_question}"""
        
        chat_history = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        chat_history = chat_manager.add_message(chat_history, "assistant", response)
        
        return {
            **state,
            "response": response,
            "chat_history": chat_history,
            "messages_summarized": False,
            "checklist_data": checklist_data,
            "is_form_complete": False,
            "pipeline_step": "handle_guided_image_generation",
        }
    except Exception as e:
        print(f"체크리스트 기반 이미지 생성 처리 실패: {e}")
        fallback_response = "새로운 자동차 디자인을 만들어보겠습니다! 원하는 디자인을 설명해주세요."
        chat_history = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        chat_history = chat_manager.add_message(chat_history, "assistant", fallback_response)
        return {**state, "response": fallback_response, "chat_history": chat_history, "messages_summarized": False}


# 일반 대화 처리
def handle_general_conversation(state: PipelineState) -> PipelineState:
    try:
        response = chat_manager.generate_general_response(
            state["user_query"], state.get("chat_history", [])
        )
        chat_history = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        chat_history = chat_manager.add_message(chat_history, "assistant", response)
        return {**state, "response": response, "chat_history": chat_history, "messages_summarized": False}
    except Exception as e:
        print(f"일반 대화 처리 실패: {e}")
        fallback_response = "안녕하세요! 무엇을 도와드릴까요?"
        chat_history = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        chat_history = chat_manager.add_message(chat_history, "assistant", fallback_response)
        return {**state, "response": fallback_response, "chat_history": chat_history, "messages_summarized": False}


# 라우팅
def route_by_initial_intent(state: PipelineState) -> str:
    intent = state.get("initial_intent")
    user_query_lower = state["user_query"].lower()
    if intent == "rag":
        return "rewrite_query"
    elif intent == "image_generation":
        if "체크리스트" in user_query_lower or "단계별" in user_query_lower:
            return "handle_guided_image_generation"
        else:
            return "handle_image_generation_question"  # 직접 생성으로 바로 연결
    elif intent == "image_modification":
        return "handle_image_modification"
    return "handle_general_conversation"


def route_after_question(state: PipelineState) -> str:
    # 이 함수는 더 이상 handle_image_generation_question 뒤에서 직접 사용되지 않음
    # 하지만 다른 분기 로직에서 재사용될 수 있으므로 유지
    user_query_lower = state["user_query"].lower()
    if "체크리스트" in user_query_lower or "단계별" in user_query_lower:
        return "handle_guided_image_generation"
    elif "바로" in user_query_lower or "직접" in user_query_lower:
        return "handle_direct_image_generation"
    return "handle_guided_image_generation"

def route_retry_ok(state: PipelineState) -> str:
    return "handle_llm_fallback" if state.get("route") == "llm_fallback" else "END"

def route_after_image_generation(state: PipelineState) -> str:
    """
    이미지 생성 후 3D/4D 생성 여부를 결정하는 라우팅 함수
    """
    # 이미지 생성이 완료되었는지 확인
    if state.get("image_generation_status") == "completed":
        # 사용자 요청에 따라 3D/4D 생성 결정
        user_query_lower = state.get("user_query", "").lower()
        
        if "3d" in user_query_lower or "3차원" in user_query_lower:
            return "generate_3d_model"
        elif "4d" in user_query_lower or "4차원" in user_query_lower:
            return "generate_4d_model"
        else:
            # 기본적으로 3D 생성으로 진행
            return "generate_3d_model"
    
    return "END"


# 그래프 조립
def create_text_pipeline():
    g = StateGraph(PipelineState)
    g.add_node("classify_initial_intent", classify_initial_intent)
    g.add_node("rewrite_query", rewrite_query)
    g.add_node("generate_rag_response", generate_rag_response)
    g.add_node("evaluate_answer", evaluate_answer)
    g.add_node("retry_or_accept", retry_or_accept)
    g.add_node("generate_image_query", generate_image_query)
    g.add_node("generate_image", generate_image)
    g.add_node("generate_3d_model", generator_3d.generate_3d_model)
    g.add_node("generate_4d_model", generator_4d.generate_4d_model)
    g.add_node("continue_conversation", continue_conversation)
    g.add_node("handle_general_conversation", handle_general_conversation)
    g.add_node("handle_llm_fallback", handle_llm_fallback)
    g.add_node("handle_direct_image_generation", handle_direct_image_generation)
    g.add_node("handle_guided_image_generation", handle_guided_image_generation)
    g.add_node("handle_image_modification", handle_image_modification_request)
    g.add_node("handle_image_generation_question", handle_image_generation_question)

    g.set_entry_point("classify_initial_intent")
    g.add_conditional_edges("classify_initial_intent", route_by_initial_intent, {
        "rewrite_query": "rewrite_query",
        "handle_guided_image_generation": "handle_guided_image_generation",
        "handle_image_generation_question": "handle_image_generation_question",
        "handle_image_modification": "handle_image_modification",
        "handle_general_conversation": "handle_general_conversation",
    })

    # `handle_image_generation_question`은 이제 직접 `generate_image`로 연결
    g.add_edge("handle_image_generation_question", "generate_image")

    g.add_edge("rewrite_query", "generate_rag_response")
    g.add_edge("generate_rag_response", "evaluate_answer")
    g.add_edge("evaluate_answer", "retry_or_accept")
    g.add_conditional_edges("retry_or_accept", route_retry_ok, {
        "handle_llm_fallback": "handle_llm_fallback",
        "END": END,
    })

    g.add_edge("handle_guided_image_generation","continue_conversation")
    
    # continue_conversation에서 완료 여부에 따라 분기
    g.add_conditional_edges(
        "continue_conversation",
        lambda state: "generate_image_query" if state.get("is_form_complete") else "continue_conversation",
        {"generate_image_query": "generate_image_query", "continue_conversation": "continue_conversation"},
    )

    g.add_edge("generate_image_query", "generate_image")
    g.add_conditional_edges("generate_image", route_after_image_generation, {
        "generate_3d_model": "generate_3d_model",
        "generate_4d_model": "generate_4d_model",
        "END": END,
    })
    g.add_edge("continue_conversation", END)
    g.add_edge("handle_general_conversation", END)
    g.add_edge("handle_llm_fallback", END)
    g.add_edge("handle_direct_image_generation", "generate_image")
    g.add_edge("handle_image_modification", "generate_image")
    g.add_edge("generate_3d_model", END)
    g.add_edge("generate_4d_model", END)

    return g.compile(checkpointer=None, interrupt_before=[], interrupt_after=[], debug=False)


text_pipeline = create_text_pipeline()

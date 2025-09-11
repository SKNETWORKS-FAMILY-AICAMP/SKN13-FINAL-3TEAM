# pipeline/text_pipeline.py
from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END

from .base_state import PipelineState
from .components.intent_classifier import intent_classifier
from .components.rag_generator import rag_generator
from .components.chat_manager import chat_manager
from .components.image_query_generator import image_query_generator
from .components.image_generator import image_generator
from .components.image_modifier import image_modifier
from .components.content_router import content_generation_router, route_content_generation
from .components.generator_3d import generate_3d_model
from .components.generator_4d import generate_4d_model
from .components.query_rewriter import query_rewriter
from .components.answer_evaluator import answer_evaluator
from .components.checklist_generator import checklist_generator
from .llm_provider import generate_vllm_response_text, generate_vllm_response_streaming, test_stream

# 1) 의도 분류
def classify_intent(state: PipelineState) -> PipelineState:
    print("🔍 [분기] classify_intent 실행")
    intent = intent_classifier.classify_intent(state["user_query"])
    print(f"🔍 [분기] classify_intent 결과: {intent}")
    return {**state, "intent": intent}

# 2) HyDE 재작성
def rewrite_query(state: PipelineState) -> PipelineState:
    print("🔍 [분기] rewrite_query 실행")
    rq, _ = query_rewriter.hyde_expand_and_rewrite(state["user_query"])
    print(f"🔍 [분기] rewrite_query 결과: {rq[:100] if rq else 'None'}...")
    return {**state, "user_query": rq or state["user_query"], "rewritten": True}

# 3) RAG 응답 생성 (+히스토리 반영)
def generate_rag_response(state: PipelineState) -> PipelineState:
    print("🔍 [분기] generate_rag_response 실행")
    user_query = state["user_query"]
    chat_history = state.get("chat_history", [])
    
    # RAG 응답 생성 (텍스트)
    response_text = rag_generator.generate_response(user_query, chat_history)
    print(f"🔍 [분기] generate_rag_response 결과: {response_text[:100]}...")
    
    # 스트리밍 응답 생성
    response = generate_vllm_response_streaming(response_text)
    # response = test_stream(response_text)

    # 멀티턴을 위해 대화 기록 업데이트 (스트리밍이므로 임시로 빈 응답으로 기록)
    updated = chat_manager.add_message(chat_history, "user", user_query)
    updated = chat_manager.add_message(updated, "assistant", "[스트리밍 응답]")
    
    return {**state, "response": response, "chat_history": updated, "messages_summarized": False}

# 4) 답변 자체평가
def evaluate_answer(state: PipelineState) -> PipelineState:
    print("🔍 [분기] evaluate_answer 실행")
    score = answer_evaluator.analyze(
        user_query=state["user_query"],
        answer=state.get("response", ""),
        context_hint="",
    )
    print(f"🔍 [분기] evaluate_answer 결과: {score}")
    return {**state, "eval": score}

# 5) 재시도/확정
def retry_or_accept(state: PipelineState) -> PipelineState:
    print("🔍 [분기] retry_or_accept 실행")
    rel = float(state.get("eval", {}).get("relevance", 0.0))
    ade = float(state.get("eval", {}).get("adequacy", 0.0))
    THRESH = 0.55
    print(f"🔍 [분기] retry_or_accept 점수: relevance={rel}, adequacy={ade}, threshold={THRESH}")
    
    if (rel < THRESH or ade < THRESH) and not state.get("retried"):
        print("🔍 [분기] retry_or_accept 결과: retry")
        return {**state, "retried": True, "route": "retry"}
    print("🔍 [분기] retry_or_accept 결과: ok")
    return {**state, "route": "ok"}

# 6) 폼 완성 확인
def check_form_completion(state: PipelineState) -> PipelineState:
    print("🔍 [분기] check_form_completion 실행")
    is_complete = chat_manager.is_form_complete(state.get("chat_history", []))
    print(f"🔍 [분기] check_form_completion 결과: {is_complete}")
    return {**state, "is_form_complete": is_complete}

# 7) 이미지 쿼리 생성
def generate_image_query(state: PipelineState) -> PipelineState:
    """
    ImageQueryGenerator 인스턴스를 사용하여 이미지 쿼리 생성
    """
    print("🔍 [분기] generate_image_query 실행")
    
    # 이미지 쿼리 생성
    image_query = image_query_generator.generate_image_query(state)
    
    print(f"🔍 [분기] generate_image_query 결과: {image_query[:100]}...")
    return {**state, "image_query": image_query}

# 8) 이미지 생성
def generate_image(state: PipelineState) -> PipelineState:
    """
    ImageGenerator 인스턴스를 사용하여 이미지 생성
    """
    print("🔍 [분기] generate_image 실행")
    
    # 이미지 생성
    response, s3_url = image_generator.generate_image(state)
    
    # 멀티턴을 위해 대화 기록 업데이트
    updated = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
    updated = chat_manager.add_message(updated, "assistant", response)
    
    print(f"🔍 [분기] generate_image 결과: {response[:100]}")
    return {**state, "chat_history": updated, "response": response, "s3_url": s3_url}

# 9) 이미지 수정
def modify_image(state: PipelineState) -> PipelineState:
    """
    ImageModifier 인스턴스를 사용하여 이미지 수정
    """
    print("🔍 [분기] modify_image 실행")
    
    # 이미지 수정
    response, s3_url = image_modifier.modify_image(state)
    
    # 멀티턴을 위해 대화 기록 업데이트
    updated = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
    updated = chat_manager.add_message(updated, "assistant", response)
    
    print(f"🔍 [분기] modify_image 결과: {response[:100]}")
    return {**state, "chat_history": updated, "response": response, "s3_url": s3_url}

# 8) 대화 지속(체크리스트 기반 후속질문)
def continue_conversation(state: PipelineState) -> PipelineState:
    print("🔍 [분기] continue_conversation 실행")
    try:
        # 대화 기록에서 폼 데이터 추출
        form_data = checklist_generator.extract_form_data(state.get("chat_history", []))
        print(f"🔍 [분기] continue_conversation 폼 데이터: {form_data}")
        
        # 체크리스트 기반 후속 질문 생성
        followup = checklist_generator.generate_follow_up_with_checklist(
            state["user_query"], 
            state.get("response", ""), 
            form_data
        )
        print(f"🔍 [분기] continue_conversation 후속질문: {followup[:100]}...")
        
        # 완성도 상태 추가
        completion_status = checklist_generator.get_completion_status(form_data)
        print(f"🔍 [분기] continue_conversation 완성도: {completion_status}")
        
    except Exception as e:
        print(f"체크리스트 기반 대화 지속 실패: {e}")
        followup = "네, 계속해서 조건을 알려주세요."
        completion_status = {"completed": 0, "total": 11, "percentage": 0, "is_complete": False}

    # 스트리밍 모드: StreamingHttpResponse 반환
    streaming_response = generate_vllm_response_streaming(followup)
    
    # 멀티턴을 위해 대화 기록 업데이트 (스트리밍이므로 임시로 빈 응답으로 기록)
    updated = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
    updated = chat_manager.add_message(updated, "assistant", "[스트리밍 응답]")
    
    return {**state, "response": streaming_response, "chat_history": updated, "messages_summarized": False, "completion_status": completion_status}

# 일반 대화 처리
def handle_general_conversation(state: PipelineState) -> PipelineState:
    """일반 대화 처리 (인사, 간단한 질문 등)"""
    print("🔍 [분기] handle_general_conversation 실행")
    try:
        response = chat_manager.generate_general_response(
            state["user_query"], 
            state.get("chat_history", [])
        )
        print(f"🔍 [분기] handle_general_conversation 결과: {response[:100]}...")
        
        # 스트리밍 모드: StreamingHttpResponse 반환
        streaming_response = generate_vllm_response_streaming(response)
        print(f"text_pipeline.py 에서 받은 응답 !!! : StreamingHttpResponse 객체")
        # 멀티턴을 위해 대화 기록 업데이트 (스트리밍이므로 임시로 빈 응답으로 기록)
        updated = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        updated = chat_manager.add_message(updated, "assistant", "[스트리밍 응답]")
        
        return {**state, "response": streaming_response, "chat_history": updated, "messages_summarized": False}
        
    except Exception as e:
        print(f"일반 대화 처리 실패: {e}")
        fallback_response = "안녕하세요! 무엇을 도와드릴까요?"
        print(f"🔍 [분기] handle_general_conversation 폴백: {fallback_response}")
        
        # 스트리밍 모드: StreamingHttpResponse 반환
        streaming_response = generate_vllm_response_streaming(fallback_response)
        print(f"text_pipeline.py 에서 받은 응답 !!! : StreamingHttpResponse 객체")

        # 멀티턴을 위해 대화 기록 업데이트 (스트리밍이므로 임시로 빈 응답으로 기록)
        updated = chat_manager.add_message(state.get("chat_history", []), "user", state["user_query"])
        updated = chat_manager.add_message(updated, "assistant", "[스트리밍 응답]")
        
        return {**state, "response": streaming_response, "chat_history": updated, "messages_summarized": False}

# 라우팅 함수들 (임시로 이미지 생성으로 바로 라우팅)
def route_by_intent(state: PipelineState) -> str:
    intent = state.get("intent", "rag")
    print(f"🔍 [라우팅] route_by_intent: intent={intent}")
    # 임시로 모든 경우에 이미지 쿼리 생성으로 라우팅
    print("🔍 [라우팅] route_by_intent 결과: generate_image_query (임시)")
    return "generate_image_query"

def route_retry_ok(state: PipelineState) -> str:
    route = state.get("route")
    result = "generate_rag_response" if route == "retry" else "check_form_completion"
    print(f"🔍 [라우팅] route_retry_ok: route={route}, 결과={result}")
    return result

def route_form_completion(state: PipelineState) -> str:
    is_complete = state.get("is_form_complete", False)
    result = "generate_image_query" if is_complete else "continue_conversation"
    print(f"🔍 [라우팅] route_form_completion: is_complete={is_complete}, 결과={result}")
    return result


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
    g.add_node("modify_image", modify_image)
    g.add_node("generate_3d_model", generate_3d_model)
    g.add_node("generate_4d_model", generate_4d_model)
    g.add_node("continue_conversation", continue_conversation)
    g.add_node("handle_general_conversation", handle_general_conversation)

    g.set_entry_point("handle_general_conversation")
    g.add_edge("handle_general_conversation", END)
    # g.add_edge("classify_intent", "generate_image_query")
    # g.add_edge("generate_image_query", "modify_image")
    # g.add_edge("modify_image", END)

    return g.compile()

text_pipeline = create_text_pipeline()

from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
import operator
from pydantic import BaseModel

# 파이프라인 컴포넌트 import
from .components.intent_classifier import intent_classifier
from .components.rag_generator import rag_generator
from .components.chat_manager import chat_manager
from .components.image_query_generator import image_query_generator

# 파이프라인 상태 정의
class PipelineState(TypedDict):
    user_query: str
    intent: str
    chat_history: List[Dict[str, str]]
    response: str
    image_query: str
    is_form_complete: bool
    messages_summarized: bool  # 요약 완료 여부 추가

# 의도 분류 노드
def classify_intent(state: PipelineState) -> PipelineState:
    """사용자 쿼리의 의도를 분류하는 노드"""
    user_query = state["user_query"]
    intent = intent_classifier.classify_intent(user_query)
    return {**state, "intent": intent}

# RAG 기반 답변 생성 노드 (요약 기능 포함)
def generate_rag_response(state: PipelineState) -> PipelineState:
    """RAG 기반 답변 생성 노드 (요약 기능 포함)"""
    user_query = state["user_query"]
    chat_history = state["chat_history"]

    # 요약 체인 생성
    chain_with_summarization = create_summarization_chain()
    
    # 요약과 함께 RAG 응답 생성
    result = chain_with_summarization.invoke({
        "user_query": user_query,
        "chat_history": chat_history
    })
    
    response = result.get("response", "")
    updated_history = result.get("chat_history", chat_history)
    messages_summarized = result.get("messages_summarized", False)

    return {
        **state, 
        "response": response, 
        "chat_history": updated_history,
        "messages_summarized": messages_summarized
    }

def create_summarization_chain():
    """요약 기능이 포함된 체인 생성"""
    from .models.exaone_llm_model import exaone_llm_model
    
    # 요약 프롬프트 템플릿
    summarization_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that summarizes conversations."),
        ("placeholder", "{chat_history}"),
        ("human", "Distill the above chat messages into a single summary message. Include as many specific details as you can. Answer in Korean."),
    ])
    
    # LangChain 호환 채팅 모델
    class LangChainChatModel:
        def __init__(self, llm_model):
            self.llm_model = llm_model
        
        def invoke(self, messages):
            if isinstance(messages, dict) and 'chat_history' in messages:
                chat_text = self._format_messages(messages['chat_history'])
                prompt = f"다음 대화를 요약해주세요:\n\n{chat_text}\n\n요약:"
            else:
                prompt = str(messages)
            
            response = self.llm_model.generate_response(prompt, max_length=512)
            return AIMessage(content=response)
        
        def _format_messages(self, messages):
            formatted = []
            for msg in messages:
                if hasattr(msg, 'type'):
                    if msg.type == 'human':
                        formatted.append(f"사용자: {msg.content}")
                    elif msg.type == 'ai':
                        formatted.append(f"어시스턴트: {msg.content}")
                else:
                    formatted.append(str(msg))
            return "\n".join(formatted)
    
    chat_model = LangChainChatModel(exaone_llm_model)
    
    # 요약 함수
    def summarize_messages(chain_input):
        stored_messages = chain_input.get("chat_history", [])
        if len(stored_messages) == 0:
            return {"messages_summarized": False, "chat_history": stored_messages}
        
        # 대화 기록을 LangChain 메시지로 변환
        langchain_messages = []
        for msg in stored_messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
        
        # 요약 실행
        summarization_chain = summarization_prompt | chat_model
        summary_result = summarization_chain.invoke({"chat_history": langchain_messages})
        
        # 요약 결과를 새로운 대화 기록으로 교체
        summary_content = summary_result.content if hasattr(summary_result, 'content') else str(summary_result)
        summarized_history = [
            {"role": "assistant", "content": f"이전 대화 요약: {summary_content}"}
        ]
        
        return {
            "messages_summarized": True, 
            "chat_history": summarized_history
        }
    
    # RAG 응답 생성 함수
    def generate_response(chain_input):
        user_query = chain_input.get("user_query", "")
        chat_history = chain_input.get("chat_history", [])
        
        # RAG 응답 생성
        response = rag_generator.generate_response(user_query, chat_history)
        
        # 대화 기록에 추가
        updated_history = chat_manager.add_message(chat_history, "user", user_query)
        updated_history = chat_manager.add_message(updated_history, "assistant", response)
        
        return {
            "response": response,
            "chat_history": updated_history
        }
    
    # RunnablePassthrough를 사용한 체인 구성
    chain_with_summarization = (
        RunnablePassthrough.assign(messages_summarized=summarize_messages)
        | RunnablePassthrough.assign(response=generate_response)
    )
    
    return chain_with_summarization

# 이미지 수정 요청 처리 노드
def handle_image_modification(state: PipelineState) -> PipelineState:
    """이미지 수정 요청 처리 노드"""
    user_query = state["user_query"]
    chat_history = state["chat_history"]
    
    # 이미지 수정 요청에 대한 응답
    response = "이미지 수정 기능은 현재 개발 중입니다. 텍스트 기반 자동차 디자인 대화를 먼저 진행해보시겠어요?"
    
    # 대화 기록에 추가
    updated_history = chat_manager.add_message(chat_history, "user", user_query)
    updated_history = chat_manager.add_message(updated_history, "assistant", response)
    
    return {
        **state, 
        "response": response, 
        "chat_history": updated_history,
        "messages_summarized": False
    }

# 폼 완성 확인 노드
def check_form_completion(state: PipelineState) -> PipelineState:
    """자동차 디자인 폼 완성 여부 확인 노드"""
    chat_history = state["chat_history"]
    is_form_complete = chat_manager.is_form_complete(chat_history)
    return {**state, "is_form_complete": is_form_complete}

# 이미지 쿼리 생성 노드
def generate_image_query(state: PipelineState) -> PipelineState:
    """이미지 생성 쿼리 생성 노드"""
    if not state["is_form_complete"]:
        return state
    
    chat_history = state["chat_history"]
    image_query = image_query_generator.generate_image_query(chat_history)
    
    # 응답에 이미지 쿼리 정보 추가
    response = f"이미지 생성 쿼리가 완성되었습니다!\n\n{image_query}\n\n이 쿼리를 사용하여 Stable Diffusion으로 이미지를 생성할 수 있습니다."
    
    return {**state, "image_query": image_query, "response": response}

# 대화 계속 노드
def continue_conversation(state: PipelineState) -> PipelineState:
    """대화 계속 노드"""
    user_query = state["user_query"]
    chat_history = state["chat_history"]
    
    # 간단한 응답 생성
    response = "네, 계속해서 자동차 디자인에 대해 이야기해보세요. 어떤 부분을 더 자세히 알고 싶으신가요?"
    
    # 대화 기록에 추가
    updated_history = chat_manager.add_message(chat_history, "user", user_query)
    updated_history = chat_manager.add_message(updated_history, "assistant", response)
    
    return {
        **state, 
        "response": response, 
        "chat_history": updated_history,
        "messages_summarized": False
    }

# 라우팅 함수
def route_based_on_intent(state: PipelineState) -> str:
    """의도에 따른 라우팅"""
    intent = state["intent"]
    
    if intent == "text_generation":
        return "generate_rag_response"
    elif intent == "image_modification":
        return "handle_image_modification"
    else:
        return "generate_rag_response"

def route_after_rag(state: PipelineState) -> str:
    """RAG 응답 후 라우팅"""
    if state["is_form_complete"]:
        return "generate_image_query"
    else:
        return "continue_conversation"

# 파이프라인 그래프 생성
def create_text_pipeline():
    """텍스트 파이프라인 생성"""
    workflow = StateGraph(PipelineState)
    
    # 노드 추가
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("generate_rag_response", generate_rag_response)
    workflow.add_node("handle_image_modification", handle_image_modification)
    workflow.add_node("check_form_completion", check_form_completion)
    workflow.add_node("generate_image_query", generate_image_query)
    workflow.add_node("continue_conversation", continue_conversation)
    
    # 시작점 설정
    workflow.set_entry_point("classify_intent")
    
    # 조건부 라우팅 추가
    workflow.add_conditional_edges(
        "classify_intent",
        route_based_on_intent,
        {
            "generate_rag_response": "generate_rag_response",
            "handle_image_modification": "handle_image_modification"
        }
    )
    
    # RAG 응답 후 폼 완성 확인
    workflow.add_edge("generate_rag_response", "check_form_completion")
    workflow.add_edge("handle_image_modification", "check_form_completion")
    
    # 폼 완성 확인 후 라우팅
    workflow.add_conditional_edges(
        "check_form_completion",
        route_after_rag,
        {
            "generate_image_query": "generate_image_query",
            "continue_conversation": "continue_conversation"
        }
    )
    
    # 종료점 설정
    workflow.add_edge("generate_image_query", END)
    workflow.add_edge("continue_conversation", END)
    
    return workflow.compile()

# 전역 파이프라인 인스턴스
text_pipeline = create_text_pipeline()

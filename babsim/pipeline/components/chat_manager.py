from typing import Dict, Any, List, Optional
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from ..config import config
from ..models.exaone_llm_model import exaone_llm_model

class ChatManager:
    """Multi-turn 대화 관리 컴포넌트"""
    
    def __init__(self):
        self.max_history_length = config.MAX_HISTORY_LENGTH
        self.summarization_threshold = config.SUMMARIZATION_THRESHOLD
        self.system_prompt = config.SYSTEM_PROMPT

    def add_message(
        self, chat_history: List[Dict[str, str]], role: str, content: str
    ) -> List[Dict[str, str]]:
        """대화 기록에 메시지 추가"""
        message = {"role": role, "content": content}
        chat_history.append(message)

        # 대화 기록이 너무 길어지면 요약
        if len(chat_history) > self.max_history_length:
            chat_history = self._summarize_history(chat_history)

        return chat_history

    def _summarize_history(
        self, chat_history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """대화 기록 요약 (LangChain 방식)"""
        try:
            # 요약할 메시지들 추출 (시스템 메시지 제외)
            messages_to_summarize = [
                msg for msg in chat_history if msg.get("role") in ["user", "assistant"]
            ]

            if len(messages_to_summarize) < self.summarization_threshold:
                return chat_history

            # LangChain ChatPromptTemplate 사용
            summarization_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant that summarizes conversations."),
                ("placeholder", "{chat_history}"),
                ("human", "Distill the above chat messages into a single summary message. Include as many specific details as you can. Answer in Korean."),
            ])

            # LangChain 체인 생성
            summarization_chain = summarization_prompt | self._get_langchain_chat_model()

            # 대화 기록을 LangChain 메시지 형식으로 변환
            langchain_messages = self._convert_to_langchain_messages(messages_to_summarize)
            
            # 요약 실행
            summary_result = summarization_chain.invoke({"chat_history": langchain_messages})
            
            # 요약 결과 추출
            summary_content = summary_result.content if hasattr(summary_result, 'content') else str(summary_result)

            # 요약된 대화 기록으로 교체
            summarized_history = [
                {"role": "assistant", "content": f"이전 대화 요약: {summary_content}"}
            ]

            return summarized_history

        except Exception as e:
            print(f"대화 기록 요약 실패: {e}")
            # 요약 실패 시 최근 메시지만 유지
            return chat_history[-self.max_history_length // 2 :]

    def _get_langchain_chat_model(self):
        """LangChain 호환 채팅 모델 반환"""
        # LLM 모델을 LangChain 호환 형태로 래핑
        class LangChainChatModel:
            def __init__(self, llm_model):
                self.llm_model = llm_model
            
            def invoke(self, messages):
                # 메시지에서 텍스트 추출
                if isinstance(messages, dict) and 'chat_history' in messages:
                    # 대화 기록이 있는 경우
                    chat_text = self._format_langchain_messages(messages['chat_history'])
                    prompt = f"다음 대화를 요약해주세요:\n\n{chat_text}\n\n요약:"
                else:
                    # 단일 메시지인 경우
                    prompt = str(messages)
                
                # LLM 모델로 응답 생성
                response = self.llm_model.generate_response(prompt, max_length=512)
                return AIMessage(content=response)
            
            def _format_langchain_messages(self, messages):
                """LangChain 메시지를 텍스트로 변환"""
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
        
        return LangChainChatModel(exaone_llm_model)

    def _convert_to_langchain_messages(self, messages: List[Dict[str, str]]):
        """Django 메시지를 LangChain 메시지로 변환"""
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
        
        return langchain_messages

    def _create_summary_prompt(self, messages: List[Dict[str, str]]) -> str:
        """요약 프롬프트 생성 (기존 방식 - 호환성 유지)"""
        conversation_text = self._format_chat_history(messages)

        prompt = f"""
다음 대화를 간결하게 요약해주세요. 중요한 정보와 사용자의 선호사항을 포함해주세요.

대화 내용:
{conversation_text}

요약:
"""
        return prompt

    def _format_chat_history(self, chat_history: List[Dict[str, str]]) -> str:
        """대화 기록을 텍스트로 포맷"""
        formatted_history = []

        for message in chat_history:
            role = message.get("role", "")
            content = message.get("content", "")

            if role == "user":
                formatted_history.append(f"사용자: {content}")
            elif role == "assistant":
                formatted_history.append(f"어시스턴트: {content}")

        return "\n".join(formatted_history)

    def get_formatted_history(self, chat_history: List[Dict[str, str]]) -> str:
        """포맷된 대화 기록 반환"""
        return self._format_chat_history(chat_history)

    def clear_history(self) -> List[Dict[str, str]]:
        """대화 기록 초기화"""
        return []

    def is_form_complete(self, chat_history: List[Dict[str, str]]) -> bool:
        """이미지 생성 폼이 완성되었는지 확인"""
        # 마지막 어시스턴트 메시지에서 폼 완성 여부 확인
        for message in reversed(chat_history):
            if message.get("role") == "assistant":
                content = message.get("content", "")
                if "이미지 생성 쿼리" in content or "폼이 완성" in content:
                    return True
        return False

# 전역 채팅 매니저 인스턴스
chat_manager = ChatManager()

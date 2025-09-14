from typing import Dict, Any, List, Optional
import sys
import os
from pathlib import Path

# 파이프라인 루트 경로를 Python 경로에 추가
PIPELINE_ROOT = Path(__file__).parent.parent
sys.path.append(str(PIPELINE_ROOT))
from ..config import config
from ..llm_provider import kanana_llm_model

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
        """대화 기록 요약 (직접 LLM 호출 방식)"""
        try:
            # 요약할 메시지들 추출 (시스템 메시지 제외)
            messages_to_summarize = [
                msg for msg in chat_history if msg.get("role") in ["user", "assistant"]
            ]

            if len(messages_to_summarize) < self.summarization_threshold:
                return chat_history

            # 대화 기록을 텍스트로 변환
            conversation_text = self._format_chat_history(messages_to_summarize)
            
            # 요약 프롬프트 생성
            summarization_prompt = f"""다음 대화를 간결하게 요약해주세요. 중요한 정보와 사용자의 선호사항을 포함해주세요.

대화 내용:
{conversation_text}

요약:"""

            # LLM으로 직접 요약 실행
            summary_content = kanana_llm_model.generate_vllm_response_streaming(summarization_prompt, max_length=256)

            # 요약된 대화 기록으로 교체
            summarized_history = [
                {"role": "assistant", "content": f"이전 대화 요약: {summary_content}"}
            ]

            return summarized_history

        except Exception as e:
            print(f"대화 기록 요약 실패: {e}")
            # 요약 실패 시 최근 메시지만 유지
            return chat_history[-self.max_history_length // 2 :]


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
    
    def generate_general_response(self, user_query: str, chat_history: List[Dict[str, str]] = None) -> str:
        """일반 대화용 응답 생성"""
        try:
            # 일반 대화용 프롬프트 사용
            general_prompt = config.GENERAL_CONVERSATION_PROMPT
            
            # 대화 기록이 있으면 포함
            if chat_history:
                history_text = self._format_chat_history(chat_history)
                prompt = f"{general_prompt}\n\n대화 기록:\n{history_text}\n\n사용자 질문: {user_query}\n답변:"
            else:
                prompt = f"{general_prompt}\n\n사용자 질문: {user_query}\n답변:"
            
            # Kanana LLM으로 응답 생성
            response = kanana_llm_model.generate_vllm_response_streaming(prompt, max_length=512)
            
            return response
            
        except Exception as e:
            print(f"일반 대화 응답 생성 실패: {e}")
            return "안녕하세요! 무엇을 도와드릴까요?"

# 전역 채팅 매니저 인스턴스
chat_manager = ChatManager()

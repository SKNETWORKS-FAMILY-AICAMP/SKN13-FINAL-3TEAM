import sys
import os
import django
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# babsim Django 프로젝트 설정
BABSIM_ROOT = Path(__file__).parent.parent
sys.path.append(str(BABSIM_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Django 설정 로드
django.setup()

# babsim 모델 import
from JJACKLETTE.models import Users, ChatSession, PromptLog

# 파이프라인 import
from .text_pipeline import text_pipeline
from .components.intent_classifier import intent_classifier
from .components.rag_generator import rag_generator
from .components.chat_manager import chat_manager
from .components.image_query_generator import image_query_generator

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BabsimPipelineService:
    """Babsim Django와 파이프라인을 연결하는 서비스"""
    
    def __init__(self):
        self.chat_manager = chat_manager
        self.rag_generator = rag_generator
        self.intent_classifier = intent_classifier
        self.image_query_generator = image_query_generator
    
    def get_user_by_id(self, user_id: str) -> Optional[Users]:
        """user_id로 사용자 조회"""
        try:
            return Users.objects.get(user_id=user_id)
        except Users.DoesNotExist:
            return None
    
    def create_user(self, email: str, password: str = None) -> Users:
        """새 사용자 생성"""
        if not password:
            password = "default_password_123"  # 실제 환경에서는 안전한 비밀번호 사용
        
        user = Users.objects.create_user(email=email, password=password)
        logger.info(f"새 사용자 생성: {email}")
        return user
    
    def get_or_create_chat_session(self, user: Users) -> ChatSession:
        """사용자의 활성 채팅 세션 조회 또는 생성"""
        # 가장 최근의 활성 세션 조회
        active_session = ChatSession.objects.filter(
            user=user, 
            ended_at__isnull=True
        ).order_by('-started_at').first()
        
        if active_session:
            return active_session
        
        # 새 세션 생성
        new_session = ChatSession.objects.create(user=user)
        logger.info(f"새 채팅 세션 생성: {new_session.session_id}")
        return new_session
    
    def save_prompt_log(self, session: ChatSession, user_prompt: str, ai_response: str) -> PromptLog:
        """프롬프트 로그 저장"""
        prompt_log = PromptLog.objects.create(
            session=session,
            user_prompt=user_prompt,
            ai_response=ai_response
        )
        logger.info(f"프롬프트 로그 저장: {prompt_log.prompt_id}")
        return prompt_log
    
    def save_generated_result(self, prompt_log: PromptLog, result_type: str, result: str) -> PromptLog:
        """생성 결과 저장 (PromptLog 모델에 직접 저장)"""
        prompt_log.result_type = result_type
        prompt_log.result_path = result
        prompt_log.save()
        logger.info(f"생성 결과 저장: {prompt_log.prompt_id}")
        return prompt_log
    
    def get_chat_history_for_pipeline(self, session: ChatSession) -> List[Dict[str, str]]:
        """Django 모델의 대화 기록을 파이프라인용 형식으로 변환"""
        prompt_logs = session.prompt_logs.all().order_by('created_at')
        chat_history = []
        
        for log in prompt_logs:
            if log.user_prompt:
                chat_history.append({
                    'role': 'user',
                    'content': log.user_prompt
                })
            if log.ai_response:
                chat_history.append({
                    'role': 'assistant',
                    'content': log.ai_response
                })
        
        return chat_history
    
    def process_user_message(self, user_id: str, user_query: str) -> Dict[str, Any]:
        """사용자 메시지 처리 및 파이프라인 실행"""
        try:
            # 사용자 조회 또는 생성
            user = self.get_user_by_id(user_id)
            if not user:
                user = self.create_user(user_id)
            
            # 채팅 세션 조회 또는 생성
            session = self.get_or_create_chat_session(user)
            
            # 파이프라인용 대화 기록 준비
            chat_history = self.get_chat_history_for_pipeline(session)
            
            # LangGraph 파이프라인 실행
            initial_state = {
                "user_query": user_query,
                "intent": "",
                "chat_history": chat_history,
                "response": "",
                "image_query": "",
                "is_form_complete": False,
                "messages_summarized": False
            }
            
            pipeline_result = text_pipeline.invoke(initial_state)
            
            # 결과 추출
            response = pipeline_result.get('response', '')
            intent = pipeline_result.get('intent', '')
            is_form_complete = pipeline_result.get('is_form_complete', False)
            image_query = pipeline_result.get('image_query', '')
            updated_history = pipeline_result.get('chat_history', chat_history)
            
            # 결과를 Django 모델에 저장
            prompt_log = self.save_prompt_log(session, user_query, response)
            
            # 이미지 쿼리가 생성된 경우 결과 저장
            if image_query:
                self.save_generated_result(
                    prompt_log, 
                    'image', 
                    image_query
                )
            
            # 응답 데이터 구성
            response_data = {
                'response': response,
                'intent': intent,
                'is_form_complete': is_form_complete,
                'image_query': image_query,
                'session_id': str(session.session_id),
                'prompt_id': str(prompt_log.prompt_id),
                'user_id': user_id
            }
            
            return response_data
            
        except Exception as e:
            logger.error(f"메시지 처리 실패: {e}")
            return {
                'error': str(e),
                'response': '죄송합니다. 처리 중 오류가 발생했습니다.',
                'user_id': user_id
            }
    
    def get_session_history(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자의 채팅 세션 기록 조회"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return []
            
            sessions = user.chat_sessions.all().order_by('-started_at')
            history = []
            
            for session in sessions:
                session_data = {
                    'session_id': str(session.session_id),
                    'started_at': session.started_at.isoformat(),
                    'ended_at': session.ended_at.isoformat() if session.ended_at else None,
                    'prompts': []
                }
                
                for prompt_log in session.prompt_logs.all().order_by('created_at'):
                    session_data['prompts'].append({
                        'prompt_id': str(prompt_log.prompt_id),
                        'user_prompt': prompt_log.user_prompt,
                        'ai_response': prompt_log.ai_response,
                        'created_at': prompt_log.created_at.isoformat()
                    })
                
                history.append(session_data)
            
            return history
            
        except Exception as e:
            logger.error(f"세션 기록 조회 실패: {e}")
            return []
    
    def clear_session(self, user_id: str) -> bool:
        """사용자의 활성 세션 종료"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            active_sessions = user.chat_sessions.filter(ended_at__isnull=True)
            for session in active_sessions:
                session.ended_at = django.utils.timezone.now()
                session.save()
            
            logger.info(f"사용자 {user_id}의 활성 세션 종료")
            return True
            
        except Exception as e:
            logger.error(f"세션 종료 실패: {e}")
            return False

    def process_query(self, user_query: str, user_id: str = "default_user") -> Dict[str, Any]:
        """사용자 쿼리를 파이프라인으로 처리 (새로운 구조)"""
        try:
            logger.info(f"파이프라인 쿼리 처리 시작: {user_query}")
            
            # LangGraph 파이프라인 실행
            initial_state = {
                "user_query": user_query,
                "intent": "",
                "chat_history": [],
                "response": "",
                "image_query": "",
                "is_form_complete": False,
                "messages_summarized": False,
                "rewritten": False,
                "retried": False,
                "eval": {},
                "completion_status": {}
            }
            
            # 파이프라인 실행
            pipeline_result = text_pipeline.invoke(initial_state)
            
            # 결과 추출
            response = pipeline_result.get('response', '')
            intent = pipeline_result.get('intent', '')
            is_form_complete = pipeline_result.get('is_form_complete', False)
            image_query = pipeline_result.get('image_query', '')
            completion_status = pipeline_result.get('completion_status', {})
            
            # 생성된 결과 구성
            generated_results = []
            if image_query:
                generated_results.append({
                    "result_type": "image",
                    "result_path": "/src/assets/prototype_lab/Ionic6.png",
                    "result": image_query
                })
            
            # 결과 반환
            result = {
                "response": response,
                "generated_results": generated_results,
                "intent": intent,
                "user_query": user_query,
                "is_form_complete": is_form_complete,
                "completion_status": completion_status
            }
            
            logger.info(f"파이프라인 처리 완료: {result}")
            return result
            
        except Exception as e:
            logger.error(f"파이프라인 처리 실패: {e}")
            return {
                "response": "죄송합니다. 처리 중 오류가 발생했습니다.",
                "generated_results": [],
                "intent": "error",
                "user_query": user_query,
                "is_form_complete": False,
                "completion_status": {"completed": 0, "total": 11, "percentage": 0, "is_complete": False}
            }


# 전역 서비스 인스턴스
babsim_pipeline_service = BabsimPipelineService()

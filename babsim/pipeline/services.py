import sys
import os
import time
from uuid import UUID, uuid4
import django
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from langgraph.types import Command

# babsim Django 프로젝트 설정
BABSIM_ROOT = Path(__file__).parent.parent
sys.path.append(str(BABSIM_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Django 설정 로드
django.setup()

# babsim 모델 import
from JJACKLETTE.models import Users, ChatSession, PromptLog

# 파이프라인 import
from .text_pipeline_full_v2 import all_pipeline as text_pipeline
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
    
    def create_user(self, user_id: str, password: str = None) -> Users:
        """새 사용자 생성"""
        if not password:
            password = "default_password_123"  # 실제 환경에서는 안전한 비밀번호 사용
        
        # user_id를 email로 사용 (UUID 형식)
        email = f"{user_id}@default.com"
        user = Users.objects.create_user(email=email, password=password, user_id=user_id)
        logger.info(f"새 사용자 생성: {email} (user_id: {user_id})")
        return user
    
    def create_chat_session(self, user_id: str, session_id: uuid4) -> ChatSession:
        """새 채팅 세션 생성"""
        user = self.get_user_by_id(user_id)
        if not user:
            user = self.create_user(user_id)
        
        from django.utils import timezone
        session = ChatSession.objects.create(
            session_id=session_id,
            user=user,
            started_at=timezone.now()
        )
        return session
    
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
    
    def save_prompt_log(self, session: ChatSession, user_prompt: str, ai_response: str, 
                       generation_type: str = None, result_path: str = None) -> PromptLog:
        """프롬프트 로그 저장"""
        # generation_type에 따른 result_type 매핑
        result_type_mapping = {
            'text': 'text',
            'image': 'image', 
            '3D': '3d',
            '4D': '4d'
        }
        
        result_type = result_type_mapping.get(generation_type) if generation_type else None
        
        prompt_log = PromptLog.objects.create(
            session=session,
            user_prompt=user_prompt,
            ai_response=ai_response,
            result_type=result_type,
            result_path=result_path
        )
        logger.info(f"프롬프트 로그 저장: {prompt_log.prompt_id} (type: {result_type}, path: {result_path})")
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
    
    def process_user_message(self, user_id: str, session_id: uuid4, user_query: str) -> Dict[str, Any]:
        """사용자 메시지 처리 및 파이프라인 실행 - 테스트용"""
        try:
            # 사용자 조회 또는 생성
            user = self.get_user_by_id(user_id)
            if not user:
                user = self.create_user(user_id)
            
            # 채팅 세션 조회
            try:
                session = ChatSession.objects.get(session_id=session_id)
            except ChatSession.DoesNotExist:
                # 세션이 없으면 새로 생성
                session = self.create_chat_session(user_id, session_id)
            
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
                "messages_summarized": False,
                "streaming_id": None,  # 스트리밍 ID 초기화
                "is_streaming": False  # 스트리밍 상태 초기화
            }
            
            pipeline_result = text_pipeline.invoke(initial_state)
            
            # 스트리밍 응답인 경우 StreamingHttpResponse를 그대로 반환
            if hasattr(pipeline_result.get('response'), 'streaming_content'):
                print("StreamingHttpResponse 를 받아 넘겨줌!!")
                return {"streaming_response": pipeline_result['response']}
            
            # 결과 추출
            response = pipeline_result.get('response', '')
            intent = pipeline_result.get('intent', '')
            is_form_complete = pipeline_result.get('is_form_complete', False)
            image_query = pipeline_result.get('image_query', '')
            updated_history = pipeline_result.get('chat_history', chat_history)
            
            # 결과를 Django 모델에 저장
            prompt_log = self.save_prompt_log(session, user_query, response)
            
            # generation_type과 S3 URL 추출
            generation_type = pipeline_result.get('generation_type', 'text')
            s3_url = pipeline_result.get('s3_url', '')
            s3_url_3d = pipeline_result.get('s3_url_3d', '')
            s3_url_4d = pipeline_result.get('s3_url_4d', '')
            
            # generation_type에 따른 결과 저장
            if generation_type == 'image' and s3_url:
                self.save_generated_result(prompt_log, 'image', s3_url)
            elif generation_type == '3D' and s3_url_3d:
                self.save_generated_result(prompt_log, '3d', s3_url_3d)
            elif generation_type == '4D' and s3_url_4d:
                self.save_generated_result(prompt_log, '4d', s3_url_4d)
            elif image_query:  # 기존 이미지 쿼리 로직 유지
                self.save_generated_result(prompt_log, 'image', image_query)
            
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
    
    # 대기 중인 HumanNode 키를 추정
    def _guess_waiting_key(self, state: dict) -> str:
        # 파이프라인에서 앞 단계에서 세팅해둘 'waiting_node'가 최우선
        if state.get("waiting_node"):
            return state["waiting_node"]

        # 파이프라인 진행 상태를 보고 추정 (fallback들)
        step = state.get("pipeline_step", "")
        intent = (state.get("initial_intent") or "").strip().lower()

        if step == "guided_asking":
            return "guided_input"
        if step == "await_direct_desc":
            return "direct_freeform"

        # 이미지 수정 브랜치 추정
        if intent == "image_modification":
            if not state.get("input_image"):
                return "mod_image_url"
            if state.get("input_image") and not state.get("image_query"):
                return "mod_instruction"

        # 최상위 웰컴 단계 (기본값)
        return "welcome_pick"


    def process_query(self, user_query: str, user_id: str = "default_user", 
                     checklist_data: Dict[str, Any] = None, session_id: UUID = None,
                     completion_status: Dict[str, Any] = None) -> Dict[str, Any]:
        """사용자 쿼리를 파이프라인으로 처리 (체크리스트 데이터 포함, Django 모델 연동)"""
        import uuid
        process_id = str(uuid.uuid4())[:8]  # 고유 ID 생성
        
        try:
            # logger.info(f"🚀 [PID:{process_id}] 파이프라인 쿼리 처리 시작: {user_query}")
            # logger.info(f"🚀 [PID:{process_id}] 체크리스트 데이터: {checklist_data}")
            # logger.info(f"🚀 [PID:{process_id}] 완성도 상태: {completion_status}")
            print(f"🚀 [PID:{process_id}] process_query 시작 - user_query: '{user_query[:50]}...'")
            
            # 사용자 조회 또는 생성
            user = self.get_user_by_id(user_id)
            if not user:
                user = self.create_user(user_id)
            
            # 채팅 세션 조회 또는 생성
            if session_id:
                try:
                    session = ChatSession.objects.get(session_id=session_id)
                except ChatSession.DoesNotExist:
                    session = self.get_or_create_chat_session(user)
            else:
                session = self.get_or_create_chat_session(user)
            
            # 파이프라인용 대화 기록 준비
            chat_history = self.get_chat_history_for_pipeline(session)
            
            # 파이프라인 실행
            initial_state = {
                "user_query": user_query,
                "chat_history": chat_history,
                "pipeline_step": "start",
                "checklist_data": checklist_data or {},
                "completion_status": completion_status or {},
                "thread_id": session_id,
                "user_id": user_id,
                "streaming_id": None,  # 스트리밍 ID 초기화
                "is_streaming": False,  # 스트리밍 상태 초기화
                "waiting_node": None    # waiting_node 초기화
            }

            config = {
                "configurable": {
                    "thread_id": session_id
                }
            }
            
            print(f"🔍 session_id: {session_id}")
            print(f"🔍 config: {config}")

            # 첫 번째 실행인지 재실행인지 구분
            # LangGraph 체크포인터를 사용해서 이전에 interrupt가 발생했는지 확인
            try:
                # 체크포인터에서 현재 상태 확인
                current_state = text_pipeline.get_state(config) # waiting_node 가 저장되지 않음 -> 초기화 조건 추가
                # 이전에 interrupt가 발생했고, 사용자 입력이 있는 경우만 재실행
                # waiting_node는 체크포인터에 저장되지 않으므로 current_state.next만 확인
                is_resume = (current_state.next is not None and 
                        #    current_state.values.get("waiting_node") is not None and
                           user_query.strip() != "")
                print(f"🔍 체크포인터 상태 확인 - is_resume: {is_resume}")
                print(f"🔍 current_state.next: {current_state.next}")
                print(f"🔍 current_state.values: {current_state.values}")
                print(f"🔍 waiting_node in values: {current_state.values.get('waiting_node')}")
                print(f"🔍 user_query: '{user_query}'")
            except Exception as e:
                print(f"🔍 체크포인터 상태 확인 실패: {e}")
                is_resume = False
       
            if is_resume:
             # 직전 세션 상태(또는 이번 요청으로 만든 initial_state)로부터 대기 키 추정
                print(f"🔍 파이프라인 재실행: ")
                print(f"🔍 user_query 전달: '{user_query}'")
                # waiting_key = self._guess_waiting_key(initial_state)
                # print(f"🔍 waiting_key: {waiting_key}")
                # Command(resume=...)을 사용할 때는 현재 상태에 데이터를 추가
                print(f"🔍 checklist_data 값 확인: {checklist_data}")
                print(f"🔍 completion_status 값 확인: {completion_status}")
                resume_data = {
                    "user_query": user_query,
                    "user_id": user_id,
                    "streaming_id": None,  # 스트리밍 ID 초기화
                    "is_streaming": False,  # 스트리밍 상태 초기화
                    "waiting_node": current_state.next[0],
                    "response": current_state.values.get("response"),
                    "current_field_conversation": current_state.values.get("current_field_conversation", ""),
                }
                # print(f"🔍 resume_data: {resume_data}")
                # print(f"🔍 user_id 타입: {type(user_id)} = {user_id}")
                # print(f"🔍 user_query 타입: {type(user_query)} = {user_query}")
                # Command 객체 생성 시 올바른 구조 사용
                text_pipeline.update_state(config, resume_data)
                command = Command(resume=current_state)
                # print(f"🔍 command: {command}")
                # print(f"🔍 command.resume: {command.resume}")
                pipeline_result = text_pipeline.invoke(None, config=config, command=command)
            else:
                print(f"🔍 파이프라인 첫 실행: {initial_state}")
                pipeline_result = text_pipeline.invoke(initial_state, config=config)

                
            # 결과 추출 (interrupt 처리 포함)
            print(f"🔍 파이프라인 결과: {pipeline_result}")
            
            # interrupt가 발생한 경우 처리
            interrupt_data = {}
            if '__interrupt__' in pipeline_result:
                print(f"🔍 Interrupt 발생: {pipeline_result['__interrupt__']}")
                # interrupt에서 마지막 메시지 추출
                interrupt_data = pipeline_result['__interrupt__'][-1].value
                response = interrupt_data.get('query', '')
                is_loading = interrupt_data.get('is_loading', False)
                generation_type = interrupt_data.get('generation_type', '')

                if interrupt_data.get('is_streaming', False):
                    streaming_id = interrupt_data.get('streaming_id', '')
                    is_streaming = interrupt_data.get('is_streaming', False)
                else:
                    streaming_id = ''
                    is_streaming = False
                print(f"🔍 Interrupt 응답: {response[:50]}")
            else:
                response = pipeline_result.get('response', '')
            
            initial_intent = pipeline_result.get('initial_intent', '')
            image_generation_intent = pipeline_result.get('image_generation_intent', '')
            is_form_complete = pipeline_result.get('is_form_complete', False)
            image_query = pipeline_result.get('image_query', '')
            updated_completion_status = interrupt_data.get('completion_status', pipeline_result.get('completion_status', {}))
            updated_checklist_data = interrupt_data.get('checklist_data', pipeline_result.get('checklist_data', {}))
            
            # 디버깅 로그 추가
            # print(f"[services.py] [DEBUG] image_query: {image_query}")
            # print(f"[services.py] [DEBUG] updated_completion_status: {updated_completion_status}")
            print(f"[services.py] [DEBUG] updated_checklist_data: {updated_checklist_data}")
            # print(f"[services.py] [DEBUG] pipeline_result keys: {list(pipeline_result.keys())}")
            # print(f"[services.py] [DEBUG] interrupt_data keys: {list(interrupt_data.keys())}")
            updated_history = pipeline_result.get('chat_history', chat_history)

            
            # 결과를 Django 모델에 저장
            prompt_log = self.save_prompt_log(session, user_query, response)
            
            # generation_type과 S3 URL 추출
            generation_type = pipeline_result.get('generation_type', 'text')
            s3_url = pipeline_result.get('s3_url', '')
            s3_url_3d = pipeline_result.get('s3_url_3d', '')
            s3_url_4d = pipeline_result.get('s3_url_4d', '')
            
            # 생성된 결과 구성
            generated_results = []
            
            # 임시 로딩창
            if is_loading:
                # interrupt_data에서 generation_type 가져오기
                generation_type = interrupt_data.get('generation_type', 'text')
                if generation_type == 'image':
                    generated_results.append({
                        "result_type": "image",
                        "result_path": "",
                    })
                elif generation_type == "3D":
                    generated_results.append({
                        "result_type": "3d",
                        "result_path": "",
                    })
                elif generation_type == "4D":
                    generated_results.append({
                        "result_type": "4d",
                        "result_path": "",
                    })
                elif generation_type == "text":
                    generated_results.append({
                        "result_type": "text",
                        "result_path": "",
                    })
                
                # 로딩 메시지 반환 후 자동으로 파이프라인 재실행
                result = {
                    "response": "",
                    "generated_results": generated_results,
                    "initial_intent": initial_intent,
                    "image_generation_intent": image_generation_intent,
                    "user_query": user_query,
                    "user_message": user_query,
                    "is_form_complete": is_form_complete,
                    "completion_status": updated_completion_status,
                    "checklist_data": updated_checklist_data,
                    "session_id": session_id,
                    "prompt_id": str(prompt_log.prompt_id),
                    "user_id": user_id,
                    "is_streaming": False,
                    "is_loading": True,
                    "generation_type": generation_type,
                    "auto_retry": True  # 자동 재시도 플래그
                }
                
                print(f"🔄 로딩 메시지 반환 후 자동 재시도 예정: {generation_type}")
                return result
            # generation_type에 따른 결과 저장
            if generation_type == 'image' and s3_url:
                generated_results.append({
                    "result_type": "image",
                    "result_path": s3_url,
                    # "result": image_query
                })
                self.save_generated_result(prompt_log, 'image', s3_url)
            elif generation_type == '3D' and s3_url_3d:
                generated_results.append({
                    "result_type": "3d",
                    "result_path": s3_url_3d,
                    # "result": response
                })
                self.save_generated_result(prompt_log, '3d', s3_url_3d)
            elif generation_type == '4D' and s3_url_4d:
                generated_results.append({
                    "result_type": "4d",
                    "result_path": s3_url_4d,
                    # "result": response
                })
                self.save_generated_result(prompt_log, '4d', s3_url_4d)
            
            # 스트리밍 응답 처리
            streaming_response = None  # 초기화
            if is_streaming and streaming_id != None:
                # 전역 변수에서 StreamingHttpResponse 가져오기
                from .text_pipeline_full_v2 import _streaming_responses
                # print(f"🔍 스트리밍 디버깅:")
                # print(f"  - streaming_id: {streaming_id}")
                # print(f"  - _streaming_responses 키들: {list(_streaming_responses.keys())}")
                # print(f"  - streaming_id가 존재하는가: {streaming_id in _streaming_responses}")
                
                if streaming_id in _streaming_responses:
                    streaming_response = _streaming_responses[streaming_id]
                    # print(f"  - streaming_response 타입: {type(streaming_response)}")
                    # print(f"  - streaming_response 값: {streaming_response}")
                else:
                    print(f"  - ❌ streaming_id '{streaming_id}'를 _streaming_responses에서 찾을 수 없음!")
                    # print(f"  - 사용 가능한 키들: {list(_streaming_responses.keys())}")
            
            # 결과 반환
            result = {
                "response": response,
                "generated_results": generated_results,
                "initial_intent": initial_intent,
                "image_generation_intent": image_generation_intent,
                "user_query": user_query,
                "user_message": user_query,  # HTTP 헤더용 (user_query와 동일)
                "is_form_complete": is_form_complete,
                "completion_status": updated_completion_status,
                "checklist_data": updated_checklist_data,
                "session_id": session_id,
                "prompt_id": str(prompt_log.prompt_id),
                "user_id": user_id,
                "is_streaming": is_streaming
            }

            # print(f"[services.py] [DEBUG] 반환되는 result : {result}")
            
            # 스트리밍 응답인 경우 streaming_response 키 추가
            if is_streaming:
                print(f"streaming_response : {streaming_response}")
                result["streaming_response"] = streaming_response
            
            logger.info(f"파이프라인 처리 완료: {result}")
            return result
            
        except Exception as e:
            logger.error(f"파이프라인 처리 실패: {e}")
            return {
                "response": "죄송합니다. 처리 중 오류가 발생했습니다.",
                "generated_results": [],
                "initial_intent": "error",
                "user_query": user_query,
                "is_form_complete": False,
                "completion_status": {"completed": 0, "total": 11, "percentage": 0, "is_complete": False},
                "checklist_data": {},
                "session_id": None,
                "prompt_id": None,
                "user_id": user_id
            }

    def update_chat_history(self, user_id: str, session_id: uuid4, user_message: str, assistant_response: str) -> bool:
        """스트리밍 완료 후 대화 기록 업데이트"""
        try:
            logger.info(f"대화 기록 업데이트: user_id={user_id}, session_id={session_id}")
            
            # 채팅 세션 조회
            session = ChatSession.objects.filter(session_id=session_id).first()
            if not session:
                logger.error(f"세션을 찾을 수 없음: {session_id}")
                return False
            
            # 사용자 조회
            user = self.get_user_by_id(user_id)
            if not user:
                logger.error(f"사용자를 찾을 수 없음: {user_id}")
                return False
            
            # 대화 기록 업데이트 (기존 임시 기록을 실제 응답으로 교체)
            # 현재 대화 기록 가져오기
            current_history = self.get_chat_history_for_pipeline(session)
            
            # 마지막 assistant 메시지가 "[스트리밍 응답]"인 경우 실제 응답으로 교체
            if current_history and current_history[-1].get('role') == 'assistant' and current_history[-1].get('content') == '[스트리밍 응답]':
                current_history[-1]['content'] = assistant_response
            else:
                # 새로운 대화 기록 추가
                current_history = self.chat_manager.add_message(current_history, "user", user_message)
                current_history = self.chat_manager.add_message(current_history, "assistant", assistant_response)
            
            # Django 모델에 저장
            self.save_prompt_log(session, user_message, assistant_response)
            
            logger.info("대화 기록 업데이트 완료")
            return True
            
        except Exception as e:
            logger.error(f"대화 기록 업데이트 실패: {e}")
            return False

    def generate_image_query_from_checklist(self, checklist_data: dict) -> str:
        """체크리스트 데이터를 기반으로 이미지 쿼리 생성"""
        try:
            print(f"🔍 [분기] 체크리스트 기반 이미지 쿼리 생성 시작")
            
            # image_query_generator 인스턴스 사용
            from .components.image_query_generator import image_query_generator
            
            return image_query_generator.generate_image_query_from_checklist(checklist_data)
            
        except Exception as e:
            print(f"❌ 체크리스트 이미지 쿼리 생성 실패: {e}")
            return "car design based on checklist"

    def generate_image_from_checklist(self, checklist_data: dict, image_query: str, 
                                    session_id: str = None, user_id: str = 'anonymous_user') -> dict:
        """체크리스트 기반 이미지 생성"""
        try:
            print(f"🔍 [분기] 체크리스트 기반 이미지 생성 시작")
            
            # 먼저 로딩 상태 반환
            loading_result = {
                "generated_results": [{
                    "result_type": "image",
                    "result_path": "",
                    "result_id": f"loading_{int(time.time())}"
                }],
                "is_loading": True,
                "generation_type": "image"
            }
            
            # 실제 이미지 생성
            from .components.image_generator import image_generator
            
            # 이미지 생성 실행
            generation_result = image_generator.generate_image(
                image_query,
                session_id=session_id,
                user_id=user_id
            )
            
            if generation_result and generation_result.get('s3_url'):
                # 성공적으로 생성된 경우
                final_result = {
                    "generated_results": [{
                        "result_type": "image",
                        "result_path": generation_result['s3_url'],
                        "result_id": f"checklist_{int(time.time())}",
                        "result": generation_result.get('description', '')
                    }],
                    "is_loading": False,
                    "generation_type": "image",
                    "s3_url": generation_result['s3_url']
                }
                
                print(f"✅ 체크리스트 이미지 생성 완료: {generation_result['s3_url']}")
                return final_result
            else:
                # 생성 실패
                print(f"❌ 체크리스트 이미지 생성 실패")
                return {
                    "generated_results": [],
                    "is_loading": False,
                    "generation_type": "image",
                    "error": "이미지 생성에 실패했습니다."
                }
                
        except Exception as e:
            print(f"❌ 체크리스트 이미지 생성 중 오류: {e}")
            import traceback
            print(f"❌ 스택 트레이스: {traceback.format_exc()}")
            return {
                "generated_results": [],
                "is_loading": False,
                "generation_type": "image",
                "error": f"이미지 생성 중 오류가 발생했습니다: {str(e)}"
            }


# 전역 서비스 인스턴스
babsim_pipeline_service = BabsimPipelineService()

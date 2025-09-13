from typing import Dict, Any, List
from qdrant_client import QdrantClient
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 파이프라인 루트 경로를 Python 경로에 추가
PIPELINE_ROOT = Path(__file__).parent.parent
sys.path.append(str(PIPELINE_ROOT))

from ..config import config
from ..llm_provider import kanana_llm_model

class RAGGenerator:
    """RAG 기반 답변 생성 컴포넌트 (babsim Vector DB 사용)"""
    
    def __init__(self):
        self.system_prompt = config.SYSTEM_PROMPT
        self.qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
        self.collection_name = config.QDRANT_COLLECTION_NAME
        self.embedding_model = None  # 지연 로딩
    
    def generate_response(self, user_query: str, chat_history: List[Dict[str, str]] = None) -> str:
        """RAG를 사용하여 답변 생성"""
        try:
            # babsim Vector DB에서 관련 문서 검색
            relevant_docs = self._search_vector_db(user_query)
            
            if not relevant_docs:
                # RAG 실패 시 Kanana LLM 직접 응답
                return self._fallback_llm_response(user_query, chat_history)
            
            # 컨텍스트 구성
            context = self._build_context(relevant_docs)
            
            # 프롬프트 구성
            prompt = self._build_prompt(user_query, context, chat_history)
            
            # LLM을 사용하여 답변 생성
            response = kanana_llm_model.generate_vllm_response_streaming(prompt, max_length=1024)
            
            # Multi-turn 대화를 위한 후속 질문 추가
            follow_up_question = self._generate_follow_up_question(user_query, response)
            
            return f"{response}\n\n{follow_up_question}"
        
        except Exception as e:
            print(f"RAG 답변 생성 실패: {e}")
            # RAG 실패 시 Kanana LLM 직접 응답
            return self._fallback_llm_response(user_query, chat_history)
    
    def _search_vector_db(self, query: str, k: int = None) -> List[Dict[str, Any]]:
        """babsim Vector DB에서 검색"""
        try:
            # k 값이 없으면 설정에서 가져오기
            if k is None:
                k = config.RAG_TOP_K
            
            # RunPod BAAI/bge-m3 API를 사용하여 쿼리 임베딩 생성
            query_vector = self._embed_query_via_api(query)
            
            # 검색 실행 (더 많은 문서 검색)
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=config.RAG_FETCH_K,  # 더 넓은 검색
                with_payload=True,
                score_threshold=config.RAG_SCORE_THRESHOLD  # 유사도 임계값
            )
            
            # 결과 변환 및 상위 k개만 선택
            results = []
            for result in search_result:
                results.append({
                    'content': result.payload.get('page_content', ''),
                    'metadata': {k: v for k, v in result.payload.items() if k != 'page_content'},
                    'score': result.score
                })
            
            # 상위 k개만 반환
            return results[:k]
            
        except Exception as e:
            print(f"Vector DB 검색 실패: {e}")
            return []
    
    def _embed_query_via_api(self, query: str) -> List[float]:
        """RunPod BAAI/bge-m3 API를 사용하여 쿼리 임베딩 생성"""
        import os
        import requests
        
        # RunPod API 설정
        embedding_endpoint_id = os.getenv("EMBEDDING_ENDPOINT_ID")
        runpod_api_key = os.getenv("RUNPOD_API_KEY")
        
        if not embedding_endpoint_id or not runpod_api_key:
            raise Exception("EMBEDDING_ENDPOINT_ID 또는 RUNPOD_API_KEY가 설정되지 않았습니다.")
        
        # RunPod API 호출
        url = f"https://api.runpod.ai/v2/{embedding_endpoint_id}/runsync"
        headers = {
            "Authorization": f"Bearer {runpod_api_key}",
            "Content-Type": "application/json"
        }
        
        # RunPod 임베딩 API 요청 형식 수정
        data = {
            "input": {
                "model": "BAAI/bge-m3",
                "input": [query]

            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            print(f"RunPod 임베딩 API 응답: {result}")  # 디버깅용 로그
            
            if result.get("status") == "COMPLETED":
                output = result.get("output", {})
                # 오류 응답 확인
                if "code" in output and output["code"] != 200:
                    print(f"RunPod API 오류 응답: {output}")
                    raise Exception(f"RunPod API 오류: {output.get('message', 'Unknown error')}")
                
                if "embeddings" in output:
                    embeddings = output["embeddings"]
                    return embeddings[0]  # 첫 번째 (유일한) 임베딩 반환
                else:
                    print(f"RunPod API 응답에 'embeddings' 키가 없음: {output}")
                    raise Exception(f"RunPod API 응답에 'embeddings' 키가 없음: {output}")
            else:
                print(f"RunPod API 상태 오류: {result}")
                raise Exception(f"RunPod API 상태 오류: {result.get('status', 'Unknown status')}")
                
        except Exception as e:
            print(f"RunPod 임베딩 API 호출 실패: {e}")
            # 폴백: 로컬 모델 사용
            print("RunPod API 실패, 로컬 임베딩 모델로 폴백")
            if self.embedding_model is None:
                try:
                    from langchain_community.embeddings import HuggingFaceBgeEmbeddings
                    self.embedding_model = HuggingFaceBgeEmbeddings(
                        model_name="BAAI/bge-m3",
                        model_kwargs={'device': 'cpu'},
                        encode_kwargs={'normalize_embeddings': True}
                    )
                    print("로컬 BAAI/bge-m3 임베딩 모델 로드 성공")
                except Exception as e:
                    print(f"로컬 BAAI/bge-m3 임베딩 모델 로드 실패: {e}")
                    # 최종 폴백: 더미 임베딩 반환
                    print("더미 임베딩 반환")
                    return [0.0] * 1024  # bge-m3의 기본 차원
            
            try:
                return self.embedding_model.embed_query(query)
            except Exception as e:
                print(f"로컬 임베딩 모델 쿼리 실패: {e}")
                # 최종 폴백: 더미 임베딩 반환
                return [0.0] * 1024
    
    def _build_context(self, relevant_docs: List[Dict[str, Any]]) -> str:
        """관련 문서들을 컨텍스트로 구성"""
        context_parts = []
        
        for i, doc in enumerate(relevant_docs, 1):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            
            context_part = f"문서 {i}:\n{content}"
            if metadata:
                context_part += f"\n메타데이터: {metadata}"
            
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
    def _build_prompt(self, user_query: str, context: str, chat_history: List[Dict[str, str]] = None) -> str:
        """프롬프트 구성"""
        prompt_parts = [self.system_prompt]
        
        # 대화 기록 추가
        if chat_history:
            history_text = self._format_chat_history(chat_history)
            prompt_parts.append(f"대화 기록:\n{history_text}")
        
        # 컨텍스트 추가
        prompt_parts.append(f"참고 정보:\n{context}")
        
        # 사용자 질문 추가
        prompt_parts.append(f"사용자 질문: {user_query}")
        prompt_parts.append("답변:")
        
        return "\n\n".join(prompt_parts)
    
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
    
    def _generate_follow_up_question(self, user_query: str, response: str) -> str:
        """후속 질문 생성"""
        follow_up_prompt = f"""
다음 대화에서 사용자가 추가로 물어볼 만한 질문을 하나 생성해주세요.

사용자 질문: {user_query}
어시스턴트 답변: {response}

후속 질문 (한 문장으로 간단하게):
"""
        
        try:
            follow_up = kanana_llm_model.generate_vllm_response_streaming(follow_up_prompt, max_length=100)
            return f"추가 질문이 있으시면 언제든 말씀해 주세요. 예를 들어: {follow_up.strip()}"
        except:
            return "추가 질문이 있으시면 언제든 말씀해 주세요."
    
    def _fallback_llm_response(self, user_query: str, chat_history: List[Dict[str, str]] = None) -> str:
        """RAG 실패 시 Kanana LLM 직접 응답"""
        try:
            # 대화 기록이 있으면 포함
            if chat_history:
                history_text = self._format_chat_history(chat_history)
                prompt = f"{self.system_prompt}\n\n대화 기록:\n{history_text}\n\n사용자 질문: {user_query}\n답변:"
            else:
                prompt = f"{self.system_prompt}\n\n사용자 질문: {user_query}\n답변:"
            
            # Kanana LLM 직접 응답
            response = kanana_llm_model.generate_vllm_response_streaming(prompt, max_length=1024)
            
            # 후속 질문 추가
            follow_up_question = self._generate_follow_up_question(user_query, response)
            
            return f"{response}\n\n{follow_up_question}"
            
        except Exception as e:
            print(f"Fallback LLM 응답 실패: {e}")
            return "죄송합니다. 현재 답변을 생성할 수 없습니다. 다시 시도해 주세요."


# 전역 RAG 생성기 인스턴스
rag_generator = RAGGenerator()

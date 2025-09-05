from typing import Dict, Any, List
from qdrant_client import QdrantClient
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from config import config
# from ..llm_provider import kanana_llm_model

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
                return "죄송합니다. 관련된 정보를 찾을 수 없습니다."
            
            # 컨텍스트 구성
            context = self._build_context(relevant_docs)
            
            # 프롬프트 구성
            prompt = self._build_prompt(user_query, context, chat_history)
            
            # LLM을 사용하여 답변 생성
            response = kanana_llm_model.generate_response(prompt, max_length=1024)
            
            # Multi-turn 대화를 위한 후속 질문 추가
            follow_up_question = self._generate_follow_up_question(user_query, response)
            
            return f"{response}\n\n{follow_up_question}"
        
        except Exception as e:
            print(f"RAG 답변 생성 실패: {e}")
            return "죄송합니다. 답변을 생성하는 중 오류가 발생했습니다."
    
    def _search_vector_db(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """babsim Vector DB에서 검색"""
        try:
            # 지연 로딩으로 embedding 모델 초기화 (safetensors 사용)
            if self.embedding_model is None:
                self.embedding_model = HuggingFaceBgeEmbeddings(
                    model_name=config.EMBEDDING_MODEL,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
            
            # 쿼리 임베딩 생성
            query_vector = self.embedding_model.embed_query(query)
            
            # 검색 실행
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=k,
                with_payload=True
            )
            
            # 결과 변환
            results = []
            for result in search_result:
                results.append({
                    'content': result.payload.get('page_content', ''),
                    'metadata': {k: v for k, v in result.payload.items() if k != 'page_content'},
                    'score': result.score
                })
            
            return results
            
        except Exception as e:
            print(f"Vector DB 검색 실패: {e}")
            return []
    
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
            follow_up = kanana_llm_model.generate_response(follow_up_prompt, max_length=100)
            return f"추가 질문이 있으시면 언제든 말씀해 주세요. 예를 들어: {follow_up.strip()}"
        except:
            return "추가 질문이 있으시면 언제든 말씀해 주세요."

# 전역 RAG 생성기 인스턴스
rag_generator = RAGGenerator()

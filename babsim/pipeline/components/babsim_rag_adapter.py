from typing import Dict, Any, List
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class BabsimRAGAdapter:
    """Babsim Vector DB를 현재 파이프라인 RAG와 연결하는 어댑터"""
    
    def __init__(self):
        self.qdrant_client = QdrantClient(host="localhost", port=6333)
        self.collection_name = "babsim_rag_db"
        self.embedding_model = None  # 지연 로딩
    
    def search_relevant_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """babsim Vector DB에서 관련 문서 검색"""
        try:
            # 지연 로딩
            if self.embedding_model is None:
                self.embedding_model = SentenceTransformer('BAAI/bge-m3')
            # 쿼리 임베딩 생성
            query_vector = self.embedding_model.encode(query).tolist()
            
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
            
            logger.info(f"babsim Vector DB에서 {len(results)}개 문서 검색 완료")
            return results
            
        except Exception as e:
            logger.error(f"babsim Vector DB 검색 실패: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """컬렉션 정보 조회"""
        try:
            info = self.qdrant_client.get_collection(self.collection_name)
            count = self.qdrant_client.count(self.collection_name, exact=True)
            
            return {
                'collection_name': self.collection_name,
                'vector_size': info.config.params.vectors.size,
                'distance': str(info.config.params.vectors.distance),
                'total_points': count.count,
                'status': 'connected'
            }
        except Exception as e:
            logger.error(f"컬렉션 정보 조회 실패: {e}")
            return {
                'collection_name': self.collection_name,
                'status': 'disconnected',
                'error': str(e)
            }


# 전역 어댑터 인스턴스
babsim_rag_adapter = BabsimRAGAdapter()

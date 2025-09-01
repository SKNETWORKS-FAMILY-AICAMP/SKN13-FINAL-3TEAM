import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Config:
    """파이프라인 설정 클래스"""
    
    # 모델 설정 (Kanana 모델 사용)
    LLM_MODEL = "kanana-1.5-8b-instruct-2505"  # Kanana 모델 사용
    EMBEDDING_MODEL = "BAAI/bge-m3" 
    
    # Vector DB 설정 (JJACKLETTE와 동일)
    QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT_REST", "6333"))
    QDRANT_COLLECTION_NAME = "babsim_rag_db"  # babsim의 컬렉션명 사용
    
    # RAG 설정
    MMR_K = 5  # 최종 결과 문서 개수
    MMR_FETCH_K = 20  # 처음 검색할 문서 개수
    MMR_LAMBDA = 0.5  # MMR 다양성 파라미터
    
    # 대화 설정
    MAX_HISTORY_LENGTH = 10  # 대화 기록 최대 길이
    SUMMARIZATION_THRESHOLD = 5  # 요약 시작 임계값
    
    # 의도 분류 설정
    INTENT_CLASSES = {
        "text_generation": "텍스트 생성 (현대자동차/자동차 지식 질문)",
        "image_modification": "이미지 수정 요청"
    }
    
    # 프롬프트 템플릿
    SYSTEM_PROMPT = """You are a helpful assistant specialized in Hyundai Motor Company and automotive knowledge. 
    Answer all questions to the best of your ability. The provided chat history includes facts about the user you are speaking with. 
    YOU MUST ANSWER IN KOREAN."""
    
    INTENT_CLASSIFICATION_PROMPT = """다음 사용자 질문의 의도를 분류해주세요:

사용자 질문: {user_query}

의도 분류 옵션:
1. text_generation: 현대자동차나 자동차에 대한 지식 질문
2. image_modification: 이미지를 첨부하고 수정을 요청하는 질문

의도만 간단히 답변해주세요 (text_generation 또는 image_modification):"""

# 전역 설정 인스턴스
config = Config()

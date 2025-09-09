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
    
    # RAG 설정 - 최적화된 top-k 설정
    RAG_TOP_K = 8  # 최종 결과 문서 개수 (더 많은 컨텍스트)
    RAG_FETCH_K = 25  # 처음 검색할 문서 개수 (더 넓은 검색)
    RAG_SCORE_THRESHOLD = 0.7  # 유사도 임계값
    MMR_LAMBDA = 0.5  # MMR 다양성 파라미터
    
    # 대화 설정
    MAX_HISTORY_LENGTH = 10  # 대화 기록 최대 길이
    SUMMARIZATION_THRESHOLD = 5  # 요약 시작 임계값
    
    
    # 프롬프트 템플릿
    SYSTEM_PROMPT = """You are a helpful assistant specialized in Hyundai Motor Company and automotive knowledge. 
    Answer all questions to the best of your ability. The provided chat history includes facts about the user you are speaking with. 
    YOU MUST ANSWER IN KOREAN."""
    
    # 1단계: 초기 목적 파악 프롬프트
    INITIAL_INTENT_CLASSIFICATION_PROMPT = """다음 사용자 질문의 의도를 분류해주세요:

사용자 질문: {user_query}

의도 분류 옵션:
1. rag: 현대자동차나 자동차에 대한 구체적인 지식 질문 (기술, 디자인, 철학, 역사 등)
2. image_generation: 새로운 자동차 이미지 생성 요청 (예: "자동차 이미지 만들어줘", "새로운 디자인 생성해줘", "이미지 생성")
3. image_modification: 이미지 수정 요청 (예: "이미지 수정해줘", "이 차 색깔 바꿔줘", "이미지 업로드해서 수정")

반드시 다음 중 하나의 키워드만 답변하세요: rag, image_generation, image_modification"""

    # 2단계: 이미지 생성 세부 경로 분류 프롬프트
    IMAGE_GENERATION_INTENT_CLASSIFICATION_PROMPT = """사용자가 이미지 생성을 원합니다. 어떤 방식으로 진행할지 분류해주세요:

사용자 질문: {user_query}

이미지 생성 방식 분류:
1. guided: 체크리스트 기반 단계별 가이드 (예: "단계별로 만들어줘", "체크리스트로 해줘", "차근차근 만들어줘")
2. direct: 직접 이미지 생성 (예: "빨간색 SUV 만들어줘", "현대차 스타일로 만들어줘", "바로 만들어줘")

반드시 다음 중 하나의 키워드만 답변하세요: guided, direct"""

# 전역 설정 인스턴스
config = Config()

# 비즈니스 로직을 모아두는 곳입니다. views.py는 가볍게 유지하고,
# 실제 복잡한 로직(예: Qdrant 검색 로직, 데이터 계산, 외부 API 호출 등)은 여기에 작성
# Qdrant 연동 코드는 이 파일이나 별도의 qdrant_client.py 같은 파일에 정의하여 
# services.py에서 호출하는 방식

# JJACKLETTE/services.py

import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from django.conf import settings
# Qdrant 관련 모듈은 더 이상 직접 사용하지 않으므로 임포트하지 않거나 주석 처리
# from qdrant_client import QdrantClient, models 

# 전역 변수로 모델과 토크나이저 인스턴스를 저장하여 한 번만 로드되도록 캐싱
_global_ai_model = None
_global_ai_tokenizer = None

# Qdrant 클라이언트는 사용하지 않으므로 주석 처리하거나 제거
# _global_qdrant_client = None

# 임베딩 차원은 현재 사용하지 않지만, 나중에 RAG 활성화 시 필요할 수 있으므로 유지 (혹은 제거 가능)
EMBEDDING_DIMENSION = 2048 

# Qdrant 클라이언트 함수는 현재 사용하지 않으므로 주석 처리
# def get_qdrant_client():
#     """Qdrant 클라이언트를 초기화하거나 이미 초기화된 클라이언트를 반환합니다."""
#     global _global_qdrant_client
#     if _global_qdrant_client is None:
#         QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant") 
#         QDRANT_PORT = int(os.getenv("QDRANT_PORT_GRPC", "6334")) 
        
#         print(f"⏳ Qdrant 클라이언트 연결 시도: {QDRANT_HOST}:{QDRANT_PORT}")
#         try:
#             # print 문은 유지하여 연결 시도는 확인할 수 있게 함
#             _global_qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
#             _global_qdrant_client.get_collections() 
#             print("✅ Qdrant 클라이언트 연결 성공!")
#         except Exception as e:
#             print(f"❌ Qdrant 연결 테스트 실패: {e}")
#             _global_qdrant_client = None 
#             # raise ConnectionError(f"Qdrant 서버에 연결할 수 없습니다: {e}") # 연결 실패 시 오류 발생 중단
#     return _global_qdrant_client


def load_or_get_ai_model():
    global _global_ai_model, _global_ai_tokenizer

    if _global_ai_model is not None and _global_ai_tokenizer is not None:
        print("💡 AI 모델과 토크나이저는 이미 로드되어 있습니다.")
        return _global_ai_model, _global_ai_tokenizer

    # settings.py에서 설정된 모델 폴더 경로 사용
    model_folder_path = settings.CURRENT_MODEL_PATH 

    if not model_folder_path.exists():
        raise FileNotFoundError(f"모델 폴더가 존재하지 않습니다: {model_folder_path}")

    print(f"⏳ AI 모델 로드 시작: {model_folder_path}")

    try:
        # Exaone 4.0 1.2B의 경우 torch_dtype=torch.bfloat16 또는 torch.float16을 명시할 수 있습니다.
        # GPU 메모리 부족 시 도움이 됩니다. 없어도 작동할 수 있습니다.
        _global_ai_model = AutoModelForCausalLM.from_pretrained(
            model_folder_path, 
            trust_remote_code=True,
            # torch_dtype=torch.bfloat16 # 필요한 경우 주석 해제하여 사용
        )
        _global_ai_tokenizer = AutoTokenizer.from_pretrained(model_folder_path, trust_remote_code=True)
        
        # 토크나이저에 PAD 토큰이 없으면 EOS 토큰으로 설정 (일반적인 LLM 관행)
        if _global_ai_tokenizer.pad_token is None:
            _global_ai_tokenizer.pad_token = _global_ai_tokenizer.eos_token 
        
        _global_ai_model.eval() # 추론 모드로 설정
        print("✅ Hugging Face AI 모델과 토크나이저 로드 완료!")
        print(f"로드된 모델의 hidden_size: {_global_ai_model.config.hidden_size}")
        
        # 임베딩 차원 경고는 RAG가 활성화될 때 유효하므로 현재는 불필요하지만 유지 가능
        print(f"예상 임베딩 차원 (RAG 시): {EMBEDDING_DIMENSION}")
        if _global_ai_model.config.hidden_size != EMBEDDING_DIMENSION:
            print(f"🚨 경고: config.json의 hidden_size({_global_ai_model.config.hidden_size})와 코드의 EMBEDDING_DIMENSION({EMBEDDING_DIMENSION})이 다릅니다. RAG 활성화 시 확인 필요.")


        return _global_ai_model, _global_ai_tokenizer

    except Exception as e:
        print(f"❌ AI 모델 로드 중 오류 발생: {e}")
        _global_ai_model = None
        _global_ai_tokenizer = None
        raise # 모델 로드 실패는 치명적이므로 예외를 다시 발생시킵니다.


# get_query_embedding 함수는 현재 LLM 단독 테스트 단계에서는 사용하지 않으므로 주석 처리
# def get_query_embedding(text_input: str) -> list:
#     """
#     주어진 텍스트 입력(사용자 쿼리)으로 AI 모델 추론을 수행하고 임베딩 결과를 반환합니다.
#     """
#     model, tokenizer = load_or_get_ai_model()
#     if model is None or tokenizer is None:
#         raise ValueError("AI 모델이 로드되지 않았습니다.")
#     try:
#         inputs = tokenizer(text_input, return_tensors="pt", truncation=True, max_length=512)
#         if torch.cuda.is_available():
#             inputs = {k: v.to(model.device) for k, v in inputs.items()}
#         with torch.no_grad():
#             outputs = model(**inputs, output_hidden_states=True)
#             if hasattr(outputs, 'last_hidden_state'):
#                 embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()
#             else:
#                 raise AttributeError("모델 출력에 'last_hidden_state'가 없습니다. Exaone 4.0의 임베딩 추출 방식을 확인해주세요.")
#         return embeddings.cpu().numpy().tolist()[0] 
#     except Exception as e:
#         print(f"❌ 쿼리 임베딩 생성 중 오류 발생: {e}")
#         raise RuntimeError(f"쿼리 임베딩 생성 실패: {e}")

# retrieve_documents 함수도 현재 LLM 단독 테스트 단계에서는 사용하지 않으므로 주석 처리
# def retrieve_documents(query_embedding: list, collection_name: str = "my_rag_documents", limit: int = 5):
#     """
#     주어진 쿼리 임베딩으로 Qdrant에서 관련 문서를 검색합니다.
#     """
#     client = get_qdrant_client() # Qdrant 클라이언트 호출 시도 (주석 처리)
#     print(f"⏳ Qdrant에서 '{collection_name}' 컬렉션 검색 중...")
#     try:
#         search_result = client.search(
#             collection_name=collection_name,
#             query_vector=query_embedding,
#             limit=limit,
#             with_payload=True,  
#             with_vectors=False  
#         )
#         print(f"✅ Qdrant 검색 완료. {len(search_result)}개 문서 발견.")
#         return search_result
#     except Exception as e:
#         print(f"❌ Qdrant 문서 검색 중 오류 발생: {e}")
#         raise RuntimeError(f"Qdrant 검색 실패: {e}")

# --- RAG의 전체 흐름을 담당하는 메인 서비스 함수 (LLM 단독 테스트용) ---
def perform_rag_query(user_query: str):
    """
    사용자 쿼리를 받아 RAG 프로세스를 수행하고 결과를 반환합니다.
    현재는 LLM이 Django 내에서 잘 돌아가는지 확인하기 위해,
    Qdrant 검색 단계 없이 LLM이 직접 답변을 생성하도록 임시 수정합니다.
    """
    try:
        # LLM 모델 가져오기
        model, tokenizer = load_or_get_ai_model() 

        # --- Qdrant 검색 단계는 완전히 건너뛰고 LLM이 직접 응답하도록 설정 ---
        # messages = [
        #     {"role": "user", "content": f"다음 정보를 참고하여 질문에 답하세요:\n\n정보: {' '.join(context_texts)}\n\n질문: {user_query}\n\n답변:"}
        # ]
        # 위 RAG 프롬프트 대신, 사용자 쿼리 자체를 LLM에 전달합니다.
        messages = [
            {"role": "user", "content": user_query}
        ]
        
        input_ids = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
            # enable_thinking=True, # Reasoning mode를 원하면 이 주석을 해제
        )
        # 입력 텐서를 GPU로 이동
        if torch.cuda.is_available():
            input_ids = input_ids.to(model.device)

        # 답변 생성 파라미터 설정 (Exaone 권장 설정)
        generation_params = {
            "max_new_tokens": 512, # 생성할 최대 토큰 수
            "do_sample": True,
            "temperature": 0.1,    # 한국어 일반 대화 권장
            "top_p": 0.95,         # 일반적으로 사용
            "pad_token_id": tokenizer.pad_token_id,
            "eos_token_id": tokenizer.eos_token_id, 
        }
        # degeneration이 발생하면 presence_penalty=1.5 추가
        # generation_params["presence_penalty"] = 1.5 


        output_ids = model.generate(
            input_ids,
            **generation_params
        )
        
        generated_text = tokenizer.decode(output_ids[0][input_ids.shape[1]:], skip_special_tokens=True)
        final_answer = generated_text.strip()

        # RAG가 아니므로 source_documents는 항상 빈 리스트로 반환
        return {
            "answer": final_answer,
            "source_documents": [] 
        }

    except Exception as e:
        print(f"❌ LLM 텍스트 생성 중 오류 발생: {e}")
        # 오류 발생 시 에러 메시지 반환
        return {"error": f"LLM 텍스트 생성 실패: {e}"}
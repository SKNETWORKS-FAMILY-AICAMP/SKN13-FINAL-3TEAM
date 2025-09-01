
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import torch
from typing import List

# --- 설정 ---
MODEL_NAME = "BAAI/bge-m3"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"임베딩 모델을 {DEVICE}에서 실행합니다.")

# --- 모델 로딩 ---
# 서버 시작 시 모델을 한 번만 로드합니다.
try:
    model = SentenceTransformer(MODEL_NAME, device=DEVICE)
    print(f"'{MODEL_NAME}' 모델 로딩 성공.")
except Exception as e:
    print(f"모델 로딩 실패: {e}")
    model = None

# --- FastAPI 앱 생성 ---
app = FastAPI()

# --- 요청/응답 모델 정의 ---
class EmbeddingRequest(BaseModel):
    texts: List[str]

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]

# --- API 엔드포인트 ---
@app.get("/")
def read_root():
    return {"status": "Embedding server is running."}

@app.post("/embed", response_model=EmbeddingResponse)
def get_embeddings(request: EmbeddingRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="모델이 로드되지 않았습니다.")
    
    try:
        # sentence-transformers를 사용해 임베딩 생성
        embeddings = model.encode(request.texts, convert_to_tensor=False).tolist()
        return {"embeddings": embeddings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"임베딩 생성 중 오류 발생: {str(e)}")


import os
import json
from pathlib import Path
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm
from uuid import uuid4

HOST = os.getenv("HOST_PUBLIC_IP", "localhost")
PORT = 6333
EMBEDDING_DIM = 3072
COLLECTION_NAME = "qdrant_vectordb"

def load_documents(json_path):
    """
    Qdrant DB 에 올릴 문서 경로를 받아 JSON 데이터를 Document 객체로 변환 후 리스트로 반환해주는 함수
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    docs = [
        Document(page_content=item["page_content"], metadata=item["metadata"])
        for item in data
    ]
    return docs

def ensure_qdrant_collection(client, collection_name, vector_dim):
    """
    Qdrant Collection이 생성되었는지 확인하는 함수
    없을 경우 새로 생성
    """
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vector_config=VectorParams(size=vector_dim, distance=Distance.COSINE),
        )

def get_existing_titles(client, collection_name):
    """
    개별 데이터의 중복 확인 함수
    metadata -> title 값으로 확인
    """
    existing_titles = set()
    try:
        points, _ = client.scroll(collection_name=collection_name, limit=10000)
        for point in points:
            title = point.payload.get("title")
            if title:
                existing_titles.add(title)
    except Exception as e:
        print(f"Error while fetching existing titles: {e}")
    return existing_titles

def upload_docs_to_qdrant_batch(client, collection_name, docs, embedder, batch_size=64):
    """
    docs: Document 객체 리스트
    embedder: langchain 임베딩 객체
    batch_size: 한 번에 올릴 문서 수
    """
    total = len(docs)
    for i in tqdm(range(0, total, batch_size), desc="Qdrant 업로드"):
        batch_docs = docs[i:i+batch_size]
        vectors = embedder.embed_documents([doc.page_content for doc in batch_docs])
        points = [
            # id=None이면 Qdrant가 자동 할당
            PointStruct(id=str(uuid4()), vector=vec, payload=doc.metadata)
            for doc, vec in zip(batch_docs, vectors)
        ]
        client.upsert(collection_name=collection_name, points=points)

def check_qdrant_docs(client, collection_name):
    """
    현재 Qdrant 에 들어가있는 전체 문서 수 반환
    """
    print(client.count(collection_name))

def init_description_vectordb():
    """
    Vector DB 초기화 함수
    """
    # DATA_DIR = Path(__file__).parent.parent / "data"
    # DESC_JSON = DATA_DIR / "rag_vectordb.json"
    DESC_JSON = "./rag_vectordb.json"
    
    client = QdrantClient(host=HOST, port=PORT)
    ensure_qdrant_collection(client, COLLECTION_NAME, EMBEDDING_DIM)
    docs = load_documents(DESC_JSON)
    existing_titles = get_existing_titles(client, COLLECTION_NAME)
    new_docs = [doc for doc in docs if doc.metadata.get("title") not in existing_titles]
    embedder = OpenAIEmbeddings(
        model="text-embedding-3-large"
    )
    upload_docs_to_qdrant_batch(client, COLLECTION_NAME, new_docs, embedder)
    check_qdrant_docs(client, COLLECTION_NAME)

if __name__ == "__main__":
    init_description_vectordb()

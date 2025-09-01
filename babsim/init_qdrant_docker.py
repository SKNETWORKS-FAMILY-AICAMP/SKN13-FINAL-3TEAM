#!/usr/bin/env python3
"""
Docker 컨테이너 내에서 Qdrant DB 초기화 스크립트
BAAI/bge-m3 임베딩 모델을 사용하여 벡터 DB에 데이터를 넣습니다.
"""

import os
import json
from pathlib import Path
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from tqdm import tqdm
from uuid import uuid4

# Qdrant 설정 (Docker 컨테이너 내부에서 접근)
HOST = os.getenv("QDRANT_HOST", "qdrant")
PORT = int(os.getenv("QDRANT_PORT_REST", "6333"))
COLLECTION_NAME = "babsim_rag_db"

# 임베딩 모델 설정
EMBEDDING_MODEL = "BAAI/bge-m3"

def load_documents(json_path):
    """
    JSON 데이터를 Document 객체로 변환
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        docs = []
        for item in data:
            if isinstance(item, dict):
                content = item.get("page_content", "")
                metadata = item.get("metadata", {})
                docs.append(Document(page_content=content, metadata=metadata))
        
        print(f"로드된 문서 수: {len(docs)}")
        return docs
    except Exception as e:
        print(f"문서 로드 실패: {e}")
        return []

def ensure_qdrant_collection(client, collection_name):
    """
    Qdrant Collection 생성 확인
    """
    try:
        if not client.collection_exists(collection_name):
            print(f"컬렉션 '{collection_name}' 생성 중...")
            # BAAI/bge-m3 모델의 임베딩 차원은 1024
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
            )
            print(f"컬렉션 '{collection_name}' 생성 완료")
        else:
            print(f"컬렉션 '{collection_name}' 이미 존재")
    except Exception as e:
        print(f"컬렉션 생성/확인 실패: {e}")

def get_existing_titles(client, collection_name):
    """
    기존 데이터 중복 확인
    """
    existing_titles = set()
    try:
        points, _ = client.scroll(collection_name=collection_name, limit=10000)
        for point in points:
            title = point.payload.get("title")
            if title:
                existing_titles.add(title)
        print(f"기존 문서 수: {len(existing_titles)}")
    except Exception as e:
        print(f"기존 문서 확인 실패: {e}")
    return existing_titles

def upload_docs_to_qdrant_batch(client, collection_name, docs, embedder, batch_size=32):
    """
    문서를 배치로 Qdrant에 업로드
    """
    total = len(docs)
    print(f"총 {total}개 문서 업로드 시작...")
    
    for i in tqdm(range(0, total, batch_size), desc="Qdrant 업로드"):
        batch_docs = docs[i:i+batch_size]
        try:
            # 임베딩 생성
            texts = [doc.page_content for doc in batch_docs]
            vectors = embedder.embed_documents(texts)
            
            # 포인트 생성
            points = []
            for doc, vec in zip(batch_docs, vectors):
                point = PointStruct(
                    id=str(uuid4()),
                    vector=vec,
                    payload={
                        'page_content': doc.page_content,
                        **doc.metadata
                    }
                )
                points.append(point)
            
            # Qdrant에 업로드
            client.upsert(collection_name=collection_name, points=points)
            
        except Exception as e:
            print(f"배치 업로드 실패 (인덱스 {i}): {e}")
            continue

def check_qdrant_docs(client, collection_name):
    """
    Qdrant 문서 수 확인
    """
    try:
        count = client.count(collection_name)
        print(f"Qdrant 컬렉션 '{collection_name}'의 총 문서 수: {count}")
        return count
    except Exception as e:
        print(f"문서 수 확인 실패: {e}")
        return 0

def init_qdrant_vectordb():
    """
    Qdrant Vector DB 초기화 메인 함수
    """
    print("=== Qdrant Vector DB 초기화 시작 ===")
    
    # Qdrant 클라이언트 연결
    try:
        client = QdrantClient(host=HOST, port=PORT)
        print(f"Qdrant 연결 성공: {HOST}:{PORT}")
    except Exception as e:
        print(f"Qdrant 연결 실패: {e}")
        return
    
    # 컬렉션 확인/생성
    ensure_qdrant_collection(client, COLLECTION_NAME)
    
    # 데이터 파일 경로 설정
    data_files = [
        "./text_data/RAG/rag_vectordb.json",
        "./text_data/QA_context/hyundai_journal_articles_qa.jsonl",
        "./text_data/QA_context/interview_articles_qa.jsonl",
        "./text_data/QA_context/new_articles_qa.jsonl",
        "./text_data/QA_context/preview_articles_qa.jsonl",
        "./text_data/QA_context/total_articles_qa.jsonl"
    ]
    
    # 임베딩 모델 로드
    try:
        print(f"임베딩 모델 로딩 중: {EMBEDDING_MODEL}")
        embedder = HuggingFaceBgeEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("임베딩 모델 로딩 성공")
    except Exception as e:
        print(f"임베딩 모델 로딩 실패: {e}")
        return
    
    # 기존 문서 확인
    existing_titles = get_existing_titles(client, COLLECTION_NAME)
    
    # 각 데이터 파일 처리
    for data_file in data_files:
        if not os.path.exists(data_file):
            print(f"파일이 존재하지 않음: {data_file}")
            continue
            
        print(f"\n처리 중: {data_file}")
        
        # JSONL 파일인 경우 별도 처리
        if data_file.endswith('.jsonl'):
            docs = []
            with open(data_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        item = json.loads(line.strip())
                        if isinstance(item, dict):
                            content = item.get("question", "") + " " + item.get("answer", "")
                            metadata = {
                                "title": item.get("title", ""),
                                "source": data_file,
                                "type": "qa"
                            }
                            docs.append(Document(page_content=content, metadata=metadata))
                    except json.JSONDecodeError:
                        continue
        else:
            # 일반 JSON 파일 처리
            docs = load_documents(data_file)
        
        if not docs:
            print(f"문서가 없음: {data_file}")
            continue
        
        # 중복 제거
        new_docs = [doc for doc in docs if doc.metadata.get("title") not in existing_titles]
        
        if not new_docs:
            print(f"새로운 문서가 없음: {data_file}")
            continue
        
        print(f"업로드할 문서 수: {len(new_docs)}")
        
        # Qdrant에 업로드
        upload_docs_to_qdrant_batch(client, COLLECTION_NAME, new_docs, embedder)
        
        # 기존 제목 목록 업데이트
        for doc in new_docs:
            title = doc.metadata.get("title")
            if title:
                existing_titles.add(title)
    
    # 최종 문서 수 확인
    final_count = check_qdrant_docs(client, COLLECTION_NAME)
    print(f"\n=== Qdrant Vector DB 초기화 완료 ===")
    print(f"총 문서 수: {final_count}")

if __name__ == "__main__":
    init_qdrant_vectordb()

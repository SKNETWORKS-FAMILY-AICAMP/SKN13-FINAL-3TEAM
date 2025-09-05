#!/usr/bin/env python3
"""
Docker 컨테이너 내에서 Qdrant DB 초기화 스크립트
RunPod에 배포된 임베딩 모델을 사용하여 벡터 DB에 데이터를 넣습니다.
"""

import os
import json
import time
from pathlib import Path
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from tqdm import tqdm
from typing import List
from uuid import uuid4
import requests
from dotenv import load_dotenv

# Qdrant 설정 (Docker 컨테이너 내부에서 접근)
HOST = os.getenv("QDRANT_HOST", "qdrant")
PORT = int(os.getenv("QDRANT_PORT_REST", "6333"))
COLLECTION_NAME = "babsim_rag_db"

# 임베딩 모델 설정
load_dotenv()
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_ENDPOINT_ID = os.getenv("EMBEDDING_ENDPOINT_ID")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")

def embed_documents(self, texts: List[str]) -> List[List[float]]:
    return self._embed(texts)

def embed_query(self, text: str) -> List[float]:
    result = self._embed([text])
    return result[0] if result and result[0] else []


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
        # payload 필터링을 위해 with_payload에 title만 요청
        points, _ = client.scroll(collection_name=collection_name, limit=10000, with_payload=["title"])
        for point in points:
            title = point.payload.get("title")
            if title:
                existing_titles.add(title)
        print(f"기존 문서 수: {len(existing_titles)}")
    except Exception as e:
        print(f"기존 문서 확인 실패: {e}")
    return existing_titles

def check_embedding_status(endpoint_id, job_id, poll_interval=2):
    """
    Serverless Embedding Endpoint 상태 확인 함수 (폴링 방식)
    
    Args:
        endpoint_id (str) : Runpod endpoint ID
        job_id (str) : 잡 ID
        poll_interval (int) : 상태 확인 주기 (초)
    
    Returns:
        dict : 최종 응답 JSON
    """
    url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}

    while True:
        resp = requests.get(url, headers=headers).json()
        status = resp.get("status")

        if status == "COMPLETED":
            return resp
        elif status in ["FAILED", "CANCELLED"]:
            raise RuntimeError(f"❌ Job {job_id} failed: {resp}")
        else:
            print(f"⏳ Job {job_id} status: {status}")
            time.sleep(poll_interval)


def get_embedding_from_runpod(endpoint_id, texts):
    """
    Serverless Runpod Embedding Endpoint를 이용하여 임베딩 생성 (폴링 패턴)
    
    Args:
        endpoint_id (str) : Runpod endpoint ID
        texts (list[str]) : 입력 텍스트 리스트
    
    Returns:
        list : 생성된 임베딩 벡터들
    """
    url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }
    payload = {
        "input": {
            "input": texts,   # 워커가 기대하는 key 확인 필요 ("texts", "input", "prompt" 등)
            "model": EMBEDDING_MODEL
        }
    }

    # 1) 잡 실행
    resp = requests.post(url, headers=headers, json=payload).json()
    job_id = resp.get("id")
    if not job_id:
        raise RuntimeError(f"❌ Job 생성 실패: {resp}")

    # 2) 상태 확인 (폴링)
    final_resp = check_embedding_status(endpoint_id, job_id)

    # 3) 임베딩 결과 추출
    output = final_resp.get("output")
    if not output:
        raise RuntimeError(f"❌ 결과 없음: {final_resp}")

    # 워커 스펙에 맞게 키 이름 조정 필요
    datas = output.get("data")
    vectors = [item.get("embedding") for item in datas if item.get("embedding")]

    return vectors


def upload_docs_to_qdrant_batch(client, collection_name, docs, endpoint_id, batch_size=32):
    """
    문서를 배치로 Qdrant에 업로드
    """
    total = len(docs)
    print(f"총 {total}개 문서 업로드 시작...")
    
    for i in tqdm(range(0, total, batch_size), desc="Qdrant 업로드"):
        batch_docs = docs[i:i+batch_size]
        try:
            texts = [doc.page_content for doc in batch_docs]
            vectors = get_embedding_from_runpod(endpoint_id, texts)

            if not vectors:
                print(f"❌ 임베딩 생성 실패 (인덱스 {i}): {texts[0][:10]}")
                continue

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
            
            client.upsert(collection_name=collection_name, points=points, wait=True)
            
        except Exception as e:
            print(f"배치 업로드 실패 (인덱스 {i}): {e}")
            continue

def check_qdrant_docs(client, collection_name):
    """
    Qdrant 문서 수 확인
    """
    try:
        count = client.count(collection_name=collection_name, exact=True)
        print(f"Qdrant 컬렉션 '{collection_name}'의 총 문서 수: {count.count}")
        return count.count
    except Exception as e:
        print(f"문서 수 확인 실패: {e}")
        return 0

def init_qdrant_vectordb():
    """
    Qdrant Vector DB 초기화 메인 함수
    """
    print("=== Qdrant Vector DB 초기화 시작 ===")
    
    try:
        client = QdrantClient(host=HOST, port=PORT)
        print(f"Qdrant 연결 성공: {HOST}:{PORT}")
    except Exception as e:
        print(f"Qdrant 연결 실패: {e}")
        return
    
    ensure_qdrant_collection(client, COLLECTION_NAME)
    
    data_files = [
        "./text_data/RAG/rag_vectordb.json",
        "./text_data/QA_context/hyundai_journal_articles_qa.jsonl",
        "./text_data/QA_context/interview_articles_qa.jsonl",
        "./text_data/QA_context/new_articles_qa.jsonl",
        "./text_data/QA_context/preview_articles_qa.jsonl",
        "./text_data/QA_context/total_articles_qa.jsonl"
    ]
    
    # 기존 문서 확인
    existing_titles = get_existing_titles(client, COLLECTION_NAME)
    
    for data_file in data_files:
        if not os.path.exists(data_file):
            print(f"파일이 존재하지 않음: {data_file}")
            continue
            
        print(f"\n처리 중: {data_file}")
        
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
            docs = load_documents(data_file)
        
        if not docs:
            print(f"문서가 없음: {data_file}")
            continue
        
        new_docs = [doc for doc in docs if doc.metadata.get("title") not in existing_titles]
        
        if not new_docs:
            print(f"새로운 문서가 없음: {data_file}")
            continue
        
        print(f"업로드할 문서 수: {len(new_docs)}")
        
        # Qdrant에 업로드
        upload_docs_to_qdrant_batch(client, COLLECTION_NAME, new_docs, EMBEDDING_ENDPOINT_ID)
        
        for doc in new_docs:
            title = doc.metadata.get("title")
            if title:
                existing_titles.add(title)
    
    final_count = check_qdrant_docs(client, COLLECTION_NAME)
    print(f"\n=== Qdrant Vector DB 초기화 완료 ===")
    print(f"총 문서 수: {final_count}")

if __name__ == "__main__":
    init_qdrant_vectordb()
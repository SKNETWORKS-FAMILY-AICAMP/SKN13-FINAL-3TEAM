import os
import json
from pathlib import Path
import logging
from uuid import uuid4
import re
import hashlib
from datetime import datetime, timezone
from typing import List, Tuple, Optional

import torch
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient, models
from tqdm import tqdm

try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except ImportError:
    _HAS_DOTENV = False

try:
    import tiktoken
    _HAS_TIKTOKEN = True
except ImportError:
    _HAS_TIKTOKEN = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HOST = os.getenv("QDRANT_HOST", "localhost")
PORT = 6333
COLLECTION_NAME = "babsim_rag_db"

EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

TOKEN_CHUNK_SIZE = 1000
TOKEN_CHUNK_OVERLAP = 200
CHAR_FALLBACK_CHUNK_SIZE = 4000
CHAR_FALLBACK_CHUNK_OVERLAP = 400

SEPARATORS = ["\n\n", "\n", "。", "．", ". ", "! ", "? ", " ", ""]

def _get_splitter() -> RecursiveCharacterTextSplitter:
    if _HAS_TIKTOKEN and hasattr(RecursiveCharacterTextSplitter, "from_tiktoken_encoder"):
        return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base",
            separators=SEPARATORS,
            chunk_size=TOKEN_CHUNK_SIZE,
            chunk_overlap=TOKEN_CHUNK_OVERLAP,
        )
    return RecursiveCharacterTextSplitter(
        separators=SEPARATORS,
        chunk_size=CHAR_FALLBACK_CHUNK_SIZE,
        chunk_overlap=CHAR_FALLBACK_CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )

def _split_text_with_offsets(full_text: str, splitter: RecursiveCharacterTextSplitter) -> List[Tuple[str, int, int]]:
    chunks = splitter.split_text(full_text)
    results: List[Tuple[str, int, int]] = []
    cursor = 0
    search_back = 500
    for chunk in chunks:
        start_search = max(0, cursor - search_back)
        found = full_text.find(chunk, start_search)
        if found == -1:
            start_idx = cursor
        else:
            start_idx = found
        end_idx = start_idx + len(chunk)
        results.append((chunk, start_idx, end_idx))
        cursor = end_idx
    return results

def load_and_process_documents(data_path: Path) -> list[Document]:
    all_docs = []
    logging.info(f"'{data_path}' 디렉토리에서 문서 처리를 시작합니다...")
    for file_path in data_path.glob('*.*'):
        try:
            if file_path.suffix == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
                if file_path.name == "rag_vectordb.json":
                    for item in json_data:
                        if item.get("page_content"):
                            metadata = {**item.get("metadata", {}), "source": file_path.name}
                            all_docs.append(Document(page_content=item["page_content"], metadata=metadata))
                elif file_path.name == "hyundai_car_history.json":
                    for item in json_data:
                        if item.get("explain"):
                            content = f"차종: {item.get('car_name', '정보 없음')}\n연도: {item.get('year', '정보 없음')}\n설명: {item.get('explain')}"
                            metadata = {"source": file_path.name, "car_name": item.get('car_name'), "mime_type": "application/json"}
                            all_docs.append(Document(page_content=content, metadata=metadata))
                logging.info(f"✅ JSON 파일 처리 완료: {file_path.name}")
            elif file_path.suffix == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                articles = re.split(r'(?=\[\d+\])|^-+$', content, flags=re.MULTILINE)
                for i, article_text in enumerate(articles):
                    if article_text.strip():
                        metadata = {"source": file_path.name, "article_index": i, "mime_type": "text/plain"}
                        all_docs.append(Document(page_content=article_text.strip(), metadata=metadata))
                logging.info(f"✅ TXT 파일 처리 완료: {file_path.name}")
            elif file_path.suffix == ".pdf":
                loader = PyPDFLoader(str(file_path))
                docs_from_pdf = loader.load()
                for idx, d in enumerate(docs_from_pdf):
                    d.metadata = {**d.metadata, "source": file_path.name, "page": d.metadata.get("page", idx), "mime_type": "application/pdf"}
                all_docs.extend(docs_from_pdf)
                logging.info(f"✅ PDF 파일 처리 완료: {file_path.name}")
        except Exception as e:
            logging.error(f"'{file_path.name}' 파일 처리 중 오류 발생: {e}")

    splitter = _get_splitter()
    split_docs: list[Document] = []
    for doc in tqdm(all_docs, desc="문서 조각(Chunk)으로 분할 중"):
        text = doc.page_content
        pieces = _split_text_with_offsets(text, splitter)
        for idx, (chunk_text, start_idx, end_idx) in enumerate(pieces):
            doc_id = hashlib.sha256(str(doc.metadata.get("source", "")).encode("utf-8")).hexdigest()
            content_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
            new_meta = {
                **doc.metadata,
                "doc_id": doc_id,
                "chunk_index": idx,
                "char_start": start_idx,
                "char_end": end_idx,
                "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "content_hash": content_hash,
            }
            split_docs.append(Document(page_content=chunk_text, metadata=new_meta))
    logging.info(f"총 {len(all_docs)}개 원본 문서를 {len(split_docs)}개의 조각(Chunk)으로 분할했습니다.")
    return split_docs

def upload_docs_to_qdrant(client: QdrantClient, collection_name: str, docs: list[Document], embedder: HuggingFaceEmbeddings, batch_size: int = 32):
    for i in tqdm(range(0, len(docs), batch_size), desc="Qdrant에 문서 업로드 중"):
        batch_docs = docs[i:i+batch_size]
        contents = [doc.page_content for doc in batch_docs]
        vectors = embedder.embed_documents(contents)
        points = [
            models.PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload={**doc.metadata, "page_content": content},
            )
            for doc, vector, content in zip(batch_docs, vectors, contents)
        ]
        client.upsert(collection_name=collection_name, points=points, wait=True)

def main():
    DATA_DIR = Path(__file__).parent
    client = QdrantClient(host=HOST, port=PORT)
    try:
        logging.info(f"'{COLLECTION_NAME}' 컬렉션을 초기화하고 재생성합니다.")
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=EMBEDDING_DIM, distance=models.Distance.COSINE),
        )
        logging.info("페이로드 인덱스를 생성합니다.")
        for field in ("source", "doc_id", "section", "content_hash"):
            try:
                client.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
            except Exception as e:
                logging.debug(f"인덱스 생성 중 정보: {e}")
    except Exception as e:
        logging.error(f"Qdrant 컬렉션 생성 중 심각한 오류 발생: {e}")
        return

    all_docs = load_and_process_documents(DATA_DIR)
    new_docs = all_docs
    if not new_docs:
        logging.info("처리할 문서가 없습니다. 작업을 종료합니다.")
        return

    logging.info(f"총 {len(new_docs)}개의 문서 조각을 DB에 추가합니다.")
    logging.info(f"'{EMBEDDING_MODEL}' 임베딩 모델을 로드합니다... (최초 실행 시 시간이 걸릴 수 있습니다)")
    
    embedder = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    logging.info(f"모델이 {embedder.model_kwargs.get('device', 'cpu')} 장치에 로드되었습니다.")
    
    upload_docs_to_qdrant(client, COLLECTION_NAME, new_docs, embedder)

    final_count = client.count(collection_name=COLLECTION_NAME, exact=True).count
    logging.info(f"✅ 모든 작업 완료! 현재 '{COLLECTION_NAME}' 컬렉션의 총 문서 수: {final_count}")

if __name__ == "__main__":
    if _HAS_DOTENV:
        load_dotenv(dotenv_path=Path(__file__).parent / ".env")
    main()
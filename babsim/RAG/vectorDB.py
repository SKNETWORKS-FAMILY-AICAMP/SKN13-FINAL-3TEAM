import os
import json
from pathlib import Path
import logging
from uuid import uuid4
import re
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient, models
from tqdm import tqdm

# Qdrant 서버 및 컬렉션 정보
HOST = os.getenv("HOST_PUBLIC_IP", "localhost")
PORT = 6333
COLLECTION_NAME = "babsim_rag_db"

# OpenAI 임베딩 모델 정보
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072

def load_and_process_documents(data_path: Path) -> list[Document]:
    """
    지정된 디렉토리에서 다양한 형식의 파일을 읽고, 각 파일의 구조에 맞게
    최적의 방식으로 처리하여 LangChain Document 객체 리스트로 반환합니다.
    """
    all_docs = []
    logging.info(f"'{data_path}' 디렉토리에서 문서 처리를 시작합니다...")

    for file_path in data_path.glob('*.*'): # 모든 파일 탐색
        try:
            if file_path.suffix == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
                
                # 두 가지 다른 JSON 구조를 감지하고 처리
                if file_path.name == "rag_vectordb.json":
                    # 메타데이터가 이미 잘 정의된 경우
                    for item in json_data:
                        # page_content가 비어있지 않은 경우에만 추가
                        if item.get("page_content"):
                            all_docs.append(Document(page_content=item["page_content"], metadata=item["metadata"]))
                elif file_path.name == "hyundai_car_history.json":
                    # car_name, year, explain 구조인 경우
                    for item in json_data:
                        # explain 필드가 비어있지 않은 경우에만 처리
                        if item.get("explain"):
                            content = f"차종: {item.get('car_name', '정보 없음')}\n연도: {item.get('year', '정보 없음')}\n설명: {item.get('explain')}"
                            metadata = {"source": file_path.name, "car_name": item.get('car_name')}
                            all_docs.append(Document(page_content=content, metadata=metadata))
                logging.info(f"✅ JSON 파일 처리 완료: {file_path.name}")

            elif file_path.suffix == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # '[숫자]' 패턴으로 기사를 분리
                articles = re.split(r'\[\d+\]', content)
                for i, article_text in enumerate(articles):
                    if article_text.strip(): # 내용이 있는 경우에만 처리
                        metadata = {"source": file_path.name, "article_index": i}
                        all_docs.append(Document(page_content=article_text.strip(), metadata=metadata))
                logging.info(f"✅ TXT 파일 처리 완료: {file_path.name}")

            elif file_path.suffix == ".pdf":
                loader = PyPDFLoader(str(file_path))
                # PDF는 페이지 단위로 로드됩니다.
                docs_from_pdf = loader.load()
                all_docs.extend(docs_from_pdf)
                logging.info(f"✅ PDF 파일 처리 완료: {file_path.name}")

        except Exception as e:
            logging.error(f"'{file_path.name}' 파일 처리 중 오류 발생: {e}")
    
    # --- 텍스트 분할 (Chunking) ---
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False,
    )
    
    split_docs = text_splitter.split_documents(all_docs)
    logging.info(f"총 {len(all_docs)}개 문서를 {len(split_docs)}개의 조각(Chunk)으로 분할했습니다.")
    return split_docs

def get_existing_sources(client: QdrantClient, collection_name: str) -> set:
    """DB에 이미 존재하는 문서의 소스(파일명)를 확인하여 중복 저장을 방지합니다."""
    existing_sources = set()
    try:
        response = client.scroll(collection_name=collection_name, limit=10000, with_payload=["source"])
        points = response[0]
        for point in points:
            source = point.payload.get("source")
            if source:
                existing_sources.add(source)
        logging.info(f"기존에 저장된 {len(existing_sources)}개의 소스 파일을 확인했습니다.")
    except Exception as e:
        logging.warning(f"기존 소스 확인 중 정보 메시지 (오류가 아닐 수 있음): {e}")
    return existing_sources

def upload_docs_to_qdrant(client: QdrantClient, collection_name: str, docs: list[Document], embedder: OpenAIEmbeddings, batch_size: int = 32):
    """Document 리스트를 배치 단위로 임베딩하여 Qdrant에 업로드합니다."""
    
    for i in tqdm(range(0, len(docs), batch_size), desc="Qdrant에 문서 업로드 중"):
        batch_docs = docs[i:i+batch_size]
        contents = [doc.page_content for doc in batch_docs]
        vectors = embedder.embed_documents(contents)
        
        points = [
            models.PointStruct(
                id=str(uuid4()), 
                vector=vector, 
                payload={**doc.metadata, "page_content": content}
            )
            for doc, vector, content in zip(batch_docs, vectors, contents)
        ]
        
        client.upsert(collection_name=collection_name, points=points, wait=True)

def main():
    """Vector DB 초기화 및 데이터 업로드 실행 함수"""
    DATA_DIR = Path(__file__).parent
    client = QdrantClient(host=HOST, port=PORT)
    
    try:
        client.get_collection(collection_name=COLLECTION_NAME)
        logging.info(f"'{COLLECTION_NAME}' 컬렉션이 이미 존재합니다.")
    except Exception:
        logging.info(f"'{COLLECTION_NAME}' 컬렉션이 없어 새로 생성합니다.")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=EMBEDDING_DIM, distance=models.Distance.COSINE),
        )

    all_docs = load_and_process_documents(DATA_DIR)
    
    existing_sources = get_existing_sources(client, COLLECTION_NAME)
    
    new_docs = [doc for doc in all_docs if doc.metadata.get("source") not in existing_sources]
    
    if not new_docs:
        logging.info("새롭게 추가할 문서가 없습니다. 작업을 종료합니다.")
        return

    logging.info(f"총 {len(new_docs)}개의 새로운 문서 조각을 DB에 추가합니다.")

    embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    upload_docs_to_qdrant(client, COLLECTION_NAME, new_docs, embedder)
    
    final_count = client.count(collection_name=COLLECTION_NAME, exact=True).count
    logging.info(f"✅ 모든 작업 완료! 현재 '{COLLECTION_NAME}' 컬렉션의 총 문서 수: {final_count}")


if __name__ == "__main__":
    if "OPENAI_API_KEY" not in os.environ:
        logging.error("환경변수에 OPENAI_API_KEY가 설정되지 않았습니다. 스크립트를 종료합니다.")
    else:
        main()

# data/processed_data/*.json 파일을 읽어옵니다.
# 각 JSON 객체의 content 필드(또는 title + content 조합)를 가져와서
# 임베딩 모델을 통해 벡터 생성
# Qdrant 클라이언트를 사용하여 Qdrant 서버에 접속하고, 필요한 컬렉션을 생성
# 생성된 벡터와 해당 JSON 객체의 id, title, url 등 RAG 검색 결과에 필요한 메타데이터(payload)를
# Qdrant에 포인트로 삽입
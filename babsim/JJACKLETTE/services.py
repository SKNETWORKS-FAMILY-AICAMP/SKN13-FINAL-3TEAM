# 비즈니스 로직을 모아두는 곳입니다. views.py는 가볍게 유지하고,
# 실제 복잡한 로직(예: Qdrant 검색 로직, 데이터 계산, 외부 API 호출 등)은 여기에 작성
# Qdrant 연동 코드는 이 파일이나 별도의 qdrant_client.py 같은 파일에 정의하여 
# services.py에서 호출하는 방식
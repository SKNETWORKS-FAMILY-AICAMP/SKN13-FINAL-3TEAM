# Babsim 파이프라인 테스트 가이드

이 문서는 Babsim 파이프라인을 테스트하는 다양한 방법들을 설명합니다.

## 📋 목차

1. [사전 준비](#사전-준비)
2. [테스트 방법들](#테스트-방법들)
3. [문제 해결](#문제-해결)
4. [테스트 결과 해석](#테스트-결과-해석)

## 🔧 사전 준비

### 1. 환경 설정

```bash
# babsim 디렉토리로 이동
cd /path/to/babsim

# 필요한 패키지 설치
pip install -r requirements.txt

# 추가 패키지 설치 (필요한 경우)
pip install langgraph langchain-core pydantic
```

### 2. 서비스 확인

- **Qdrant 서버**: Vector DB가 실행 중인지 확인
- **Django 서버**: Django 애플리케이션이 실행 중인지 확인
- **모델 파일**: 필요한 AI 모델들이 다운로드되어 있는지 확인

## 🧪 테스트 방법들

### 1. 단위 테스트

개별 컴포넌트들을 독립적으로 테스트합니다.

```bash
python pipeline/test_unit.py
```

**테스트 항목:**
- 설정 파일 로드
- 의도 분류기
- 채팅 매니저
- 이미지 쿼리 생성기
- RAG 어댑터
- 서비스 레이어

### 2. 종합 통합 테스트

전체 파이프라인 워크플로우와 Django 연동을 테스트합니다.

```bash
python test_pipeline_integration.py
```

**테스트 항목:**
- Django 설정 및 모델 연동
- Vector DB 연결
- 파이프라인 컴포넌트
- 파이프라인 서비스
- Django API
- 대화형 테스트

### 3. 파이프라인 기본 테스트

파이프라인의 기본 기능을 테스트합니다.

```bash
python run_pipeline_test.py
```

### 4. 모델 로딩 테스트

AI 모델이 정상적으로 로드되는지 테스트합니다.

```bash
python test_model.py
```

## 🔍 테스트 시나리오

### 기본 시나리오

1. **인사 테스트**
   ```
   입력: "안녕하세요"
   예상: 일반적인 인사 응답
   ```

2. **현대자동차 질문**
   ```
   입력: "현대자동차에 대해 알려주세요"
   예상: RAG 기반 상세 답변
   ```

3. **이미지 수정 요청**
   ```
   입력: "이 이미지를 수정해주세요"
   예상: 이미지 수정 관련 응답
   ```

### 고급 시나리오

1. **Multi-turn 대화**
   ```
   사용자: "SUV 차량을 디자인하고 싶어요"
   어시스턴트: "좋습니다! 어떤 종류의 SUV를 원하시나요?"
   사용자: "전면부 뷰로 보여주세요"
   어시스턴트: "전면부 뷰로 SUV를 디자인하겠습니다."
   ```

2. **폼 완성 플로우**
   ```
   사용자: "SUV 차량을 디자인하고 싶어요"
   사용자: "LED 헤드램프를 사용하고 싶어요"
   사용자: "검은색으로 만들어주세요"
   사용자: "스포티한 느낌으로 디자인해주세요"
   예상: 이미지 생성 쿼리 생성
   ```

## ⚠️ 문제 해결

### 일반적인 오류들

1. **ModuleNotFoundError**
   ```
   해결: pip install [패키지명]
   ```

2. **Django 설정 오류**
   ```
   해결: Django 서버가 실행 중인지 확인
   ```

3. **Qdrant 연결 오류**
   ```
   해결: Qdrant 서버가 실행 중인지 확인
   ```

4. **모델 로딩 오류**
   ```
   해결: 필요한 모델 파일이 다운로드되어 있는지 확인
   ```

### 디버그 모드

대화형 테스트에서 디버그 모드를 활성화하면 상세한 정보를 볼 수 있습니다.

```
사용자: debug
🔍 디버그 모드가 활성화되었습니다.
```

## 📊 테스트 결과 해석

### 성공 지표

- ✅ 모든 컴포넌트가 정상 로드
- ✅ 의도 분류가 정확함
- ✅ RAG 응답이 생성됨
- ✅ 대화 기록이 유지됨
- ✅ 폼 완성이 정상 작동

### 성능 지표

- **응답 시간**: 5초 이내
- **메모리 사용량**: 2GB 이하
- **정확도**: 80% 이상

### 문제 진단

1. **느린 응답 시간**
   - 모델 로딩 최적화 필요
   - 캐싱 구현 고려

2. **부정확한 의도 분류**
   - 프롬프트 개선 필요
   - 학습 데이터 추가 고려

3. **RAG 응답 품질 저하**
   - Vector DB 데이터 품질 확인
   - 임베딩 모델 개선 고려

## 🚀 고급 테스트

### 부하 테스트

```python
# 동시 요청 테스트
import threading
import time

def stress_test():
    # 여러 스레드에서 동시에 요청
    pass
```

### 메모리 테스트

```python
# 메모리 사용량 모니터링
import psutil
import os

def memory_test():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return memory_info.rss / 1024 / 1024  # MB
```

## 📝 테스트 결과 저장

통합 테스트는 자동으로 JSON 형태로 결과를 저장합니다.

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "results": {
    "full_pipeline": [...],
    "multi_turn": [...],
    "form_completion": {...},
    "performance": {...}
  }
}
```

## 🔄 지속적 테스트

### 자동화 스크립트

```bash
#!/bin/bash
# daily_test.sh

cd /path/to/babsim
python pipeline/test_unit.py
python pipeline/test_integration.py
```

### CI/CD 통합

GitHub Actions나 Jenkins에서 자동 테스트를 설정할 수 있습니다.

## 📞 지원

테스트 중 문제가 발생하면 다음을 확인하세요:

1. 로그 파일 확인
2. 환경 변수 설정 확인
3. 의존성 패키지 버전 확인
4. 서비스 상태 확인

---

**마지막 업데이트**: 2024년 1월

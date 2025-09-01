# kanana-1.5-8b-instruct 파인튜닝 가이드

## 📋 개요

이 가이드는 `kakao/kanana-1.5-8b-instruct` 모델을 현대자동차 QA 데이터로 LoRA 파인튜닝하는 방법을 설명합니다.

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 1. 필요한 패키지 설치
python install_requirements.py

# 2. 환경변수 설정
cp env_example.txt .env
# .env 파일을 편집하여 HF_TOKEN 설정
```

### 2. 데이터셋 준비

```bash
# contexts_result 데이터를 파인튜닝용으로 변환
python prepare_finetuning_dataset.py
```

### 3. 파인튜닝 실행

```bash
# LoRA 파인튜닝 실행
python finetune_kanana.py
```

## 📁 파일 구조

```
text_data/
├── prepare_finetuning_dataset.py  # 데이터셋 준비
├── finetune_kanana.py             # 파인튜닝 실행
├── install_requirements.py        # 패키지 설치
├── env_example.txt               # 환경변수 예시
├── contexts_result/              # 입력 데이터
├── finetuning_dataset/           # 준비된 데이터셋
└── finetuned_model/              # 파인튜닝된 모델
```

## ⚙️ 설정 옵션

### LoRA 설정 (finetune_kanana.py)

```python
LORA_CONFIG = {
    "r": 16,                    # LoRA rank (높을수록 성능↑, 메모리↑)
    "lora_alpha": 32,           # LoRA alpha
    "target_modules": [...],    # 적용할 모듈들
    "lora_dropout": 0.1,        # 드롭아웃
    "bias": "none",             # 바이어스 설정
}
```

### 훈련 설정

```python
TRAINING_ARGS = {
    "num_train_epochs": 3,      # 에포크 수
    "per_device_train_batch_size": 2,  # 배치 크기
    "learning_rate": 2e-4,      # 학습률
    "gradient_accumulation_steps": 4,  # 그래디언트 누적
    "fp16": True,               # 16비트 정밀도
}
```

## 🔧 하드웨어 요구사항

### 최소 요구사항
- **GPU**: 16GB VRAM (RTX 4080, A100 등)
- **RAM**: 32GB
- **저장공간**: 50GB

### 권장사항
- **GPU**: 24GB+ VRAM (RTX 4090, A100 40GB 등)
- **RAM**: 64GB
- **저장공간**: 100GB

## 📊 데이터 형식

### 입력 데이터 (contexts_result)
```json
{
    "question": "아이오닉 5의 주행거리는?",
    "answer": "아이오닉 5는 451km 주행 가능합니다.",
    "contexts": [
        "[1] 아이오닉 5는 77.4kWh 배터리로 451km 주행 가능",
        "[2] 아이오닉 5의 최고속도는 185km/h"
    ],
    "evidence_ids": [1]
}
```

### 파인튜닝 형식
```
<|im_start|>system
당신은 현대자동차 전문가입니다. 주어진 컨텍스트를 바탕으로 질문에 답변해주세요.
<|im_end|>
<|im_start|>user
컨텍스트:
[1] 아이오닉 5는 77.4kWh 배터리로 451km 주행 가능

질문: 아이오닉 5의 주행거리는?
<|im_end|>
<|im_start|>assistant
아이오닉 5는 451km 주행 가능합니다.
<|im_end|>
```

## 🎯 성능 최적화 팁

### 1. 메모리 절약
- `load_in_4bit=True`: 4비트 양자화 사용
- `gradient_accumulation_steps`: 그래디언트 누적으로 배치 크기 효과
- `fp16=True`: 16비트 정밀도 사용

### 2. 학습률 조정
- 시작: `2e-4`
- 너무 빠름: `1e-4`로 낮춤
- 너무 느림: `5e-4`로 높임

### 3. LoRA 설정
- `r=16`: 기본값, 성능과 메모리 균형
- `r=32`: 더 높은 성능, 더 많은 메모리
- `r=8`: 메모리 절약, 성능 약간 저하

## 🔍 모니터링

### 훈련 중 확인사항
- Loss 감소 추이
- GPU 메모리 사용량
- 학습률 스케줄링

### 평가 지표
- `eval_loss`: 검증 손실
- `train_loss`: 훈련 손실
- 훈련 시간

## 🚨 문제 해결

### 1. CUDA 메모리 부족
```python
# 배치 크기 줄이기
"per_device_train_batch_size": 1

# 그래디언트 누적 늘리기
"gradient_accumulation_steps": 8
```

### 2. 학습이 너무 느림
```python
# 학습률 높이기
"learning_rate": 5e-4

# 배치 크기 늘리기
"per_device_train_batch_size": 4
```

### 3. 과적합
```python
# 드롭아웃 늘리기
"lora_dropout": 0.2

# 에포크 줄이기
"num_train_epochs": 2
```

## 📈 결과 확인

### 1. 로컬 모델 테스트
```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# 모델 로드
model = AutoModelForCausalLM.from_pretrained("kakao/kanana-1.5-8b-instruct")
model = PeftModel.from_pretrained(model, "./finetuned_model")

# 추론
tokenizer = AutoTokenizer.from_pretrained("kakao/kanana-1.5-8b-instruct")
inputs = tokenizer("질문: 아이오닉 5의 주행거리는?", return_tensors="pt")
outputs = model.generate(**inputs, max_length=100)
print(tokenizer.decode(outputs[0]))
```

### 2. 허깅페이스에서 다운로드
```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

model = AutoModelForCausalLM.from_pretrained("your-username/hyundai-kanana-finetuned")
tokenizer = AutoTokenizer.from_pretrained("your-username/hyundai-kanana-finetuned")
```

## 📝 주의사항

1. **GPU 메모리**: 8B 모델은 많은 VRAM이 필요합니다
2. **훈련 시간**: 3 에포크 기준 2-4시간 소요
3. **데이터 품질**: 입력 데이터의 품질이 결과에 큰 영향을 줍니다
4. **하이퍼파라미터**: 데이터셋에 따라 최적값이 다를 수 있습니다

## 🔗 유용한 링크

- [kanana 모델 카드](https://huggingface.co/kakao/kanana-1.5-8b-instruct)
- [PEFT 문서](https://huggingface.co/docs/peft)
- [Transformers 문서](https://huggingface.co/docs/transformers)
- [LoRA 논문](https://arxiv.org/abs/2106.09685)

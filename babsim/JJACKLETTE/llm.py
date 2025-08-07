# BABSIM/JJACKLETTE/llm.py

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model = None
tokenizer = None
# GPU가 있다면 "cuda", 없다면 "cpu"를 사용합니다. 로그를 보니 "cpu"로 실행되고 있습니다.
device = "cuda" if torch.cuda.is_available() else "cpu"

def load_model():
    """애플리케이션 시작 시 모델을 메모리에 로드하는 함수."""
    global model, tokenizer
    
    # 모델이 이미 로드되었다면 다시 로드하지 않도록 합니다.
    if model is not None:
        return

    # ---▼▼▼ 바로 이 한 줄이 모든 문제의 핵심입니다! ▼▼▼---
    # 컨테이너 내부 경로를 정확하게 지정합니다.
    # 슬래시(/)를 사용하고, PC의 C: 드라이브 경로는 절대 쓰지 않습니다.
    model_path = "/app/model/exaone_4.0_1.2b"
    # ---▲▲▲ 이 한 줄만 올바르게 수정하면 됩니다 ▲▲▲---
    # model_path = "LGAI-EXAONE/EXAONE-4.0-1.2B"

    # 이전 로그를 보니, PC의 `.../models` 폴더 안에 `exaone-4.0-1.2b` 폴더를 두신 것 같습니다.
    # 만약 `.../models` 폴더 안에 `models` 폴더가 또 있고 그 안에 있다면,
    # model_path = "/app/models/models/exaone-4.0-1.2b" 로 하셔야 합니다.
    # 이전 로그 상으로는 이 경로가 맞는 것으로 보입니다.

    print(f"LLM: Loading model from : '{model_path}' on device '{device}'...")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(model_path).to(device)
        print("LLM: Model loaded successfully.")
    except Exception as e:
        # 모델 로딩 실패 시, Gunicorn이 계속 재시작하는 것을 방지하기 위해 오류를 출력하고 넘어갑니다.
        print(f"LLM: FATAL - Failed to load model. Error: {e}")
        model = None
        tokenizer = None

def generate_text(prompt: str) -> str:
    """로드된 모델을 사용하여 텍스트를 생성하는 함수."""
    if model is None or tokenizer is None:
        return "모델이 정상적으로 로드되지 않았습니다. 서버 로그를 확인해주세요."
        
    device = model.device
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    
    outputs = model.generate(**inputs, max_new_tokens=150, pad_token_id=tokenizer.eos_token_id)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return response
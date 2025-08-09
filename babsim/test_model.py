# test_model.py
from transformers import AutoTokenizer, AutoModelForCausalLM
import os

MODEL_PATH = "models/exaone_4.0_1.2b"

print(f"--- 모델 로딩 테스트 시작 ---")
print(f"모델 경로: '{os.path.abspath(MODEL_PATH)}'")

if not os.path.isdir(MODEL_PATH):
    print(f"[실패] 오류: '{MODEL_PATH}' 폴더를 찾을 수 없습니다.")
    exit()

try:
    file_list = os.listdir(MODEL_PATH)
    if not file_list:
        print(f"[실패] 오류: '{MODEL_PATH}' 폴더가 비어있습니다.")
        exit()
    print(f"폴더 내 파일 목록 (상위 5개): {file_list[:5]}")
except Exception as e:
    print(f"[실패] 오류: 폴더를 읽는 중 문제가 발생했습니다. {e}")
    exit()

try:
    print("\n1. 토크나이저 로딩 시도...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    print("[성공] 토크나이저 로딩 완료!")
except Exception as e:
    print(f"[실패] 토크나이저 로딩 중 오류 발생!")
    print("------ ERROR MESSAGE ------")
    print(e)
    print("---------------------------")
    exit()
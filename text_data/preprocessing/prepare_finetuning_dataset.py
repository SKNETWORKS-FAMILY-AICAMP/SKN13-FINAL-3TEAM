# -*- coding: utf-8 -*-
"""
파인튜닝용 데이터셋 준비 및 허깅페이스 업로드 스크립트
"""
import os
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from datasets import Dataset, DatasetDict
from huggingface_hub import HfApi, login
import random
# 설정
CONTEXTS_DIR = Path("./contexts_result")
OUTPUT_DIR = Path("./finetuning_dataset")
HF_REPO_NAME = "hyundai-qa-dataset"  # 허깅페이스 저장소 이름
HF_TOKEN = os.environ["HF_TOKEN"]  # 환경변수에서 토큰 가져오기

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_contexts_data() -> List[Dict[str, Any]]:
    """contexts_result의 모든 JSONL 파일을 로드하여 통합"""
    all_data = []
    
    for jsonl_file in CONTEXTS_DIR.glob("*_contexts.jsonl"):
        print(f"로딩 중: {jsonl_file.name}")
        
        with jsonl_file.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    all_data.append(data)
                except json.JSONDecodeError:
                    continue
    
    print(f"총 {len(all_data)}개 샘플 로드 완료")
    return all_data

def format_for_finetuning(data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """파인튜닝용 형식으로 변환 (kanana-1.5-8b-instruct 형식)"""
    formatted_data = []
    
    for item in data:
        question = item.get("question", "")
        answer = item.get("answer", "")
        contexts = item.get("contexts", [])
        
        if not question or not answer:
            continue
            
        # 컨텍스트를 문자열로 결합
        context_text = "\n".join(contexts) if contexts else ""
        
        # kanana-1.5-8b-instruct 형식으로 포맷팅
        # <|im_start|>system
        # 당신은 현대자동차 전문가입니다. 주어진 컨텍스트를 바탕으로 질문에 답변해주세요.
        # <|im_end|>
        # <|im_start|>user
        # 컨텍스트: {context_text}
        # 
        # 질문: {question}
        # <|im_end|>
        # <|im_start|>assistant
        # {answer}
        # <|im_end|>
        
        system_prompt ="""
        당신은 현대자동차 전문가이자 디자이너입니다.  
        당신의 임무는 주어진 컨텍스트를 바탕으로 질문에 답변하는 것입니다.  

        규칙:  
        1. 제공된 컨텍스트 중에서 질문에 답을 직접적으로 뒷받침하는 문장(positive evidence)을 식별하세요.  
        2. 컨텍스트에 명시적으로 답을 지지하지 않는 문장(negative evidence)은 무시하세요.  
        3. 최종 답변은 반드시 positive evidence에 기반하여 작성하세요.  
        4. 답변에는 반드시 어떤 컨텍스트를 참고했는지 `[번호]` 형태로 표시하세요.  
        - 예시: "현대자동차의 디자인 철학은 '센슈어스 스포티니스'입니다 [2]."  
        5. positive evidence가 전혀 없는 경우에는:  
        "해당 질문에 대한 답을 찾을 수 없습니다." 라고 답변하세요.  
        6. 답변은 현대자동차 디자이너로서의 전문성과 통찰력을 반영하여, 간결하면서도 정확하게 작성하세요.
        """
        
        if context_text:
            user_prompt = f"컨텍스트:\n{context_text}\n\n질문: {question}"
        else:
            user_prompt = f"질문: {question}"
        
        formatted_item = {
            "system": system_prompt,
            "user": user_prompt,
            "assistant": answer,
            "question": question,
            "answer": answer,
            "contexts": context_text,
            "source_file": item.get("source_file", ""),
            "chunk_id": item.get("chunk_id", "")
        }
        
        formatted_data.append(formatted_item)
    
    print(f"포맷팅 완료: {len(formatted_data)}개 샘플")
    return formatted_data

def split_train_test(data: List[Dict[str, str]], test_ratio: float = 0.1) -> tuple:
    """데이터를 train/test로 분할"""
    random.shuffle(data)
    
    split_idx = int(len(data) * (1 - test_ratio))
    train_data = data[:split_idx]
    test_data = data[split_idx:]
    
    print(f"Train: {len(train_data)}개, Test: {len(test_data)}개")
    return train_data, test_data

def create_hf_dataset(train_data: List[Dict], test_data: List[Dict]) -> DatasetDict:
    """허깅페이스 Dataset 형식으로 변환"""
    
    # Train dataset
    train_dataset = Dataset.from_list(train_data)
    
    # Test dataset  
    test_dataset = Dataset.from_list(test_data)
    
    # DatasetDict 생성
    dataset_dict = DatasetDict({
        "train": train_dataset,
        "test": test_dataset
    })
    
    return dataset_dict

def save_locally(dataset_dict: DatasetDict):
    """로컬에 저장"""
    dataset_dict.save_to_disk(OUTPUT_DIR / "hyundai_qa_dataset")
    print(f"로컬 저장 완료: {OUTPUT_DIR / 'hyundai_qa_dataset'}")

def upload_to_hf(dataset_dict: DatasetDict, repo_name: str):
    """허깅페이스에 업로드"""
    if not HF_TOKEN:
        print("HF_TOKEN 환경변수가 설정되지 않았습니다. 로컬 저장만 진행합니다.")
        return
    
    try:
        login(token=HF_TOKEN)
        api = HfApi()
        
        # 저장소 생성 (이미 존재하면 무시)
        try:
            api.create_repo(repo_name, repo_type="dataset", exist_ok=True)
        except Exception as e:
            print(f"저장소 생성/확인 중 오류: {e}")
        
        # 데이터셋 업로드
        dataset_dict.push_to_hub(repo_name)
        print(f"허깅페이스 업로드 완료: https://huggingface.co/datasets/{repo_name}")
        
    except Exception as e:
        print(f"허깅페이스 업로드 실패: {e}")

def main():
    print("=== 파인튜닝 데이터셋 준비 시작 ===")
    
    # 1. 데이터 로드
    print("\n1. contexts_result 데이터 로드 중...")
    raw_data = load_contexts_data()
    
    # 2. 파인튜닝 형식으로 변환
    print("\n2. 파인튜닝 형식으로 변환 중...")
    formatted_data = format_for_finetuning(raw_data)
    
    # 3. Train/Test 분할
    print("\n3. Train/Test 분할 중...")
    train_data, test_data = split_train_test(formatted_data, test_ratio=0.1)
    
    # 4. 허깅페이스 Dataset 생성
    print("\n4. 허깅페이스 Dataset 생성 중...")
    dataset_dict = create_hf_dataset(train_data, test_data)
    
    # 5. 로컬 저장
    print("\n5. 로컬 저장 중...")
    save_locally(dataset_dict)
    
    # 6. 허깅페이스 업로드
    print("\n6. 허깅페이스 업로드 중...")
    upload_to_hf(dataset_dict, HF_REPO_NAME)
    
    print("\n=== 데이터셋 준비 완료 ===")
    print(f"Train: {len(train_data)}개")
    print(f"Test: {len(test_data)}개")
    print(f"로컬 저장 위치: {OUTPUT_DIR / 'hyundai_qa_dataset'}")

if __name__ == "__main__":
    main()

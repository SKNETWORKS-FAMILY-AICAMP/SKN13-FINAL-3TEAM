# -*- coding: utf-8 -*-
"""
kakao/kanana-1.5-8b-instruct 모델 LoRA 파인튜닝 스크립트
"""
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, DataCollatorForLanguageModeling
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
import time

# GPU 설정
os.environ["NVIDIA_VISIBLE_DEVICES"] = "0"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# 설정
MODEL_NAME = "kakaocorp/kanana-1.5-8b-instruct-2505"
DATASET_ID = "jiyun12/hyundai-qa-dataset"  # Hugging Face 데이터셋 ID
OUTPUT_DIR = "./finetuned_model"
HF_REPO_NAME = "hyundai-kanana-finetuned"

# LoRA 설정
LORA_CONFIG = {
    "r": 16,                   # LoRA rank (48GB에서는 더 높게 설정 가능)
    "lora_alpha": 64,          # LoRA alpha (r의 4배)
    "lora_dropout": 0.1,       # LoRA dropout
    "target_modules": [
        "q_proj", "k_proj", "v_proj", "o_proj",  # Attention 모듈
        "gate_proj", "up_proj", "down_proj"      # FFN 모듈 (48GB에서는 추가 가능)
    ]
}


def load_model_and_tokenizer():
    """모델과 토크나이저 로드"""
    print(f"모델 로딩 중: {MODEL_NAME}")
    
    # 모델 로드
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        device_map="auto"  # 자동 디바이스 매핑
    )
    
    # 토크나이저 로드
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME, 
        padding_side="left"
    )
    
    tokenizer.pad_token = tokenizer.eos_token
    
    print("모델과 토크나이저 로드 완료")
    return model, tokenizer

def load_dataset_from_hf():
    """Hugging Face에서 데이터셋 로드"""
    print(f"데이터셋 로딩 중: {DATASET_ID}")
    
    dataset = load_dataset(DATASET_ID)
    train_set = dataset['train']
    test_set = dataset['test']
    
    print(f"데이터셋 로드 완료: Train={len(train_set)}개, Test={len(test_set)}개")
    return dataset

def formatting_prompts_func(examples, tokenizer):
    """kanana 모델용 프롬프트 포맷팅 함수
    - instruction  <- system
    - input        <- question (+ optional context)
    - response     <- answer
    """
    kanana_prompt = (
        "Below is an instruction that describes a task, paired with an input that provides further context. "
        "Write a response that appropriately completes the request.\n\n"
        "### Instruction:\n{}\n\n"
        "### Input:\n{}\n\n"
        "### Response:\n{}"
    )

    # 필수 컬럼 - 이미 배치 처리된 리스트
    questions = examples["question"]
    answers = examples["answer"]

    # system: 배치 전체에 공통 문자열이 들어오거나, 각 샘플별 리스트로 들어올 수 있음 -> 모두 리스트로 표준화
    systems = examples.get("system", "")
    if isinstance(systems, str):
        systems = [systems] * len(questions)

    # context/contexts 지원 (없으면 빈 문자열)
    contexts = examples.get("context", examples.get("contexts", ""))
    if isinstance(contexts, str):
        contexts = [contexts] * len(questions)

    EOS_TOKEN = tokenizer.eos_token or ""

    # 배치 처리된 데이터를 직접 처리 (중첩 리스트 방지)
    texts = []
    for i in range(len(questions)):
        sys_inst = systems[i] if isinstance(systems, list) else systems
        question = questions[i]
        answer = answers[i]
        context = contexts[i] if isinstance(contexts, list) else contexts
        
        # 입력(Input) 구성: context가 있으면 함께 넣고, 없으면 질문만
        if context and str(context).strip():
            input_part = f"컨텍스트:\n{context}\n\n질문: {question}"
        else:
            input_part = f"질문: {question}"

        # 프롬프트 포맷팅 (instruction=sys_inst, input=input_part, response=answer)
        text = kanana_prompt.format(sys_inst, input_part, answer) + EOS_TOKEN
        texts.append(text)

    return {"text": texts}


def tokenize_function(examples, tokenizer):
    out = tokenizer(
        examples["text"],
        truncation=True,
        max_length=2048,
        padding=False,          # 패딩은 collator에서 동적으로
        return_attention_mask=True,
    )
    # causal LM: 라벨은 입력 복사 (단순 리스트로 변환)
    out["labels"] = out["input_ids"].copy()
    return out

def prepare_dataset(dataset, tokenizer):
    """데이터셋 전처리"""
    print("데이터셋 전처리 중...")
    
    # 프롬프트 포맷팅
    formatted_dataset = dataset.map(
        lambda x: formatting_prompts_func(x, tokenizer),
        batched=True,
        remove_columns=dataset.column_names
    )
    
    # 토크나이징 (패딩 없이)
    tokenized_dataset = formatted_dataset.map(
        lambda x: tokenize_function(x, tokenizer),
        batched=True,
        remove_columns=formatted_dataset.column_names
    )
    
    print("데이터셋 전처리 완료")
    return tokenized_dataset

def setup_lora(model):
    """LoRA 설정"""
    print("LoRA 설정 중...")
    
    lora_config = LoraConfig(
        task_type="CAUSAL_LM",
        r=LORA_CONFIG["r"],
        lora_alpha=LORA_CONFIG["lora_alpha"],
        lora_dropout=LORA_CONFIG["lora_dropout"],
        target_modules=LORA_CONFIG["target_modules"]
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    print("LoRA 설정 완료")
    return model

from transformers import DataCollatorForLanguageModeling

def create_trainer(model, train_dataset, eval_dataset, tokenizer):
    """트레이너 생성"""
    print("트레이너 설정 중...")
    
    # 데이터 콜레이터 설정 (패딩 처리)
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  # Causal LM이므로 False
    )
    
    training_args = TrainingArguments(
        output_dir="./kanana-out",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        max_steps=60,
        learning_rate=2e-4,
        bf16=True,
        logging_steps=1,
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=1234,
        remove_unused_columns=False,
        # 평가 및 저장 설정 추가
        evaluation_strategy="steps",
        save_strategy="steps",
        save_steps=30,
        eval_steps=30,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to="none"
    )

    trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator,)
    
    
    print("트레이너 설정 완료")
    return trainer

def print_gpu_info():
    """GPU 정보 출력"""
    if torch.cuda.is_available():
        gpu_stats = torch.cuda.get_device_properties(0)
        max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
        print(f"GPU = {gpu_stats.name}. Max memory = {max_memory} GB.")
        print(f"CUDA 버전: {torch.version.cuda}")
        print(f"cuDNN 버전: {torch.backends.cudnn.version()}")
    else:
        print("CUDA를 사용할 수 없습니다.")

def main():
    """메인 함수"""
    print("=== Hyundai Kanana 모델 파인튜닝 시작 ===")
    
    # GPU 정보 출력
    print_gpu_info()
    
    # 시작 시간 기록
    start_time = time.time()
    
    # 시작 시 GPU 메모리 기록
    if torch.cuda.is_available():
        start_gpu_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
        print(f"시작 시 예약된 GPU 메모리: {start_gpu_memory} GB")
    
    try:
        # 1. 모델과 토크나이저 로드
        model, tokenizer = load_model_and_tokenizer()
        
        # 2. 데이터셋 로드
        dataset = load_dataset_from_hf()
        
        # 3. 데이터셋 전처리
        train_dataset = prepare_dataset(dataset['train'], tokenizer)
        eval_dataset = prepare_dataset(dataset['test'], tokenizer)
        
        # 4. LoRA 설정
        model = setup_lora(model)
        
        # 5. 트레이너 생성
        trainer = create_trainer(model, train_dataset, eval_dataset, tokenizer)
        
        # 6. 모델 훈련
        print("모델 훈련 시작...")
        trainer_stats = trainer.train()
        
        # 7. 모델 저장
        print("모델 저장 중...")
        trainer.save_model()
        tokenizer.save_pretrained(OUTPUT_DIR)
        
        # 8. 훈련 통계 출력
        training_time = trainer_stats.metrics['train_runtime']
        print(f"훈련 완료!")
        print(f"훈련 시간: {training_time:.2f}초 ({training_time/60:.2f}분)")
        
        # 9. 최종 메모리 사용량
        if torch.cuda.is_available():
            final_gpu_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
            gpu_stats = torch.cuda.get_device_properties(0)
            max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
            
            used_memory_for_training = final_gpu_memory - start_gpu_memory
            print(f"최종 예약된 GPU 메모리: {final_gpu_memory} GB")
            print(f"훈련에 사용된 GPU 메모리: {used_memory_for_training} GB")
            print(f"최대 메모리 대비 사용률: {final_gpu_memory/max_memory*100:.1f}%")
        
        print(f"모델이 {OUTPUT_DIR}에 저장되었습니다.")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        raise
    
    finally:
        # 총 실행 시간
        total_time = time.time() - start_time
        print(f"총 실행 시간: {total_time:.2f}초 ({total_time/60:.2f}분)")

if __name__ == "__main__":
    main()

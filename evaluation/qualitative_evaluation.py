# -*- coding: utf-8 -*-
"""
(수정-v5) 베이스 모델과 파인튜닝된 모델의 답변 품질을 정성적으로 비교 평가하기 위한 스크립트.

변경 사항:
- 최종 목표인 '새로운 디자인 생성' 능력에 초점을 맞춤.
- 창의적인 컨셉을 제시하고, 그에 맞는 구체적인 디자인 요소를 '생성'하도록 유도하는 질문으로 구성.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import pandas as pd
from tqdm import tqdm

# --- 설정 ---
BASE_MODEL_PATH = "../exaone_4.0_1.2b"
ADAPTER_PATH = "../llm_finetuned_model"
OUTPUT_MD_PATH = "./qualitative_comparison_v5.md"

# 새로운 디자인을 '생성'하는 능력을 평가하기 위한 질문 목록
QUESTIONS = [
    # --- 컨셉 기반 신규 디자인 생성 ---
    "'한국의 전통적인 한옥과 수묵화'를 컨셉으로 제네시스 G90의 새로운 스페셜 에디션 모델을 디자인해줘. 특히 크레스트 그릴, 휠, 실내 내장재의 디자인이 어떻게 바뀔지 구체적으로 묘사해줘.",
    "2050년 미래 해양 도시를 탐험하기 위한 '현대 포세이돈'이라는 이름의 수륙양용 SUV를 상상해서 디자인해줘. 공기역학적인 차체, 잠수 모드를 위한 헤드라이트, 물 속 추진을 위한 휠의 변형 디자인을 중심으로.",
    
    # --- 특정 디자인 요소의 창의적 융합 및 재해석 ---
    "현대자동차의 '파라메트릭 픽셀'과 제네시스의 '두 줄' 디자인을 융합해서, 새로운 전기 스포츠카의 테일램프 디자인을 만들어줘. 어떤 모양일지 아주 상세하게 설명해줘.",
    
    # --- 브랜드 아이덴티티 기반의 새로운 모델 생성 ---
    "현대의 고성능 'N' 브랜드에서 최초의 오프로드용 픽업트럭을 만든다면 어떤 모습일까? 'N' 브랜드의 상징색, 공격적인 범퍼 디자인, 그리고 거친 지형을 위한 타이어와 휠 디자인을 구체적으로 설명해줘."
]

def load_model(model_path, adapter_path=None):
    """모델과 토크나이저를 로드하는 통합 함수"""
    print(f"모델 로드 중: {model_path}" + (f" + {adapter_path}" if adapter_path else ""))
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        trust_remote_code=True,
        device_map="auto",
        torch_dtype=torch.bfloat16
    )
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    if adapter_path:
        model = PeftModel.from_pretrained(model, adapter_path)
        model = model.merge_and_unload()
        print("✅ 파인튜닝 모델 로드 및 병합 완료")
    else:
        print("✅ 베이스 모델 로드 완료")
        
    return model, tokenizer

def generate_answer(model, tokenizer, question):
    """주어진 모델과 질문으로 답변을 생성하는 함수"""
    messages = [{"role": "user", "content": question}]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    
    try:
        input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(model.device)
        
        # 창의적이고 상세한 생성을 위해 옵션 유지
        output = model.generate(
            input_ids, 
            max_new_tokens=512, 
            do_sample=True, 
            temperature=0.8,
            top_p=0.9,
            eos_token_id=tokenizer.eos_token_id,
            repetition_penalty=1.1 # 반복을 줄여 좀 더 창의적인 결과 유도
        )
        
        full_text = tokenizer.decode(output[0], skip_special_tokens=True)
        answer = full_text.split("assistant\n")[1].strip() if "assistant\n" in full_text else full_text

        answer = answer.replace("\n", "<br>").replace("|", "&#124;")
        return answer
    except Exception as e:
        return f"답변 생성 중 오류 발생: {str(e)}"

def main():
    """메인 실행 함수"""
    base_model, tokenizer = load_model(BASE_MODEL_PATH)
    base_answers = []
    print("\n--- 베이스 모델 답변 생성 시작 ---")
    for q in tqdm(QUESTIONS, desc="베이스 모델"):
        base_answers.append(generate_answer(base_model, tokenizer, q))
    del base_model
    torch.cuda.empty_cache()

    ft_model, tokenizer = load_model(BASE_MODEL_PATH, ADAPTER_PATH)
    ft_answers = []
    print("\n--- 파인튜닝 모델 답변 생성 시작 ---")
    for q in tqdm(QUESTIONS, desc="파인튜닝 모델"):
        ft_answers.append(generate_answer(ft_model, tokenizer, q))
    del ft_model
    torch.cuda.empty_cache()

    print(f"\n--- 결과를 {OUTPUT_MD_PATH} 파일로 저장 중 ---")
    with open(OUTPUT_MD_PATH, 'w', encoding='utf-8') as f:
        f.write("# 모델별 답변 정성 평가 (v5 - 창의적 디자인 생성 중심)\n\n")
        f.write("| 질문 (Creative Brief) | 베이스 모델 답변 (Base Model) | 파인튜닝 모델 답변 (Finetuned Model) |\n")
        f.write("|---|---|---|")
        for i in range(len(QUESTIONS)):
            f.write(f"| {QUESTIONS[i]} | {base_answers[i]} | {ft_answers[i]} |\n")

    print(f"✅ 정성 평가용 데이터 생성이 완료되었습니다. '{OUTPUT_MD_PATH}' 파일을 확인해주세요.")

if __name__ == "__main__":
    main()

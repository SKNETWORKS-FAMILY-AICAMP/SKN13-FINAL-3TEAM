# -*- coding: utf-8 -*-
"""
(수정-v3) 정량 평가 스크립트.

변경 사항:
- F1-Score 외에 Precision, Recall 점수를 모두 결과에 포함하여 다각적인 분석이 가능하도록 함.
- 최종 보고서에 세 가지 지표(P, R, F1)를 모두 나란히 비교하여 모델의 성향을 파악하기 용이하게 함.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import json
import bert_score
import pandas as pd
from tqdm import tqdm

# --- 공통 설정 ---
BASE_MODEL_PATH = "../exaone_4.0_1.2b"
ADAPTER_PATH = "../llm_finetuned_model"
TEST_DATA_PATH = './test.jsonl'
OUTPUT_MD_PATH = "./quantitative_side_by_side_evaluation_v2.md"

def evaluate_model(model_name, model, tokenizer, data):
    """주어진 모델에 대해 평가를 수행하고 결과 데이터프레임을 반환하는 함수"""
    print(f"\n--- [{model_name}] 모델 답변 생성 시작 ---")
    
    predictions, references, questions = [], [], []

    for item in tqdm(data, desc=f"평가 중 [{model_name}]"):
        question = item['messages'][0]['content']
        reference_answer = item['messages'][1]['content']
        
        messages = [{"role": "user", "content": question}]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        
        input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(model.device)
        
        output = model.generate(
            input_ids, max_new_tokens=256, do_sample=False, eos_token_id=tokenizer.eos_token_id
        )
        
        full_text = tokenizer.decode(output[0], skip_special_tokens=True)
        answer = full_text.split("assistant\n")[1].strip() if "assistant\n" in full_text else full_text

        predictions.append(answer)
        references.append(reference_answer)
        questions.append(question)

    print(f"--- [{model_name}] BERTScore 계산 중 ---")
    bert_p, bert_r, bert_f1 = bert_score.score(
        predictions, references, lang="ko", model_type="bert-base-multilingual-cased", verbose=False
    )
    
    df = pd.DataFrame({
        "Question": questions,
        f"{model_name}_Answer": predictions,
        f"{model_name}_Precision": bert_p.tolist(),
        f"{model_name}_Recall": bert_r.tolist(),
        f"{model_name}_F1_Score": bert_f1.tolist(),
        "Reference Answer": references
    })
    print(f"✅ [{model_name}] 평가 완료")
    return df

def main():
    """메인 실행 함수"""
    with open(TEST_DATA_PATH, 'r', encoding='utf-8') as f:
        test_data = [json.loads(line) for line in f if line.strip()]
    print(f"✅ 총 {len(test_data)}개의 평가 데이터를 로드했습니다.")

    # --- 모델 평가 ---
    base_model, tokenizer = AutoModelForCausalLM.from_pretrained(BASE_MODEL_PATH, trust_remote_code=True, device_map="auto", torch_dtype=torch.bfloat16), AutoTokenizer.from_pretrained(BASE_MODEL_PATH)
    base_results_df = evaluate_model("Base", base_model, tokenizer, test_data)
    del base_model
    torch.cuda.empty_cache()

    base_model_for_peft = AutoModelForCausalLM.from_pretrained(BASE_MODEL_PATH, trust_remote_code=True, device_map="auto", torch_dtype=torch.bfloat16)
    finetuned_model = PeftModel.from_pretrained(base_model_for_peft, ADAPTER_PATH).merge_and_unload()
    ft_results_df = evaluate_model("Finetuned", finetuned_model, tokenizer, test_data)
    del base_model_for_peft, finetuned_model
    torch.cuda.empty_cache()

    # --- 결과 병합 및 저장 ---
    comparison_df = pd.merge(base_results_df, ft_results_df, on=["Question", "Reference Answer"])
    
    # 컬럼 순서 재정렬
    comparison_df = comparison_df[[
        "Question", "Reference Answer", 
        "Base_Answer", "Base_Precision", "Base_Recall", "Base_F1_Score",
        "Finetuned_Answer", "Finetuned_Precision", "Finetuned_Recall", "Finetuned_F1_Score"
    ]]

    # 전체 평균 점수 계산
    avg_scores_text = "| Metric | Base Model | Finetuned Model |\n"
    avg_scores_text += "|---|---|---|"
    for metric in ["Precision", "Recall", "F1_Score"]:
        base_avg = comparison_df[f'Base_{metric}'].mean()
        ft_avg = comparison_df[f'Finetuned_{metric}'].mean()
        avg_scores_text += f"| **{metric}** | {base_avg:.4f} | {ft_avg:.4f} |\n"

    print("\n--- 전체 평균 점수 ---")
    print(avg_scores_text)

    # Markdown 파일로 저장
    with open(OUTPUT_MD_PATH, 'w', encoding='utf-8') as f:
        f.write("# 정량 평가 비교 (P, R, F1) (v2)\n\n")
        f.write("## 전체 평균 점수\n\n")
        f.write(avg_scores_text)
        f.write("\n\n## 개별 결과 비교\n\n")
        f.write(comparison_df.to_markdown(index=False))

    print(f"\n✅ 비교 평가 결과가 '{OUTPUT_MD_PATH}' 파일에 저장되었습니다.")

if __name__ == "__main__":
    main()
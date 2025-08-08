from textwrap import dedent
import json
import os

prompt = dedent("""
Question:{question}

Context:{context}

Instruction:
질문, 문맥(context), 그리고 답(Answer)이 주어졌을 때, 해당 답변에 대한 논리적 근거(Reasoning)를 작성하세요.
다음의 포맷을 반드시 지켜주세요:
##Reason: {{reason}}
##Answer: {{answer}}
""")

from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "LGAI-EXAONE/EXAONE-4.0-1.2B"

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="bfloat16",
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

json_path = "현대 디자인 모토.json"
if os.path.exists(json_path):
    with open(json_path, encoding="utf-8") as f:
        try:
            datas = json.load(f)
        except:
            print(f"{json_path}에서 json 로딩 실패!!")

for data in datas:
    print(f"주어진 Context : \n", context)
    context = data["context"]
    messages = data["messages"]
    for message in messages:
        if message["role"] == "user":
            question = message["content"]
            messages = [
                {"role": "user", "content": prompt.format({"question":question, "context":context})}
            ]
            input_ids = tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt"
            )

            output = model.generate(
                input_ids.to(model.device),
                max_new_tokens=128,
                do_sample=False,
            )
            print(f"주어진 Question : \n", question)
            print(f"생성된 Answer : \n", tokenizer.decode(output[0]))

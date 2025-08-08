import openai
import json
import time
from dotenv import load_dotenv
import re
from pypdf import PdfReader

load_dotenv()

model_name = "gpt-4o"

# 1. 하이픈 기준 청크 분할
def split_by_hyphen(text, delim="----------------------------------------"):
    return [c.strip() for c in text.split(delim) if c.strip()]

def split_by_topic(text):
    splitters = ["요 약", "서 론", "실험 설정", "실험 및 결과", "1. 차체 측면 형태에 따른 공력 성능 비교", "2. 차체 측면 유리창 각도에 따른 공력 성능 비교", "3. 엔진 후드의 각도 변화에 따른 공력 성능 비교",\
                "4. 차체의 루프(roof) 각도에 따른 공력 성능 비교", "4. 후방 디퓨저 적용에 따른 공력 성능 변화", "결 론",\
                "2.1 플루이딕 스컬프쳐와 스톰 엣지", "2.2 센슈어스 스포트니스", "3.1 플루이득 스컬프쳐와 스톰엣지 미의식",\
                "3.2 센슈어스 스포트니스 미의식", "4.1 인지된 미의식과 인식적 환원의 차이", "4.2 플루이딕 스컬프쳐와 스톰 엣지의 신경학적 해석",\
                "4.3 센슈어스 스포트니스의 신경학적 해석", "4.3.1 파라메트릭 다이나믹스", "4.3.2 파라메트릭 주얼", "4.3.3. 히든라이팅",\
                "4.3.4 현대자동차 디자인 철학의 신경학적 해석" "REFLECTIONS IN MOTION", "HERITAGE SERIES", "PONY", "COLOR & LIGHT",\
                "MATERIAL", "A JOURNEY"]

    # splitter 기준으로 인덱스 찾기
    indices = []
    for splitter in splitters:
        for match in re.finditer(re.escape(splitter), text):
            indices.append((match.start(), splitter))
    indices.sort()  # 등장 순 정렬

    sections = []
    for i, (start_idx, splitter) in enumerate(indices):
        end_idx = indices[i+1][0] if i+1 < len(indices) else len(text)
        content = text[start_idx:end_idx].strip()
        sections.append(content)

    return sections

# 2. 충실한 답변 생성용 프롬프트
def make_prompt(article_chunk):
    prompt = f"""
너는 자동차 기사로부터 학습용 QA(질문-답변) 데이터셋을 만드는 어시스턴트야.
아래 기사 내용을 바탕으로, 정보가 겹치지 않는 다양한 질문-답변 쌍을 가능한 많이 생성해줘.
각 질문은 한글로, 답변도 한글로 반드시 기사에 근거해서 작성하되,
답변이 가능한 한 충실하고 자세하게(2문장 이상, 핵심+배경+수치/예시 등 포함) 만들어줘.


출력 형식:
Q: (질문)
A: (답변)

기사:
{article_chunk}
"""
    return prompt

# 3. ChatCompletion(v1.x) 함수
def extract_qa_from_chunk(chunk, model_name="gpt-4o", max_tokens=2048, temperature=0.3, retries=3):
    for i in range(retries):
        try:
            response = openai.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": make_prompt(chunk)}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[오류] 재시도 {i+1}: {e}")
            time.sleep(2)
    return "[에러] 추출 실패!"

# 4. QA 텍스트를 messages 배열로 변환
def qa_text_to_messages(qa_text):
    messages = []
    lines = [line.strip() for line in qa_text.split('\n') if line.strip()]
    last_q = None
    for line in lines:
        if line.startswith("Q:"):
            last_q = line[2:].strip()
            messages.append({"role": "user", "content": last_q})
        elif line.startswith("A:") and last_q is not None:
            messages.append({"role": "assistant", "content": line[2:].strip()})
    return messages

# 5. PDF 텍스트 추출
def extract_pdf_text(pdf_path):
    reader = PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages:
        # 각 페이지에서 텍스트 추출
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    return full_text

# 6. 메인 파이프라인
def main(file_name):
    with open(f"./finetuning/{file_name}.txt", "r", encoding="utf-8") as f:
        text = f.read()
    print(f"총 {len(text)}자 텍스트 로드 완료")

    # 하이픈 기준 청크
    chunks = split_by_hyphen(text)
    print(f"총 {len(chunks)}개 chunk로 분할됨!")

    # 반복 QA 추출 및 json 저장
    with open(f"./QA_context/{file_name}.json", "w", encoding="utf-8") as f:
        cnt = 0
        for idx, chunk in enumerate(chunks):
            print(f"[{idx+1}/{len(chunks)}] QA 추출 중...")
            qa_text = extract_qa_from_chunk(chunk, model_name=model_name)
            messages = qa_text_to_messages(qa_text)
            context = chunk
            if messages:
                json_obj = {"messages": messages}
                json_obj2 = {"context": context}
                json_merged = {**json_obj, **json_obj2}
                cnt += len(json_obj["messages"])
                f.write(json.dumps(json_merged, ensure_ascii=False) + "\n")
            time.sleep(1.1)  # API 부하 방지

    print(f"✅ 전체 QA_context {len(chunks)}개 context, 세부 데이터 {cnt}개 저장 완료 → {file_name}.json")

# 7. pdf 용 메인 파이프라인
def main2(file_name):
    # PDF 텍스트 추출
    text = extract_pdf_text(f"./finetuning/{file_name}.txt")
    print(f"총 {len(text)}자 텍스트 로드 완료")

    # 세부 내용 기준 기준 청크
    chunks = split_by_topic(text)
    print(f"총 {len(chunks)}개 chunk로 분할됨!")

    # 반복 QA 추출 및 json 저장
    with open(f"./QA_context/{file_name}.json", "w", encoding="utf-8") as f:
        cnt = 0
        for idx, chunk in enumerate(chunks):
            print(f"[{idx+1}/{len(chunks)}] QA 추출 중...")
            qa_text = extract_qa_from_chunk(chunk, model_name=model_name)
            messages = qa_text_to_messages(qa_text)
            context = chunk
            if messages:
                json_obj = {"messages": messages}
                json_obj2 = {"context": context}
                json_merged = {**json_obj, **json_obj2}
                cnt += len(json_obj["messages"])
                f.write(json.dumps(json_merged, ensure_ascii=False) + "\n")
            time.sleep(1.1)  # API 부하 방지

    print(f"✅ 전체 QA_context {len(chunks)}개 context, 세부 데이터 {cnt}개 저장 완료 → {file_name}.json")

if __name__ == "__main__":
    file_names = ["현대 디자인 모토", "hyundai_journal_articles", "interview_articles", "new_articles", "preview_articles", "total_articles"]
    file_names2 = ["자동차 차체 형태 디자인이 공기역학 성능에 미치는영향에 대한 연구", "현대 모터스튜디오_디자인 관련 문서", "현대자동차 디자인 철학에 내재하는 미의식의 신경학적 해석"]
    # for file in file_names:
    #     main(f"{file}")
    for file in file_names2:
        main2(f"{file}")

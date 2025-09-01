import os
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from tqdm import tqdm
from dotenv import load_dotenv
from textwrap import dedent

# OpenAI API Key 환경변수 세팅
load_dotenv()

# LangChain LLM 세팅 (gpt-4o-mini)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

# 프롬프트 템플릿
prompt = ChatPromptTemplate.from_template(
    dedent("""### Instruction
당신은 텍스트 분석 전문가입니다.
아래 자동차 기사를 "title", "car_name", "category", "tags", "brand"로 나눠서 json 형태로 만들어주세요.

### 주의사항
1. title 은 제목입니다.
2. car_name 은 본문에서 차의 세부 이름을 추출하여 기입하세요. 단, 추출이 불가능한 경우 빈 문자열로 대체합니다.
3. category 는 ["review", "news", "article"] 중 하나로 판단하여 기입하세요.
4. "review"는 고객 리뷰, "news" 는 최신 뉴스 및 동향 등, "article" 은 논문 내용입니다.
5. tags 는 키워드를 리스트 형태로 담습니다. 가능한 많이 추출하세요.
6. brand 는 "현대", "기아", "쌍용" 과 같은 꼴입니다. 단, 추출이 불가능한 경우 빈 문자열로 대체합니다.
7. page_content 는 본문의 내용을 기입합니다.
8. json, ``` 등과 같은 불필요한 문자는 절대 입력하지 않습니다.


### Few Shot

{{
  "metadata": {{
    "title": "현대차, 신형 그랜저 공개…럭셔리 대형세단 시장 공략",
    "car_name": "그랜저",
    "category": "news",
    "tags": ["그랜저", "현대자동차", "신차발표"],
    "brand": "현대"
  }},
  "page_content": "현대차, 신형 그랜저 공개…럭셔리 대형세단 시장 공략\n신형 그랜저가 드디어 공개됐다. 이번 모델은 디자인 혁신과 첨단 기술로 럭셔리 대형세단 시장을 정조준한다.\n태그: 그랜저, 현대자동차, 신차발표"
}},
{{
  "metadata": {{
    "title": "기아 EV6 롱텀 시승기 – 전기차의 새로운 기준",
    "car_name": "EV6",
    "category": "review",
    "tags": ["EV6", "전기차", "시승기", "기아"],
    "brand": "기아"
  }},
  "page_content": "기아 EV6 롱텀 시승기 – 전기차의 새로운 기준\n지난 2주간 기아 EV6를 직접 타보았다. 주행감과 충전 인프라 모두 만족스럽다.\n태그: EV6, 전기차, 시승기, 기아"
}}

### Input Data
{article}""")
)

# 파일명별 카테고리 매핑
file_category_map = {
    "other_issue_articles.txt": "news",
    "other_new_articles.txt": "news",
    "other_preview_articles.txt": "news",
}

def load_existing_json(json_path):
    if os.path.exists(json_path):
        with open(json_path, encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_json(json_path, data):
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def split_articles(text):
    return [a.strip() for a in text.split("----------------------------------------") if a.strip()]

def extract_structured_data(article, category):
    formatted_prompt = prompt.invoke({"article":article})
    response = llm.invoke(formatted_prompt)
    # 응답에서 JSON만 추출
    try:
        result = json.loads(response.content)
    except Exception:
        print("답변이 JSON 형식이 아닙니다 !!")
        print(f"response : {response}")
        result = None
    finally:
        return result

def main():
    json_path = "./rag_data.json"
    new_data = ""
    for filename, category in file_category_map.items():
        if not os.path.exists(filename):
            print(f"{filename} 파일을 찾지 못했습니다 !!")
            continue
        with open(filename, encoding="utf-8") as f:
            articles = split_articles(f.read())

            # 누적 계산기
            data_count = len(load_existing_json(json_path))
            articles = articles[data_count+10:]
            print(f"{data_count} 번 째부터 파싱을 시작합니다 !")

            print(f"{filename} → {len(articles)}건 추출")
            for article in tqdm(articles, desc=filename):
                existing_data = load_existing_json(json_path)
                new_data = extract_structured_data(article, category)

                # 파싱 오류 감지
                if not new_data:
                    continue
                
                # 같은 이름 검사
                if any(item.get("metadata").get("title")==new_data.get("metadata").get("title") for item in existing_data):
                    print(f"{filename} 이 이미 존재합니다 !!")
                    continue
                
                # 데이터 추가
                if new_data:
                    existing_data.append(new_data)
                else:
                    continue
                save_json(json_path, existing_data)
    
    print(f"총 {len(existing_data)}건 저장 완료!")

if __name__ == "__main__":
    main()

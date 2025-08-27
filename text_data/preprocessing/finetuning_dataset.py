# hyundai_docs_parse.py
from openai import OpenAI
from dotenv import load_dotenv
from pypdf import PdfReader
from pathlib import Path
import os, re, json, time, unicodedata, uuid

load_dotenv()

# =========================
# 설정
# =========================
MODEL_NAME = "gpt-4o"   # 로컬 LLM이면 base_url로 client 변경 가능
OUT_DIR = Path("./QA_context")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# 유틸
# =========================
def normalize(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    s = unicodedata.normalize("NFKC", s.strip())
    return " ".join(s.split())

def split_by_hyphen(text, delim="----------------------------------------"):
    return [c.strip() for c in text.split(delim) if c.strip()]

def split_by_topic(text):
    splitters = [
        "요 약","서 론","실험 설정","실험 및 결과",
        "1. 차체 측면 형태에 따른 공력 성능 비교",
        "2. 차체 측면 유리창 각도에 따른 공력 성능 비교",
        "3. 엔진 후드의 각도 변화에 따른 공력 성능 비교",
        "4. 차체의 루프(roof) 각도에 따른 공력 성능 비교",
        "4. 후방 디퓨저 적용에 따른 공력 성능 변화",
        "결 론",
        "2.1 플루이딕 스컬프쳐와 스톰 엣지", "2.2 센슈어스 스포트니스",
        "3.1 플루이득 스컬프쳐와 스톰엣지 미의식", "3.2 센슈어스 스포트니스 미의식",
        "4.1 인지된 미의식과 인식적 환원의 차이",
        "4.2 플루이딕 스컬프쳐와 스톰 엣지의 신경학적 해석",
        "4.3 센슈어스 스포트니스의 신경학적 해석",
        "4.3.1 파라메트릭 다이나믹스","4.3.2 파라메트릭 주얼","4.3.3. 히든라이팅",
        "4.3.4 현대자동차 디자인 철학의 신경학적 해석",
        "REFLECTIONS IN MOTION","HERITAGE SERIES","PONY",
        "COLOR & LIGHT","MATERIAL","A JOURNEY"
    ]
    # 인덱스 찾기
    indices = []
    for sp in splitters:
        for m in re.finditer(re.escape(sp), text):
            indices.append((m.start(), sp))
    indices.sort()
    if not indices:
        return [text.strip()] if text.strip() else []

    sections = []
    for i, (start, _) in enumerate(indices):
        end = indices[i+1][0] if i+1 < len(indices) else len(text)
        content = text[start:end].strip()
        if content:
            sections.append(content)
    return sections

def split_by_paragraph(text, min_length=100, max_length=2000):
    """문단 단위로 분할하되, 길이 제한 적용"""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) <= max_length:
            current_chunk += "\n\n" + para if current_chunk else para
        else:
            if current_chunk and len(current_chunk) >= min_length:
                chunks.append(current_chunk)
            current_chunk = para
    
    if current_chunk and len(current_chunk) >= min_length:
        chunks.append(current_chunk)
    
    return chunks

def split_by_sentence(text, min_sentences=2, max_sentences=8):
    """문장 단위로 분할"""
    # 문장 구분자: 마침표, 느낌표, 물음표 + 공백 또는 줄바꿈
    sentences = re.split(r'[.!?]\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    current_chunk = []
    
    for sentence in sentences:
        current_chunk.append(sentence)
        
        if len(current_chunk) >= max_sentences:
            if len(current_chunk) >= min_sentences:
                chunks.append('. '.join(current_chunk) + '.')
            current_chunk = []
    
    # 남은 문장들 처리
    if current_chunk and len(current_chunk) >= min_sentences:
        chunks.append('. '.join(current_chunk) + '.')
    
    return chunks

def split_by_qa_format(text):
    """Q&A 형식의 텍스트를 개별 Q&A 쌍으로 분할"""
    # Q. 또는 Q: 로 시작하는 질문 찾기
    qa_pattern = r'Q[.:]\s*(.*?)(?=Q[.:]|$)'
    matches = re.findall(qa_pattern, text, re.DOTALL)
    
    chunks = []
    for match in matches:
        if match.strip():
            chunks.append(match.strip())
    
    return chunks if chunks else [text]

def split_by_length(text, target_length=1000, overlap=200):
    """고정 길이로 분할하되 중복 허용"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + target_length
        
        # 문장 경계에서 자르기
        if end < len(text):
            # 마침표, 느낌표, 물음표 뒤에서 자르기
            last_period = text.rfind('.', start, end)
            last_exclamation = text.rfind('!', start, end)
            last_question = text.rfind('?', start, end)
            
            best_cut = max(last_period, last_exclamation, last_question)
            if best_cut > start + target_length * 0.7:  # 70% 이상이면 해당 위치에서 자르기
                end = best_cut + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def extract_pdf_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    full = []
    for p in reader.pages:
        t = p.extract_text() or ""
        if t.strip():
            full.append(t)
    return "\n".join(full)

# =========================
# 프롬프트들 (다양한 태스크용)
# =========================

# (A) QA 세트용 프롬프트
QA_PROMPT = """다음 <CONTEXT>에서만 정보를 사용하여, 문서의 핵심 사실을 정확히 겨냥한 학습용 질문-답변 쌍을 3-5개 생성하라.

도메인 초점(자동차·현대자동차 맥락):
- 설계/디자인 철학: 센슈어스 스포트니스, 파라메트릭 픽셀, 파라메트릭 다이나믹스 등
- 공력/성능: 항력계수(Cd), 양력/다운포스, 공력 요소(디퓨저, 스포일러, 에어커튼)
- 차체 비율/형상: 휠베이스, 트랙, 오버행, 벨트라인, 그린하우스, 실루엣(two-box/three-box)
- 조명/전장/섀시: DRL, 헤드램프/테일램프 구조, 서스펜션/브레이크, 휠·타이어 규격
- 수치·일정·버전: 연도/행사/모델, %, mm, kg, kW 등 단위 포함 수치

생성 지침:
- 각 쌍마다 아래 형식을 엄격히 따를 것
- POS_CONTEXTS는 반드시 <CONTEXT>의 문장/구절을 그대로 인용할 것(2~4개)
- NEG_CONTEXTS는 주제상 연관은 있지만 정답을 포함하지 않는 문장/구절을 인용(1~3개)
- UNANSWERABLE이 true일 경우 A는 "답할 수 없습니다"
- PRIMARY_CITATION은 POS_CONTEXTS에서 가장 핵심이 되는 1 기반 인덱스

출력 형식(각 쌍마다 아래 블록 반복, 블록 사이엔 ---):
Q: <질문>
A: <답변 또는 "답할 수 없습니다">
UNANSWERABLE: <true|false>
POS_CONTEXTS:
- <문장1>
- <문장2>
NEG_CONTEXTS:
- <문장1>
- <문장2>
PRIMARY_CITATION: <정수>
---
(필요한 만큼 반복)

<CONTEXT>
{context}
"""

# Negative Question 생성용 프롬프트
NEGATIVE_QA_PROMPT = """다음 <CONTEXT>와 관련은 있지만 정확한 답을 찾을 수 없는 질문들을 생성하라.

생성 지침:
- context의 주제와 관련된 질문이어야 함
- 하지만 context에서 정확한 답을 찾을 수 없어야 함
- 예: 구체적인 수치, 날짜, 모델명, 기술 상세사항 등

출력 형식:
Q1: <관련 있지만 답변 불가능한 질문>
Q2: <관련 있지만 답변 불가능한 질문>
Q3: <관련 있지만 답변 불가능한 질문>
---

<CONTEXT>
{context}
"""

# (B) 정의/용어 사전용 프롬프트
DEFINITION_PROMPT = """다음 <CONTEXT>에서 자동차 디자인과 관련된 주요 용어와 개념들을 추출하여 정의를 작성하라.

추출할 용어 유형:
- 디자인 철학: 플루이딕 스컬프처, 센슈어스 스포트니스, 아트 오브 스틸 등
- 공학 개념: 크럼플 존, 공력학적 요소, 구조 설계 등
- 기술 용어: 파라메트릭 픽셀, DRL, 휠베이스 등

출력 형식:
TERM1: <용어>
DEF1: <정의>
---
TERM2: <용어>
DEF2: <정의>
---
(발견된 용어들만)

<CONTEXT>
{context}
"""

# (C) 요약/하이라이트용 프롬프트
SUMMARY_PROMPT = """다음 <CONTEXT>의 핵심 내용을 요약하여 bullet point로 정리하라.

요약 지침:
- 핵심 사실과 수치를 포함
- 간결하고 명확하게
- 3-7개의 bullet point로 구성

출력 형식:
BULLET1: <첫 번째 요점>
BULLET2: <두 번째 요점>
BULLET3: <세 번째 요점>
---
(3-7개까지)

<CONTEXT>
{context}
"""

# (D) 선호학습 쌍용 프롬프트
PREFERENCE_PROMPT = """다음 <CONTEXT>에서 같은 질문에 대한 정답과 오답 응답 쌍을 생성하라.

생성 지침:
- 질문은 구체적이고 명확하게
- 정답은 context에서 정확히 찾을 수 있는 정보
- 오답은 비슷하지만 잘못된 정보 (수치 변경, 개념 혼동 등)

출력 형식:
QUESTION: <질문>
CHOSEN: <정답>
REJECTED: <오답>
---

<CONTEXT>
{context}
"""

# =========================
# LLM 클라이언트
# =========================

client = OpenAI()  # .env의 OPENAI_API_KEY 사용

def ask_llm(prompt: str, model: str = MODEL_NAME, temperature: float = 0.3, max_tokens: int = 1024, retries=3) -> str:
    """LLM에 질문하고 응답 반환"""
    for i in range(retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role":"user","content":prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            print(f"[경고] LLM 호출 재시도 {i+1}: {e}")
            time.sleep(1.5)
    return ""

def parse_qa_pairs(response: str, context: str) -> list:
    """QA 응답을 파싱하여 리스트로 변환 (positive/negative contexts 및 citation 포함)"""
    qa_pairs = []

    # 블록 분리
    blocks = [b.strip() for b in response.split("---") if b.strip()]
    for block in blocks:
        lines = [normalize(l) for l in block.split("\n") if l.strip()]
        if not lines:
            continue

        question = None
        answer = None
        unanswerable = False
        pos_contexts = []
        neg_contexts = []
        primary_idx = None

        mode = None  # 'pos' | 'neg' | None

        for line in lines:
            # 섹션 헤더 처리
            if line.startswith("POS_CONTEXTS:"):
                mode = 'pos'
                continue
            if line.startswith("NEG_CONTEXTS:"):
                mode = 'neg'
                continue

            if line.startswith("Q:"):
                question = normalize(line.split(":", 1)[1].strip())
                mode = None
                continue
            if line.startswith("A:"):
                answer = normalize(line.split(":", 1)[1].strip())
                mode = None
                continue
            if line.startswith("UNANSWERABLE:"):
                val = line.split(":", 1)[1].strip().lower()
                unanswerable = val in ("true", "yes", "1")
                mode = None
                continue
            if line.startswith("PRIMARY_CITATION:"):
                try:
                    primary_idx = int(line.split(":", 1)[1].strip())
                except Exception:
                    primary_idx = None
                mode = None
                continue

            # 목록 항목 처리
            if mode == 'pos' and line.startswith("-"):
                pos_contexts.append(normalize(line[1:].strip()))
                continue
            if mode == 'neg' and line.startswith("-"):
                neg_contexts.append(normalize(line[1:].strip()))
                continue

        if not question:
            continue
        if unanswerable:
            answer = "답할 수 없습니다"
            pos_contexts = []  # 답불가면 양의 근거 없음
            primary_idx = None
        else:
            # 기본값 보정
            if not answer:
                continue
            if not pos_contexts:
                # 최소한 전체 context 중 한 문장이라도 넣어 방어
                sample = context[:300]
                pos_contexts = [sample]
                primary_idx = 1
            if primary_idx is None or primary_idx < 1 or primary_idx > len(pos_contexts):
                primary_idx = 1

        qa_pairs.append({
            "id": str(uuid.uuid4())[:8],
            "question": question,
            "answer": answer,
            "context": context,
            "unanswerable": unanswerable,
            "pos_contexts": pos_contexts,
            "neg_contexts": neg_contexts,
            "primary_idx": primary_idx
        })

    return qa_pairs

def parse_definitions(response: str, context: str, source: str) -> list:
    """정의 응답을 파싱하여 리스트로 변환"""
    definitions = []
    sections = response.split("---")
    
    for section in sections:
        if not section.strip():
            continue
            
        lines = [normalize(l) for l in section.split("\n") if l.strip()]
        term, definition = None, None
        
        for line in lines:
            if line.startswith("TERM"):
                term = normalize(line.split(":", 1)[1].strip())
            elif line.startswith("DEF"):
                definition = normalize(line.split(":", 1)[1].strip())
        
        if term and definition:
            definitions.append({
                "term": term,
                "definition": definition,
                "source": source
            })
    
    return definitions

def parse_summaries(response: str, context: str, doc_id: str) -> list:
    """요약 응답을 파싱하여 리스트로 변환"""
    summaries = []
    sections = response.split("---")
    
    for section in sections:
        if not section.strip():
            continue
            
        lines = [normalize(l) for l in section.split("\n") if l.strip()]
        bullets = []
        
        for line in lines:
            if line.startswith("BULLET"):
                bullet = normalize(line.split(":", 1)[1].strip())
                bullets.append(bullet)
        
        if bullets:
            summaries.append({
                "doc_id": doc_id,
                "section": "main",
                "bullets": bullets
            })
    
    return summaries

def parse_preferences(response: str, context: str) -> list:
    """선호학습 쌍 응답을 파싱하여 리스트로 변환"""
    preferences = []
    sections = response.split("---")
    
    for section in sections:
        if not section.strip():
            continue
            
        lines = [normalize(l) for l in section.split("\n") if l.strip()]
        question, chosen, rejected = None, None, None
        
        for line in lines:
            if line.startswith("QUESTION"):
                question = normalize(line.split(":", 1)[1].strip())
            elif line.startswith("CHOSEN"):
                chosen = normalize(line.split(":", 1)[1].strip())
            elif line.startswith("REJECTED"):
                rejected = normalize(line.split(":", 1)[1].strip())
        
        if question and chosen and rejected:
            preferences.append({
                "prompt": question,
                "chosen": chosen,
                "rejected": rejected
            })
    
    return preferences

# =========================
# 데이터셋 생성 함수들
# =========================

def generate_qa_dataset(chunks: list, source: str) -> list:
    """QA 데이터셋 생성 (Answerable + Unanswerable 혼합, positive/negative contexts 포함)"""
    qa_dataset = []

    for i, chunk in enumerate(chunks):
        ctx = normalize(chunk)
        if not ctx:
            continue

        prompt = QA_PROMPT.format(context=ctx)
        response = ask_llm(prompt)
        qa_pairs = parse_qa_pairs(response, ctx)

        for qa in qa_pairs:
            # POS/NEG contexts를 id 부여하여 정규화
            positive_items = []
            for idx, txt in enumerate(qa.get("pos_contexts", []), start=1):
                positive_items.append({"id": f"D{i}-P{idx}", "text": txt})
            negative_items = []
            for idx, txt in enumerate(qa.get("neg_contexts", []), start=1):
                negative_items.append({"id": f"D{i}-N{idx}", "text": txt})

            # citation 선택
            citations = []
            if not qa["unanswerable"] and positive_items:
                primary = qa.get("primary_idx") or 1
                primary = max(1, min(primary, len(positive_items)))
                citations = [positive_items[primary - 1]["id"]]

            qa_dataset.append({
                "id": f"{source}_{qa['id']}",
                "question": qa["question"],
                "contexts": {
                    "positive": positive_items,
                    "negative": negative_items
                },
                "answer": qa["answer"],
                "citations": citations,
                "unanswerable": qa["unanswerable"]
            })

        print(f"  - chunk {i+1}/{len(chunks)} → {len(qa_pairs)}개 QA 쌍 생성")
        time.sleep(1.1)

    return qa_dataset

def generate_definition_dataset(chunks: list, source: str) -> list:
    """정의 데이터셋 생성"""
    definition_dataset = []
    
    for i, chunk in enumerate(chunks):
        ctx = normalize(chunk)
        if not ctx:
            continue
            
        prompt = DEFINITION_PROMPT.format(context=ctx)
        response = ask_llm(prompt)
        definitions = parse_definitions(response, ctx, source)
        
        for definition in definitions:
            definition_dataset.append(definition)
        
        print(f"  - chunk {i+1}/{len(chunks)} → {len(definitions)}개 정의 생성")
        time.sleep(1.1)
    
    return definition_dataset

def generate_summary_dataset(chunks: list, doc_id: str) -> list:
    """요약 데이터셋 생성"""
    summary_dataset = []
    
    for i, chunk in enumerate(chunks):
        ctx = normalize(chunk)
        if not ctx:
            continue
            
        prompt = SUMMARY_PROMPT.format(context=ctx)
        response = ask_llm(prompt)
        summaries = parse_summaries(response, ctx, doc_id)
        
        for summary in summaries:
            summary_dataset.append(summary)
        
        print(f"  - chunk {i+1}/{len(chunks)} → {len(summaries)}개 요약 생성")
        time.sleep(1.1)
    
    return summary_dataset

def generate_preference_dataset(chunks: list) -> list:
    """선호학습 데이터셋 생성"""
    preference_dataset = []
    
    for i, chunk in enumerate(chunks):
        ctx = normalize(chunk)
        if not ctx:
            continue
            
        prompt = PREFERENCE_PROMPT.format(context=ctx)
        response = ask_llm(prompt)
        preferences = parse_preferences(response, ctx)
        
        for preference in preferences:
            preference_dataset.append(preference)
        
        print(f"  - chunk {i+1}/{len(chunks)} → {len(preferences)}개 선호쌍 생성")
        time.sleep(1.1)
    
    return preference_dataset

# =========================
# 저장 함수들
# =========================

def save_qa_dataset(dataset: list, filename: str):
    """QA 데이터셋을 JSONL 형식으로 저장"""
    out_path = OUT_DIR / f"{filename}_qa.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"[QA] 저장 완료: {out_path} ({len(dataset)}개)")

def save_definition_dataset(dataset: list, filename: str):
    """정의 데이터셋을 JSONL 형식으로 저장"""
    out_path = OUT_DIR / f"{filename}_definitions.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"[DEF] 저장 완료: {out_path} ({len(dataset)}개)")

def save_summary_dataset(dataset: list, filename: str):
    """요약 데이터셋을 JSONL 형식으로 저장"""
    out_path = OUT_DIR / f"{filename}_summaries.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"[SUM] 저장 완료: {out_path} ({len(dataset)}개)")

def save_preference_dataset(dataset: list, filename: str):
    """선호학습 데이터셋을 JSONL 형식으로 저장"""
    out_path = OUT_DIR / f"{filename}_preferences.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"[PREF] 저장 완료: {out_path} ({len(dataset)}개)")

# =========================
# 메인 파이프라인: TXT 소스
# =========================
def main_txt(file_name: str, chunking_method="paragraph", task_types=None):
    if task_types is None:
        task_types = ["qa", "definitions", "summaries", "preferences"]
    
    src = Path(f"./finetuning/{file_name}.txt")
    if not src.exists():
        raise FileNotFoundError(f"입력 텍스트 없음: {src}")
    text = src.read_text(encoding="utf-8")
    print(f"[TXT] 총 {len(text)}자 로드")

    # chunking 방법 선택
    if chunking_method == "hyphen":
        chunks = split_by_hyphen(text)
    elif chunking_method == "paragraph":
        chunks = split_by_paragraph(text)
    elif chunking_method == "sentence":
        chunks = split_by_sentence(text)
    elif chunking_method == "qa_format":
        chunks = split_by_qa_format(text)
    elif chunking_method == "length":
        chunks = split_by_length(text)
    else:
        chunks = split_by_hyphen(text)
    
    print(f"[TXT] {len(chunks)}개 청크 ({chunking_method} 방식)")

    # 태스크별 데이터셋 생성
    if "qa" in task_types:
        qa_dataset = generate_qa_dataset(chunks, file_name)
        save_qa_dataset(qa_dataset, file_name)
    
    if "definitions" in task_types:
        definition_dataset = generate_definition_dataset(chunks, file_name)
        save_definition_dataset(definition_dataset, file_name)
    
    if "summaries" in task_types:
        summary_dataset = generate_summary_dataset(chunks, file_name)
        save_summary_dataset(summary_dataset, file_name)
    
    if "preferences" in task_types:
        preference_dataset = generate_preference_dataset(chunks)
        save_preference_dataset(preference_dataset, file_name)

# =========================
# 메인 파이프라인: PDF 소스
# =========================
def main_pdf(file_name: str, chunking_method="topic", task_types=None):
    if task_types is None:
        task_types = ["qa", "definitions", "summaries", "preferences"]
    
    src = Path(f"./finetuning/{file_name}.pdf")
    if not src.exists():
        raise FileNotFoundError(f"입력 PDF 없음: {src}")
    text = extract_pdf_text(str(src))
    print(f"[PDF] 총 {len(text)}자 로드")

    # chunking 방법 선택
    if chunking_method == "topic":
        chunks = split_by_topic(text)
    elif chunking_method == "paragraph":
        chunks = split_by_paragraph(text)
    elif chunking_method == "sentence":
        chunks = split_by_sentence(text)
    elif chunking_method == "length":
        chunks = split_by_length(text)
    else:
        chunks = split_by_topic(text)
    
    print(f"[PDF] {len(chunks)}개 섹션 ({chunking_method} 방식)")

    # 태스크별 데이터셋 생성
    if "qa" in task_types:
        qa_dataset = generate_qa_dataset(chunks, file_name)
        save_qa_dataset(qa_dataset, file_name)
    
    if "definitions" in task_types:
        definition_dataset = generate_definition_dataset(chunks, file_name)
        save_definition_dataset(definition_dataset, file_name)
    
    if "summaries" in task_types:
        summary_dataset = generate_summary_dataset(chunks, file_name)
        save_summary_dataset(summary_dataset, file_name)
    
    if "preferences" in task_types:
        preference_dataset = generate_preference_dataset(chunks)
        save_preference_dataset(preference_dataset, file_name)

# =========================
# 실행부
# =========================
if __name__ == "__main__":
    # 파일별 최적화된 설정
    files_config = [
        # 논문/연구 → paragraph/sentence chunk + 요약/QA
        ("자동차 차체 형태 디자인이 공기역학 성능에 미치는영향에 대한 연구", "pdf","length", ["qa", "summaries"]),
        ("현대자동차 디자인 철학에 내재하는 미의식의 신경학적 해석", "pdf", "topic", ["qa", "summaries"]),
        
        # 디자인 철학/브랜드 스토리 → paragraph + 정의 세트
        ("현대 디자인 모토", "txt", "paragraph", ["qa", "definitions"]),
        ("현대 모터스튜디오_디자인 관련 문서", "pdf", "paragraph", ["qa", "definitions"]),
        
        # 프리뷰/뉴스 기사 → sentence chunk + QA
        ("new_articles", "txt", "sentence", ["qa", "preferences"]),
        ("preview_articles", "txt", "sentence", ["qa", "preferences"]),
        ("total_articles", "txt", "length", ["qa", "preferences"]),
        
        # 인터뷰 → qa_format chunk 그대로 QA
        ("hyundai_journal_articles", "txt", "qa_format", ["qa"]),
        ("interview_articles", "txt", "qa_format", ["qa"]),
        
        # 기타
        ("자동차의 뼈대 차체 및 구조 설계의 모든 것", "txt", "paragraph", ["qa", "definitions"])
    ]

    for file_name, file_type, chunking_method, task_types in files_config:
        print(f"\n{'='*60}")
        print(f"처리 중: {file_name}")
        print(f"{'='*60}")
        
        if file_type == "pdf":
            main_pdf(file_name, chunking_method, task_types)
        else:
            main_txt(file_name, chunking_method, task_types)

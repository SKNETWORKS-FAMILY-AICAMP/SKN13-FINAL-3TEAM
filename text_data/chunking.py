from pypdf import PdfReader
from pathlib import Path
import os, re, json, time, unicodedata, uuid
import pandas as pd

# OCR 및 띄어쓰기 도구 import
try:
    from pykospacing import Spacing
    PYKOSPACING_AVAILABLE = True
except ImportError:
    PYKOSPACING_AVAILABLE = False
    print("[경고] pykospacing이 설치되지 않았습니다. pip install pykospacing으로 설치하세요.")

try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("[경고] OCR 도구가 설치되지 않았습니다. pip install pytesseract pdf2image로 설치하세요.")

OUT_DIR = Path("./chunking_result")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# 자동차 전문 용어 사전 (띄어쓰기 예외)
# =========================
AUTOMOTIVE_TERMS = [
    # 현대자동차 디자인 용어
    "센슈어스스포티니스", "플루이딕스컬프처", "파라메트릭픽셀", "파라메트릭다이나믹스",
    "아트오브스틸", "라이트아키텍처", "퍼니쉬드캄스페이스", "코리아니즘",
    
    # 차량 모델명
    "아이오닉5", "아이오닉6", "아이오닉9", "넥쏘", "그랜저", "쏘나타", "산타페",
    "캐스퍼", "베뉴", "스타리아", "팰리세이드", "투싼", "코나", "아반떼",
    
    # 기술 용어
    "크럼플존", "휠베이스", "오버행", "벨트라인", "그린하우스", "디퓨저", "스포일러",
    "에어커튼", "DRL", "헤드램프", "테일램프", "서스펜션", "브레이크",
    
    # 성능 지표
    "Cd", "Cd값", "항력계수", "양력", "다운포스", "공력성능",
    
    # 단위
    "kWh", "km", "mm", "kg", "kW", "Nm", "rpm", "mph", "kmh"
]

# =========================
# PDF 전처리 함수들
# =========================

def fix_spacing_with_pykospacing(text: str) -> str:
    """pykospacing을 사용한 정확한 띄어쓰기 처리"""
    if not PYKOSPACING_AVAILABLE:
        print("[경고] pykospacing을 사용할 수 없어 기본 띄어쓰기 처리로 대체합니다.")
        return fix_spacing_issues(text)
    
    try:
        # 자동차 전문 용어를 예외로 설정
        spacing = Spacing(rules=AUTOMOTIVE_TERMS)
        return spacing(text)
    except Exception as e:
        print(f"[경고] pykospacing 처리 실패: {e}")
        return fix_spacing_issues(text)

def fix_spacing_issues(text: str) -> str:
    """기본 띄어쓰기 문제 해결 (pykospacing 없을 때)"""
    # 한글 자모 사이 띄어쓰기 추가
    text = re.sub(r'([가-힣])([ㄱ-ㅎㅏ-ㅣ])', r'\1 \2', text)
    
    # 연속된 한글 사이 띄어쓰기 추가 (단어 경계)
    text = re.sub(r'([가-힣])([가-힣]{2,})', r'\1 \2', text)
    
    # 숫자와 한글 사이 띄어쓰기
    text = re.sub(r'(\d)([가-힣])', r'\1 \2', text)
    text = re.sub(r'([가-힣])(\d)', r'\1 \2', text)
    
    # 특수문자 주변 띄어쓰기 정리
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    text = re.sub(r'([,.!?;:])\s*([가-힣])', r'\1 \2', text)
    
    # 연속된 공백 정리
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def remove_tabs_and_formatting(text: str) -> str:
    """탭 문자 제거 및 포맷팅 정리"""
    # 탭을 공백으로 변환
    text = text.replace('\t', ' ')
    
    # 연속된 공백 정리
    text = re.sub(r'\s+', ' ', text)
    
    # 줄바꿈 정리 (단락 구분 유지)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # 불필요한 공백 제거
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+$', '', text, flags=re.MULTILINE)
    
    return text.strip()

def extract_pdf_text_with_ocr(pdf_path: str) -> str:
    """OCR을 사용한 PDF 텍스트 추출"""
    if not OCR_AVAILABLE:
        print("[경고] OCR 도구를 사용할 수 없습니다.")
        return ""
    
    try:
        # PDF를 이미지로 변환
        print(f"[OCR] PDF를 이미지로 변환 중: {pdf_path}")
        images = convert_from_path(pdf_path, dpi=300)
        
        # 각 페이지를 OCR로 텍스트 추출
        texts = []
        for i, image in enumerate(images):
            print(f"[OCR] 페이지 {i+1}/{len(images)} 처리 중...")
            text = pytesseract.image_to_string(image, lang='kor+eng')
            if text.strip():
                texts.append(text)
            time.sleep(0.5)  # OCR 부하 방지
        
        result = "\n\n".join(texts)
        print(f"[OCR] 텍스트 추출 완료: {len(result)}자")
        return result
        
    except Exception as e:
        print(f"[오류] OCR 처리 실패: {pdf_path} - {e}")
        return ""

def extract_pdf_text_with_ocr_fallback(pdf_path: str) -> str:
    """OCR이 필요한 PDF 처리 (기본 추출 실패 시)"""
    try:
        # 기본 PDF 텍스트 추출
        reader = PdfReader(pdf_path)
        full = []
        
        for p in reader.pages:
            t = p.extract_text() or ""
            if t.strip():
                full.append(t)
        
        text = "\n".join(full)
        
        # 텍스트가 너무 적으면 OCR 시도
        if len(text.strip()) < 100:
            print(f"[경고] PDF 텍스트 추출 실패 (OCR 시도): {pdf_path}")
            if OCR_AVAILABLE:
                ocr_text = extract_pdf_text_with_ocr(pdf_path)
                if ocr_text:
                    return ocr_text
                else:
                    print(f"[오류] OCR도 실패했습니다: {pdf_path}")
                    # OCR 실패 시에도 기본 텍스트 반환 (빈 텍스트라도)
                    return text
            else:
                print(f"[경고] OCR 도구가 설치되지 않아 기본 텍스트만 사용: {pdf_path}")
                return text
        
        return text
        
    except Exception as e:
        print(f"[오류] PDF 처리 실패: {pdf_path} - {e}")
        # OCR 시도
        if OCR_AVAILABLE:
            return extract_pdf_text_with_ocr(pdf_path)
        else:
            print(f"[경고] OCR 도구가 설치되지 않아 빈 텍스트 반환: {pdf_path}")
            return ""

def preprocess_pdf_text(text: str, pdf_name: str) -> str:
    """PDF별 특화 전처리"""
    if "자동차 차체 형태 디자인이 공기역학 성능에 미치는영향에 대한 연구" in pdf_name:
        # pykospacing을 사용한 정확한 띄어쓰기
        text = fix_spacing_with_pykospacing(text)
        print(f"[전처리] pykospacing 띄어쓰기 수정 완료")
        
    elif "현대 모터스튜디오_디자인 관련 문서" in pdf_name:
        # 탭 문자 제거
        text = remove_tabs_and_formatting(text)
        print(f"[전처리] 탭 문자 제거 완료")
        
    elif "현대자동차 디자인 철학에 내재하는 미의식의 신경학적 해석" in pdf_name:
        # OCR 문제 - 더 강력한 전처리 시도
        text = remove_tabs_and_formatting(text)
        
        # 텍스트가 너무 적으면 추가 처리
        if len(text.strip()) < 100:
            print(f"[경고] OCR 문제로 텍스트 추출 실패 - 수동 처리 필요")
            # 최소한의 텍스트라도 보존
            if text.strip():
                print(f"[정보] 추출된 텍스트 길이: {len(text.strip())}자")
                return text
            else:
                print(f"[오류] 텍스트 추출 완전 실패")
                return ""
        else:
            print(f"[전처리] 기본 포맷팅 정리 완료 (텍스트 길이: {len(text.strip())}자)")
    
    return text

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
    """PDF 텍스트 추출 + 전처리"""
    text = extract_pdf_text_with_ocr_fallback(pdf_path)
    if text:
        # PDF별 특화 전처리
        pdf_name = Path(pdf_path).name
        text = preprocess_pdf_text(text, pdf_name)
    return text

# =========================
# Chunking 결과 저장 함수들
# =========================

def save_chunks_to_jsonl(chunks: list, filename: str, chunking_method: str, source_file: str, overwrite: bool = False):
    """Chunking 결과를 JSONL 형식으로 저장 (DataFrame 처리용)"""
    out_path = OUT_DIR / f"{filename}_chunks.jsonl"
    
    if out_path.exists() and not overwrite:
        print(f"[SKIP] 파일이 이미 존재합니다: {out_path}")
        return
    
    with out_path.open("w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            chunk_data = {
                "chunk_id": f"{filename}_{i:04d}",
                "source_file": source_file,
                "chunking_method": chunking_method,
                "chunk_index": i,
                "text_length": len(chunk),
                "word_count": len(chunk.split()),
                "chunk_text": chunk
            }
            f.write(json.dumps(chunk_data, ensure_ascii=False) + "\n")
    
    print(f"[CHUNK] JSONL 저장 완료: {out_path} ({len(chunks)}개 청크)")

def save_chunks_to_csv(chunks: list, filename: str, chunking_method: str, source_file: str, overwrite: bool = False):
    """Chunking 결과를 CSV 형식으로 저장 (DataFrame 처리용)"""
    out_path = OUT_DIR / f"{filename}_chunks.csv"
    
    if out_path.exists() and not overwrite:
        print(f"[SKIP] 파일이 이미 존재합니다: {out_path}")
        return
    
    chunk_data = []
    for i, chunk in enumerate(chunks):
        chunk_data.append({
            "chunk_id": f"{filename}_{i:04d}",
            "source_file": source_file,
            "chunking_method": chunking_method,
            "chunk_index": i,
            "text_length": len(chunk),
            "word_count": len(chunk.split()),
            "chunk_text": chunk
        })
    
    df = pd.DataFrame(chunk_data)
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"[CHUNK] CSV 저장 완료: {out_path} ({len(chunks)}개 청크)")

def save_chunks_to_parquet(chunks: list, filename: str, chunking_method: str, source_file: str, overwrite: bool = False):
    """Chunking 결과를 Parquet 형식으로 저장 (대용량 데이터용)"""
    out_path = OUT_DIR / f"{filename}_chunks.parquet"
    
    if out_path.exists() and not overwrite:
        print(f"[SKIP] 파일이 이미 존재합니다: {out_path}")
        return
    
    chunk_data = []
    for i, chunk in enumerate(chunks):
        chunk_data.append({
            "chunk_id": f"{filename}_{i:04d}",
            "source_file": source_file,
            "chunking_method": chunking_method,
            "chunk_index": i,
            "text_length": len(chunk),
            "word_count": len(chunk.split()),
            "chunk_text": chunk
        })
    
    df = pd.DataFrame(chunk_data)
    df.to_parquet(out_path, index=False)
    print(f"[CHUNK] Parquet 저장 완료: {out_path} ({len(chunks)}개 청크)")

def save_chunks_summary(chunks: list, filename: str, chunking_method: str, source_file: str, overwrite: bool = False):
    """Chunking 결과 요약 정보 저장"""
    out_path = OUT_DIR / f"{filename}_summary.json"
    
    if out_path.exists() and not overwrite:
        print(f"[SKIP] 파일이 이미 존재합니다: {out_path}")
        return
    
    summary = {
        "filename": filename,
        "source_file": source_file,
        "chunking_method": chunking_method,
        "total_chunks": len(chunks),
        "total_characters": sum(len(chunk) for chunk in chunks),
        "total_words": sum(len(chunk.split()) for chunk in chunks),
        "avg_chunk_length": sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0,
        "avg_word_count": sum(len(chunk.split()) for chunk in chunks) / len(chunks) if chunks else 0,
        "min_chunk_length": min(len(chunk) for chunk in chunks) if chunks else 0,
        "max_chunk_length": max(len(chunk) for chunk in chunks) if chunks else 0
    }
    
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"[SUMMARY] 요약 저장 완료: {out_path}")

# =========================
# 메인 파이프라인: TXT 소스
# =========================
def main_txt(file_name: str, chunking_method="paragraph", save_formats=None, overwrite: bool = False):
    if save_formats is None:
        save_formats = ["jsonl", "csv", "summary"]
    
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

    # Chunking 결과 저장
    if "jsonl" in save_formats:
        save_chunks_to_jsonl(chunks, file_name, chunking_method, f"{file_name}.txt", overwrite)
    
    if "csv" in save_formats:
        save_chunks_to_csv(chunks, file_name, chunking_method, f"{file_name}.txt", overwrite)
    
    if "parquet" in save_formats:
        save_chunks_to_parquet(chunks, file_name, chunking_method, f"{file_name}.txt", overwrite)
    
    if "summary" in save_formats:
        save_chunks_summary(chunks, file_name, chunking_method, f"{file_name}.txt", overwrite)

# =========================
# 메인 파이프라인: PDF 소스
# =========================
def main_pdf(file_name: str, chunking_method="topic", save_formats=None, overwrite: bool = False):
    if save_formats is None:
        save_formats = ["jsonl", "csv", "summary"]
    
    src = Path(f"./finetuning/{file_name}.pdf")
    if not src.exists():
        raise FileNotFoundError(f"입력 PDF 없음: {src}")
    text = extract_pdf_text(str(src))
    
    if not text.strip():
        print(f"[오류] PDF에서 텍스트를 추출할 수 없습니다: {file_name}")
        return
    
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

    # Chunking 결과 저장
    if "jsonl" in save_formats:
        save_chunks_to_jsonl(chunks, file_name, chunking_method, f"{file_name}.pdf", overwrite)
    
    if "csv" in save_formats:
        save_chunks_to_csv(chunks, file_name, chunking_method, f"{file_name}.pdf", overwrite)
    
    if "parquet" in save_formats:
        save_chunks_to_parquet(chunks, file_name, chunking_method, f"{file_name}.pdf", overwrite)
    
    if "summary" in save_formats:
        save_chunks_summary(chunks, file_name, chunking_method, f"{file_name}.pdf", overwrite)

# =========================
# DataFrame 로딩 유틸리티
# =========================

def load_chunks_as_dataframe(filename: str, format_type="jsonl"):
    """저장된 chunking 결과를 DataFrame으로 로드"""
    if format_type == "jsonl":
        file_path = OUT_DIR / f"{filename}_chunks.jsonl"
        chunks = []
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                chunks.append(json.loads(line.strip()))
        return pd.DataFrame(chunks)
    
    elif format_type == "csv":
        file_path = OUT_DIR / f"{filename}_chunks.csv"
        return pd.read_csv(file_path, encoding='utf-8-sig')
    
    elif format_type == "parquet":
        file_path = OUT_DIR / f"{filename}_chunks.parquet"
        return pd.read_parquet(file_path)
    
    else:
        raise ValueError(f"지원하지 않는 형식: {format_type}")

def get_chunking_summary(filename: str):
    """Chunking 결과 요약 정보 로드"""
    file_path = OUT_DIR / f"{filename}_summary.json"
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)

# =========================
# 실행부
# =========================
if __name__ == "__main__":
    # 파일별 최적화된 설정
    files_config = [
        # 논문/연구 → paragraph/sentence chunk + 요약/QA
        ("자동차 차체 형태 디자인이 공기역학 성능에 미치는영향에 대한 연구", "pdf","length", ["jsonl", "csv"]),
        ("현대자동차 디자인 철학에 내재하는 미의식의 신경학적 해석", "pdf", "length", ["jsonl", "csv"]),
        
        # 디자인 철학/브랜드 스토리 → paragraph + 정의 세트
        ("현대 디자인 모토", "txt", "paragraph", ["jsonl", "csv"]),
        ("현대 모터스튜디오_디자인 관련 문서", "pdf", "length", ["jsonl", "csv"]),
        
        # 프리뷰/뉴스 기사 → sentence chunk + QA
        ("new_articles", "txt", "sentence", ["jsonl", "csv"]),
        ("preview_articles", "txt", "sentence", ["jsonl", "csv"]),
        ("total_articles", "txt", "length", ["jsonl", "csv"]),
        
        # 인터뷰 → qa_format chunk 그대로 QA
        ("hyundai_journal_articles", "txt", "qa_format", ["jsonl", "csv"]),
        ("interview_articles", "txt", "qa_format", ["jsonl", "csv"]),
        
        # 기타
        ("자동차의 뼈대 차체 및 구조 설계의 모든 것", "txt", "paragraph", ["jsonl", "csv"])
    ]

    # 덮어쓰기 옵션 (환경변수로 제어)
    overwrite = os.getenv("OVERWRITE", "false").lower() == "true"

    for file_name, file_type, chunking_method, save_formats in files_config:
        print(f"\n{'='*60}")
        print(f"처리 중: {file_name}")
        print(f"{'='*60}")
        
        if file_type == "pdf":
            main_pdf(file_name, chunking_method, save_formats, overwrite)
        else:
            main_txt(file_name, chunking_method, save_formats, overwrite)
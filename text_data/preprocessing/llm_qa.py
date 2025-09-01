# -*- coding: utf-8 -*-
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple
import unicodedata
import csv

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL_NAME = os.getenv("LLM_MODEL", "gpt-4o")
CHUNK_DIR = Path("./chunking_result")
# 출력도 chunking_result에 반영
OUT_DIR = CHUNK_DIR
OUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# 유틸
# =========================

def normalize(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    s = unicodedata.normalize("NFKC", s.strip())
    return " ".join(s.split())

# =========================
# 프롬프트 (1-3개의 Q/A 생성)
# =========================
QA_PROMPT = """다음 <CONTEXT>에서만 정보를 사용하여, 현대자동차/자동차 도메인에 적합한 사실 기반 질문-답변 쌍을 <CONTEXT>의 내용이 다 담길 수 있게 최대한 많이 겹치지 않게 생성하라.

작성 지침:
- 질문은 한 줄, 구체적이며 검증 가능한 사실(수치/단위/연도/모델명/부품/효과)을 겨냥할 것
- 답변은 한 줄의 완결된 문장으로, 컨텍스트의 용어/수치/표현을 정확히 보존할 것
- 문맥에 정보가 없으면 만들지 말 것
도메인 초점(자동차·현대자동차 맥락):
- 설계/디자인 철학: 센슈어스 스포트니스, 파라메트릭 픽셀, 파라메트릭 다이나믹스 등
- 공력/성능: 항력계수(Cd), 양력/다운포스, 공력 요소(디퓨저, 스포일러, 에어커튼)
- 차체 비율/형상: 휠베이스, 트랙, 오버행, 벨트라인, 그린하우스, 실루엣(two-box/three-box)
- 조명/전장/섀시: DRL, 헤드램프/테일램프 구조, 서스펜션/브레이크, 휠·타이어 규격
- 수치·일정·버전: 연도/행사/모델, %, mm, kg, kW 등 단위 포함 수치

출력 형식(아래 블록 외 다른 문구 금지):
Q1: <질문>
A1: <답변>
---
Q2: <질문>
A2: <답변>
---
Q3: <질문>
A3: <답변>
(생성 가능한 개수만큼 출력)

<CONTEXT>
{context}
"""

client = OpenAI()


def ask_qas(context: str, max_retries: int = 3, temperature: float = 0.3, max_tokens: int = 600) -> List[Tuple[str, str]]:
    prompt = QA_PROMPT.format(context=context)
    for i in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = resp.choices[0].message.content or ""
            return parse_qas(content)
        except Exception as e:
            print(f"[경고] LLM 호출 재시도 {i+1}: {e}")
            time.sleep(1.5)
    return []


def parse_qas(raw: str) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    blocks = [b.strip() for b in raw.split("---") if b.strip()]
    for block in blocks:
        lines = [normalize(l) for l in block.split("\n") if l.strip()]
        q, a = None, None
        for ln in lines:
            if ln.startswith("Q") and ":" in ln:
                q = normalize(ln.split(":", 1)[1])
            elif ln.startswith("A") and ":" in ln:
                a = normalize(ln.split(":", 1)[1])
        if q and a:
            pairs.append((q, a))
    # 상한 3개 보장
    return pairs[:3]


def process_file(base_name: str, start_index: int = 0, limit: int = None, sleep_s: float = 1.0, overwrite: bool = False):
    """chunking_result의 *_chunks.jsonl을 읽어 question/answer를 붙여 동일 디렉토리에 저장"""
    in_jsonl = CHUNK_DIR / f"{base_name}_chunks.jsonl"
    if not in_jsonl.exists():
        raise FileNotFoundError(f"청크 파일을 찾을 수 없음: {in_jsonl}")

    # 출력 파일명 결정: overwrite면 원본 파일명을 덮어쓰고, 아니면 *_chunks_qa.* 로 저장
    if overwrite:
        out_jsonl = OUT_DIR / f"{base_name}_chunks.jsonl"
        out_csv = OUT_DIR / f"{base_name}_chunks.csv"
        # 덮어쓰기 전 기존 파일 삭제
        if out_jsonl.exists():
            out_jsonl.unlink()
        if out_csv.exists():
            out_csv.unlink()
    else:
        out_jsonl = OUT_DIR / f"{base_name}_chunks_qa.jsonl"
        out_csv = OUT_DIR / f"{base_name}_chunks_qa.csv"
        if out_jsonl.exists():
            out_jsonl.unlink()
        if out_csv.exists():
            out_csv.unlink()

    # CSV 헤더 정의 (원본 메타 + question/answer)
    csv_header = [
        "chunk_id", "source_file", "chunking_method", "chunk_index",
        "text_length", "word_count", "chunk_text", "question", "answer"
    ]

    total_qas = 0
    handled_chunks = 0

    with in_jsonl.open("r", encoding="utf-8") as src, \
         out_jsonl.open("w", encoding="utf-8") as jdst, \
         out_csv.open("w", encoding="utf-8", newline="") as cdst:
        writer = csv.writer(cdst)
        writer.writerow(csv_header)

        for idx, line in enumerate(src):
            if idx < start_index:
                continue
            if limit is not None and handled_chunks >= limit:
                break

            obj = json.loads(line)
            chunk_text = obj.get("chunk_text", "")
            if not chunk_text:
                continue

            qas = ask_qas(chunk_text)
            if not qas:
                handled_chunks += 1
                print(f"  - chunk {idx} ({obj.get('chunk_id')}) → 0 QA")
                time.sleep(sleep_s)
                continue

            # 각 QA별로 한 행씩 출력(JSONL/CSV 모두)
            for q, a in qas:
                enriched = {
                    **obj,
                    "question": q,
                    "answer": a,
                }
                jdst.write(json.dumps(enriched, ensure_ascii=False) + "\n")
                writer.writerow([
                    obj.get("chunk_id"), obj.get("source_file"), obj.get("chunking_method"), obj.get("chunk_index"),
                    obj.get("text_length"), obj.get("word_count"), obj.get("chunk_text"), q, a
                ])
                total_qas += 1

            handled_chunks += 1
            print(f"  - chunk {idx} ({obj.get('chunk_id')}) → {len(qas)} QA")
            time.sleep(sleep_s)

    print(f"[DONE] {base_name}: 청크 {handled_chunks}개 처리, QA {total_qas}개 생성. 저장: {out_jsonl.name}, {out_csv.name}")


def main():
    # 환경변수
    only_file = os.getenv("ONLY_FILE")  # 예: new_articles
    start_index = int(os.getenv("START_INDEX", "0"))
    limit = os.getenv("LIMIT")
    limit = int(limit) if limit and limit.isdigit() else None
    sleep_s = float(os.getenv("SLEEP_S", "1.0"))
    overwrite = os.getenv("OVERWRITE", "false").lower() == "true"

    if only_file:
        files = [only_file]
    else:
        files = []
        for p in CHUNK_DIR.glob("*_chunks.jsonl"):
            base = p.name.replace("_chunks.jsonl", "")
            files.append(base)
        files.sort()

    print(f"대상 파일: {files}")
    for base in files:
        print(f"\n{'='*60}")
        print(f"처리 중: {base} (start_index={start_index}, limit={limit}, overwrite={overwrite})")
        print(f"{'='*60}")
        process_file(base, start_index=start_index, limit=limit, sleep_s=sleep_s, overwrite=overwrite)


if __name__ == "__main__":
    main()

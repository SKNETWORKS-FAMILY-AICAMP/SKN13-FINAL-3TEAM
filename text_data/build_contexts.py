# -*- coding: utf-8 -*-
import os
import re
import json
import csv
from pathlib import Path
from typing import List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CHUNK_DIR = Path("./chunking_result")
OUT_DIR = Path("./contexts_result")  # 새로운 출력 디렉토리
OUT_DIR.mkdir(parents=True, exist_ok=True)

TOP_K = int(os.getenv("TOP_K", "4"))  # 기본값을 4로 변경
OVERWRITE = os.getenv("OVERWRITE", "false").lower() == "true"


def sentence_split(text: str) -> List[str]:
    # 간단한 한국어/영문 문장 분리 (마침표/물음표/느낌표/개행 기준)
    # 너무 짧은 토막은 버림
    if not text:
        return []
    # 줄바꿈을 공백으로 정규화 후 문장 구분자 기준 분리
    normalized = re.sub(r"\s+", " ", text.strip())
    parts = re.split(r"(?<=[.!?])\s+", normalized)
    sentences = [s.strip() for s in parts if len(s.strip()) >= 5]
    return sentences


def build_contexts(question: str, chunk_text: str, top_k: int) -> Tuple[List[str], List[int], List[float]]:
    sentences = sentence_split(chunk_text)
    if not question or not sentences:
        return [], [], []

    # TF-IDF 기반 코사인 유사도
    docs = [question] + sentences
    tfidf = TfidfVectorizer(min_df=1, ngram_range=(1, 2))
    X = tfidf.fit_transform(docs)

    q_vec = X[0:1]
    s_vecs = X[1:]
    sims = cosine_similarity(q_vec, s_vecs).flatten()

    # 상위 top_k 문장 인덱스 선택 (내림차순)
    ranked_idx = np.argsort(-sims)
    top_idx = ranked_idx[:top_k]

    # 컨텍스트 문자열 구성: [1] 문장 (유사도 점수 포함)
    contexts = []
    similarities = []
    for i, s_idx in enumerate(top_idx, start=1):
        sim_score = sims[s_idx]
        contexts.append(f"[{i}] {sentences[s_idx]}")
        similarities.append(sim_score)

    # 증거 ID는 항상 1 (가장 유사한 문장)
    evidence_ids = [1] if contexts else []

    return contexts, evidence_ids, similarities


def process_file(base_name: str, top_k: int, overwrite: bool):
    # 입력 파일 (우선 QA가 붙은 파일 사용, 없으면 원본 청크 파일)
    in_jsonl = CHUNK_DIR / f"{base_name}_chunks_qa.jsonl"
    in_csv = CHUNK_DIR / f"{base_name}_chunks_qa.csv"
    if not in_jsonl.exists():
        in_jsonl = CHUNK_DIR / f"{base_name}_chunks.jsonl"
    if not in_csv.exists():
        in_csv = CHUNK_DIR / f"{base_name}_chunks.csv"

    if not in_jsonl.exists():
        raise FileNotFoundError(f"입력 JSONL을 찾을 수 없습니다: {in_jsonl}")

    # 출력 파일 (새로운 디렉토리에 저장)
    out_jsonl = OUT_DIR / f"{base_name}_contexts.jsonl"
    out_csv = OUT_DIR / f"{base_name}_contexts.csv"

    # JSONL 처리
    total = 0
    with open(in_jsonl, "r", encoding="utf-8") as rf, open(out_jsonl, "w", encoding="utf-8") as wf:
        for line in rf:
            obj = json.loads(line)
            question = obj.get("question", "")
            chunk_text = obj.get("chunk_text", "")

            contexts, evidence_ids, similarities = build_contexts(question, chunk_text, top_k)

            obj["contexts"] = contexts
            obj["evidence_ids"] = evidence_ids
            obj["similarities"] = similarities
            wf.write(json.dumps(obj, ensure_ascii=False) + "\n")
            total += 1

    # CSV 처리(선택적): 입력 CSV가 없을 수도 있음
    if in_csv and in_csv.exists():
        with open(in_csv, "r", encoding="utf-8") as rf, open(out_csv, "w", encoding="utf-8", newline="") as wf:
            reader = csv.DictReader(rf)
            fieldnames = list(reader.fieldnames or [])
            # 새 컬럼 추가
            for col in ["contexts", "evidence_ids", "similarities"]:
                if col not in fieldnames:
                    fieldnames.append(col)
            writer = csv.DictWriter(wf, fieldnames=fieldnames)
            writer.writeheader()
            for row in reader:
                question = row.get("question", "")
                chunk_text = row.get("chunk_text", "")
                contexts, evidence_ids, similarities = build_contexts(question, chunk_text, top_k)
                row["contexts"] = json.dumps(contexts, ensure_ascii=False)
                row["evidence_ids"] = json.dumps(evidence_ids, ensure_ascii=False)
                row["similarities"] = json.dumps(similarities, ensure_ascii=False)
                writer.writerow(row)

    print(f"[DONE] {base_name}: {total} 레코드에 contexts/evidence_ids/similarities 추가. 저장: {out_jsonl.name}{' & ' + out_csv.name if out_csv else ''}")


def main():
    only_file = os.getenv("ONLY_FILE")  # 처리 대상 베이스명
    top_k = int(os.getenv("TOP_K", str(TOP_K)))
    overwrite = os.getenv("OVERWRITE", "false").lower() == "true"

    if only_file:
        files = [only_file]
    else:
        # *_chunks_qa.jsonl 우선, 없으면 *_chunks.jsonl
        bases = set()
        for p in CHUNK_DIR.glob("*_chunks_qa.jsonl"):
            bases.add(p.name.replace("_chunks_qa.jsonl", ""))
        if not bases:
            for p in CHUNK_DIR.glob("*_chunks.jsonl"):
                bases.add(p.name.replace("_chunks.jsonl", ""))
        files = sorted(bases)

    print(f"대상 파일: {files}")
    for base in files:
        print(f"처리 중: {base} (top_k={top_k}, overwrite={overwrite})")
        process_file(base, top_k=top_k, overwrite=overwrite)


if __name__ == "__main__":
    main()

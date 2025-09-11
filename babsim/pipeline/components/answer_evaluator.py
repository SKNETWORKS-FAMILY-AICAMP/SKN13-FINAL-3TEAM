from __future__ import annotations
import re
from typing import Dict
import sys
import os
from pathlib import Path

# 파이프라인 루트 경로를 Python 경로에 추가
PIPELINE_ROOT = Path(__file__).parent.parent
sys.path.append(str(PIPELINE_ROOT))

from ..llm_provider import kanana_llm_model

class AnswerEvaluator:
    def analyze(self, user_query: str, answer: str, context_hint: str = "") -> Dict[str, object]:
        prompt = f"""
아래 질문/답변의 '관련성'과 '충분성'을 0~1로 각 채점하고,
개선 포인트 한 줄을 제시하세요.

[질문]
{user_query}

[컨텍스트 힌트]
{context_hint[:600]}

[답변]
{answer}

[출력 형식]
relevance=0.xx
adequacy=0.xx
note=...
"""
        raw = kanana_llm_model.generate_response(prompt, max_length=200).strip()
        return {
            "relevance": float(_pick_num(raw, "relevance") or 0.0),
            "adequacy":  float(_pick_num(raw, "adequacy") or 0.0),
            "note": _pick_text(raw, "note"),
            "raw": raw,
        }

def _pick_num(t: str, key: str):
    m = re.search(rf"{key}\s*=\s*([01](?:\.\d+)?)", t, re.I)
    return m.group(1) if m else None

def _pick_text(t: str, key: str):
    m = re.search(rf"{key}\s*=\s*(.+)", t, re.I)
    return (m.group(1).strip() if m else "").split("\n")[0]

answer_evaluator = AnswerEvaluator()
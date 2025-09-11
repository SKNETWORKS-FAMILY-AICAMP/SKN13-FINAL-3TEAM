from __future__ import annotations
import re
import sys
import os
from pathlib import Path

# 파이프라인 루트 경로를 Python 경로에 추가
PIPELINE_ROOT = Path(__file__).parent.parent
sys.path.append(str(PIPELINE_ROOT))

from ..llm_provider import kanana_llm_model

class QueryRewriter:
    def hyde_expand_and_rewrite(self, user_query: str):
        prompt = f"""
다음 질문에 대해 3~5문장 가상답변 작성 → 그 답변에서 핵심 키워드 8~12개 추출 →
키워드 위주로 1줄짜리 '검색 쿼리' 작성.

[질문]
{user_query}

[출력 형식]
가상답변: ...
키워드: 키워드1, 키워드2, ...
검색쿼리: ...
"""
        out = kanana_llm_model.generate_response(prompt, max_length=360).strip()
        pseudo = _pick(out, r"가상답변\s*:\s*(.+)")
        keys   = _pick(out, r"키워드\s*:\s*(.+)")
        q      = _pick(out, r"검색쿼리\s*:\s*(.+)") or re.sub(r"\s+", " ", keys.replace(",", " "))
        return q[:512], pseudo

def _pick(text: str, pat: str) -> str:
    m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
    if not m: return ""
    return m.group(1).split("\n")[0].strip()

query_rewriter = QueryRewriter()
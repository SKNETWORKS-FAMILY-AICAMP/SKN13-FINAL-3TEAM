from __future__ import annotations
import os
import torch
from typing import Optional
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
from peft import PeftModel

def _env(path_key: str, default: Optional[str] = None) -> Optional[str]:
    p = os.getenv(path_key, default)
    return p if p and os.path.exists(p) else default

class _KananaChat:
    def __init__(self):
        base = _env("KANANA_BASE_MODEL_PATH")
        finetuned = _env("KANANA_FINETUNED_PATH")

        if not base:
            raise RuntimeError("KANANA_BASE_MODEL_PATH 가 설정되지 않았거나 경로가 존재하지 않습니다.")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        self.tokenizer = AutoTokenizer.from_pretrained(base, trust_remote_code=True, use_fast=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            base,
            torch_dtype=self.torch_dtype,
            low_cpu_mem_usage=True,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=True,
        )

        # 파인튜닝(LoRA or full) 자동 감지
        if finetuned:
            adapter_cfg = os.path.join(finetuned, "adapter_config.json")
            try:
                if os.path.exists(adapter_cfg):
                    # LoRA 어댑터
                    self.model = PeftModel.from_pretrained(self.model, finetuned)
                else:
                    # 전량 파인튜닝 가중치 디렉터리 시도
                    self.model = AutoModelForCausalLM.from_pretrained(
                        finetuned,
                        torch_dtype=self.torch_dtype,
                        low_cpu_mem_usage=True,
                        device_map="auto" if torch.cuda.is_available() else None,
                        trust_remote_code=True,
                    )
            except Exception:
                # 문제가 있으면 베이스만 사용
                pass

        self.model.eval()
        self.gen_cfg = GenerationConfig(
            do_sample=True, temperature=0.7, top_p=0.9,
            repetition_penalty=1.05, max_new_tokens=512,
        )

    def _build_prompt(self, prompt: str) -> str:
        system = "당신은 현대자동차/자동차 지식에 특화된 한국어 어시스턴트입니다. 반드시 한국어로 답하세요."
        return f"[SYSTEM]\n{system}\n\n[USER]\n{prompt}\n\n[ASSISTANT]\n"

    @torch.inference_mode()
    def generate_response(self, prompt: str, max_length: int = 512) -> str:
        text = self._build_prompt(prompt)
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)

        cfg = self.gen_cfg
        cfg.max_new_tokens = max_length

        output_ids = self.model.generate(**inputs, generation_config=cfg)
        out = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        if out.startswith(text):
            out = out[len(text):].strip()
        return out.strip()

kanana_llm_model = _KananaChat()
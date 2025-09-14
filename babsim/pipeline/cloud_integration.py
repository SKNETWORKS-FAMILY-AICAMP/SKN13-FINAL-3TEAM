#!/usr/bin/env python3
"""
클라우드 기반 모델 서비스 통합 모듈
CPU 환경에서 클라우드 서비스를 활용하는 방법
"""

import os
import requests
import json
import torch
from typing import Dict, Any, List
from abc import ABC, abstractmethod

class CloudModelService(ABC):
    """클라우드 모델 서비스 추상 클래스"""
    
    @abstractmethod
    def generate_text(self, prompt: str, max_length: int = 512) -> str:
        """텍스트 생성"""
        pass
    
    @abstractmethod
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """임베딩 생성"""
        pass

class OpenAIService(CloudModelService):
    """OpenAI API 서비스"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
    
    def generate_text(self, prompt: str, max_length: int = 512) -> str:
        """OpenAI GPT로 텍스트 생성"""
        if not self.api_key:
            raise ValueError("OpenAI API 키가 필요합니다.")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant specialized in Hyundai Motor Company and automotive knowledge. Answer in Korean."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_length,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            print(f"OpenAI API 호출 실패: {e}")
            return "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """OpenAI 임베딩 생성"""
        if not self.api_key:
            raise ValueError("OpenAI API 키가 필요합니다.")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "text-embedding-3-small",
            "input": texts
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return [item["embedding"] for item in result["data"]]
            
        except Exception as e:
            print(f"OpenAI 임베딩 API 호출 실패: {e}")
            return []

class HuggingFaceService(CloudModelService):
    """Hugging Face Inference API 서비스"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        self.base_url = "https://api-inference.huggingface.co/models"
    
    def generate_text(self, prompt: str, max_length: int = 512) -> str:
        """Hugging Face로 텍스트 생성"""
        if not self.api_key:
            raise ValueError("Hugging Face API 키가 필요합니다.")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "inputs": prompt,
            "parameters": {
                "max_length": max_length,
                "temperature": 0.7,
                "do_sample": True
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/microsoft/DialoGPT-medium",
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "")
            return ""
            
        except Exception as e:
            print(f"Hugging Face API 호출 실패: {e}")
            return "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Hugging Face 임베딩 생성"""
        if not self.api_key:
            raise ValueError("Hugging Face API 키가 필요합니다.")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "inputs": texts
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/sentence-transformers/all-MiniLM-L6-v2",
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, list):
                return result
            return []
            
        except Exception as e:
            print(f"Hugging Face 임베딩 API 호출 실패: {e}")
            return []

class LocalFallbackService(CloudModelService):
    """로컬 폴백 서비스 (가벼운 모델 사용)"""
    
    def __init__(self):
        self._load_models()
    
    def _load_models(self):
        """가벼운 모델 로드"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            from sentence_transformers import SentenceTransformer
            
            # 가벼운 모델들
            self.tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
            self.model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")
            self.embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            
            print("✅ 로컬 모델 로드 완료")
            
        except Exception as e:
            print(f"❌ 로컬 모델 로드 실패: {e}")
            self.tokenizer = None
            self.model = None
            self.embedding_model = None
    
    def generate_text(self, prompt: str, max_length: int = 512) -> str:
        """로컬 모델로 텍스트 생성"""
        if not self.model or not self.tokenizer:
            return "로컬 모델을 사용할 수 없습니다."
        
        try:
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=max_length,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response.replace(prompt, "").strip()
            
        except Exception as e:
            print(f"로컬 텍스트 생성 실패: {e}")
            return "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """로컬 모델로 임베딩 생성"""
        if not self.embedding_model:
            return []
        
        try:
            embeddings = self.embedding_model.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()
            
        except Exception as e:
            print(f"로컬 임베딩 생성 실패: {e}")
            return []

class ModelServiceManager:
    """모델 서비스 관리자"""
    
    def __init__(self, preferred_service: str = "auto"):
        self.preferred_service = preferred_service
        self.services = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """서비스 초기화"""
        # 우선순위: OpenAI > Hugging Face > 로컬 폴백
        if os.getenv("OPENAI_API_KEY"):
            self.services["openai"] = OpenAIService()
        
        if os.getenv("HUGGINGFACE_API_KEY"):
            self.services["huggingface"] = HuggingFaceService()
        
        # 로컬 폴백은 항상 사용 가능
        self.services["local"] = LocalFallbackService()
    
    def get_text_service(self) -> CloudModelService:
        """텍스트 생성 서비스 반환"""
        if self.preferred_service == "openai" and "openai" in self.services:
            return self.services["openai"]
        elif self.preferred_service == "huggingface" and "huggingface" in self.services:
            return self.services["huggingface"]
        else:
            # 자동 선택: OpenAI > Hugging Face > 로컬
            for service_name in ["openai", "huggingface", "local"]:
                if service_name in self.services:
                    return self.services[service_name]
        
        # 기본값
        return self.services.get("local", LocalFallbackService())
    
    def get_embedding_service(self) -> CloudModelService:
        """임베딩 생성 서비스 반환"""
        return self.get_text_service()  # 같은 서비스 사용

# 전역 서비스 매니저
model_service_manager = ModelServiceManager()

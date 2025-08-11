# JJACKLETTE/apps.py

from django.apps import AppConfig
import os
import torch
# from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import GPT2TokenizerFast, AutoModelForCausalLM
import logging

logger = logging.getLogger(__name__)

class JjackletteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'JJACKLETTE'
    label = 'JJACKLETTE'
    
    def ready(self):
        # 여기서는 무거운 작업 금지. 모델 로딩은 뷰 호출 시 지연 로딩으로 처리.
        logger.info("App 'JJACKLETTE' ready (no heavy init).")

        
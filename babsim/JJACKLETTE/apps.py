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

    tokenizer = None
    model = None

    def ready(self):
        model_path = "models/exaone_4.0_1.2b"

        if not os.path.isdir(model_path) or not os.listdir(model_path):
            logger.warning(f"Model directory '{model_path}' not found or empty. Skipping model loading.")
            return

        logger.info("Starting LLM model loading... (This may take a while)")

        try:
            # JjackletteConfig.tokenizer = AutoTokenizer.from_pretrained(model_path)
            JjackletteConfig.tokenizer = GPT2TokenizerFast.from_pretrained(model_path)
            JjackletteConfig.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map="auto",
                torch_dtype=torch.bfloat16,
            )
            JjackletteConfig.model.eval()
            logger.info(f"LLM model loaded successfully. Device map: {self.model.hf_device_map}")

        except Exception as e:
            logger.error(f"Fatal error loading LLM model: {e}", exc_info=True)
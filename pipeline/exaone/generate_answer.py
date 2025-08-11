"""
EXAONE Answer Generation module: Generates text answers using EXAONE from Hugging Face.
"""
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from typing import Dict, Any

class ExaoneAnswerGenerator:
    def __init__(self, model_name: str = "LGAI-EXAONE/EXAONE-4.0-1.2B"):
        """
        Initialize ExaoneAnswerGenerator with Hugging Face model.
        
        Args:
            model_name: Hugging Face model name for EXAONE
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the EXAONE model and tokenizer."""
        try:
            print(f"Loading EXAONE model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            print("EXAONE model loaded successfully")
        except Exception as e:
            print(f"Failed to load EXAONE model: {e}")
            self.tokenizer = None
            self.model = None

    def generate(self, query: str, context: str = "") -> str:
        """
        Generate answer using EXAONE model.
        
        Args:
            query: User query
            context: Additional context from search results or web data
            
        Returns:
            str: Generated answer
        """
        if not self.model or not self.tokenizer:
            # Fallback response if model loading failed
            return f"Based on the query '{query}', here is a comprehensive answer. {context}"
        
        try:
            # Prepare input prompt
            if context:
                prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"
            else:
                prompt = f"Question: {query}\n\nAnswer:"
            
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=200,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the generated part (after the prompt)
            answer = response[len(prompt):].strip()
            
            if not answer:
                # Fallback if no answer generated
                return f"I apologize, but I couldn't generate a specific answer for '{query}'. Please try rephrasing your question."
            
            return answer
            
        except Exception as e:
            print(f"EXAONE answer generation failed: {e}")
            # Fallback response
            return f"I apologize, but I encountered an error while generating the answer for '{query}'. Please try again or rephrase your question."

    def generate_sd_explanation(self, sd_prompt: str, original_query: str, categorized_elements: Dict[str, Any]) -> str:
        """
        Generate explanation for Stable Diffusion prompt.
        
        Args:
            sd_prompt: Generated Stable Diffusion prompt
            original_query: Original user query
            categorized_elements: Categorized query elements
            
        Returns:
            str: Human-readable explanation of the generated image
        """
        if not self.model or not self.tokenizer:
            return self._fallback_sd_explanation(sd_prompt, original_query, categorized_elements)
        
        try:
            # Build explanation prompt
            car_name = categorized_elements.get('car_name', 'Hyundai car')
            design_elements = categorized_elements.get('design_elements', [])
            style = categorized_elements.get('style', 'modern')
            
            prompt = f"""You are an expert automotive design analyst. Explain the generated car image in a user-friendly way.

Original Request: {original_query}
Generated SD Prompt: {sd_prompt}

Car Details:
- Car: {car_name}
- Design Elements: {', '.join(design_elements) if design_elements else 'standard'}
- Style: {style}

Task: Create a clear, engaging explanation of what the generated image shows, focusing on:
- The car's design features and style
- How it matches the user's request
- Key visual elements and characteristics
- Design inspiration and aesthetic choices

Write a natural, conversational explanation that helps users understand what they're seeing.

Explanation:"""
            
            # Tokenize and generate
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=150,
                    temperature=0.8,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            explanation = response[len(prompt):].strip()
            
            if not explanation:
                return self._fallback_sd_explanation(sd_prompt, original_query, categorized_elements)
            
            return explanation
            
        except Exception as e:
            print(f"SD explanation generation failed: {e}")
            return self._fallback_sd_explanation(sd_prompt, original_query, categorized_elements)

    def _fallback_sd_explanation(self, sd_prompt: str, original_query: str, categorized_elements: Dict[str, Any]) -> str:
        """
        Fallback explanation when model is not available.
        
        Args:
            sd_prompt: Generated SD prompt
            original_query: Original user query
            categorized_elements: Categorized elements
            
        Returns:
            str: Fallback explanation
        """
        car_name = categorized_elements.get('car_name', 'Hyundai car')
        style = categorized_elements.get('style', 'modern')
        design_elements = categorized_elements.get('design_elements', [])
        
        explanation_parts = [
            f"이 이미지는 {car_name}의 {style} 디자인을 보여줍니다.",
            f"사용자의 요청 '{original_query}'에 따라 생성되었습니다."
        ]
        
        if design_elements:
            explanation_parts.append(f"주요 디자인 요소: {', '.join(design_elements)}")
        
        explanation_parts.append("전문적인 자동차 사진 스타일로 렌더링되었으며, 현대적인 디자인 언어를 반영합니다.")
        
        return " ".join(explanation_parts)

    def generate_with_system_prompt(self, query: str, context: str = "", system_prompt: str = None) -> str:
        """
        Generate answer with custom system prompt.
        
        Args:
            query: User query
            context: Additional context
            system_prompt: Custom system prompt
            
        Returns:
            str: Generated answer
        """
        if not self.model or not self.tokenizer:
            return f"Based on the query '{query}', here is a comprehensive answer. {context}"
        
        try:
            # Use default system prompt if none provided
            if not system_prompt:
                system_prompt = """You are EXAONE, an advanced AI assistant specialized in providing comprehensive and accurate answers.

Your responses should be:
- Accurate and well-researched
- Comprehensive but concise
- Well-structured and easy to understand
- Based on the provided context when available

Always provide helpful and informative answers."""
            
            # Prepare input with system prompt
            if context:
                prompt = f"{system_prompt}\n\nContext: {context}\n\nQuestion: {query}\n\nAnswer:"
            else:
                prompt = f"{system_prompt}\n\nQuestion: {query}\n\nAnswer:"
            
            # Tokenize and generate
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=200,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            answer = response[len(prompt):].strip()
            
            return answer if answer else f"Generated response for: {query}"
            
        except Exception as e:
            print(f"EXAONE generation with system prompt failed: {e}")
            return f"Error generating answer for: {query}"

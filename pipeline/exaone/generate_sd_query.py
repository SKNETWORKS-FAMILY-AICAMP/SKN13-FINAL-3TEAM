"""
EXAONE SD Query Generation module: Generates image generation queries (e.g., 77 CLIP tokens) for Stable Diffusion.
"""
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from typing import Dict, Any, List

class ExaoneSDQueryGenerator:
    def __init__(self, model_name: str = "LGAI-EXAONE/EXAONE-4.0-1.2B"):
        """
        Initialize ExaoneSDQueryGenerator with Hugging Face model.
        
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
            print(f"Loading EXAONE SD model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            print("EXAONE SD model loaded successfully")
        except Exception as e:
            print(f"Failed to load EXAONE SD model: {e}")
            self.tokenizer = None
            self.model = None

    def generate_sd_query(self, categorized_query: Dict[str, Any], creative_context: str = "") -> Dict[str, str]:
        """
        Generate Stable Diffusion query using EXAONE model.
        
        Args:
            categorized_query: Categorized query elements from query analyzer
            creative_context: Creative context from MCP web search
            
        Returns:
            Dict: Contains 'prompt' and 'explanation'
        """
        if not self.model or not self.tokenizer:
            # Fallback response
            return self._fallback_sd_query(categorized_query, creative_context)
        
        try:
            # Prepare input prompt for SD query generation
            prompt = self._build_sd_prompt(categorized_query, creative_context)
            
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=150,
                    temperature=0.8,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the generated part
            generated_text = response[len(prompt):].strip()
            
            # Parse the response to extract prompt and explanation
            result = self._parse_sd_response(generated_text)
            
            return result
            
        except Exception as e:
            print(f"EXAONE SD query generation failed: {e}")
            return self._fallback_sd_query(categorized_query, creative_context)

    def _build_sd_prompt(self, categorized_query: Dict[str, Any], creative_context: str) -> str:
        """
        Build prompt for SD query generation.
        
        Args:
            categorized_query: Categorized query elements
            creative_context: Creative context from web search
            
        Returns:
            str: Formatted prompt
        """
        car_name = categorized_query.get('car_name', 'Hyundai car')
        design_elements = categorized_query.get('design_elements', [])
        style = categorized_query.get('style', 'modern')
        color = categorized_query.get('color', '')
        perspective = categorized_query.get('perspective', '')
        background = categorized_query.get('background', '')
        additional_features = categorized_query.get('additional_features', [])
        
        # Build the prompt
        prompt = f"""You are an expert at creating Stable Diffusion prompts for car design visualization.

Task: Create a detailed, 77 CLIP token compatible prompt for generating a car image.

Car Information:
- Car: {car_name}
- Design Elements: {', '.join(design_elements) if design_elements else 'standard'}
- Style: {style}
- Color: {color if color else 'default'}
- Perspective: {perspective if perspective else '3/4 view'}
- Background: {background if background else 'studio background'}
- Additional Features: {', '.join(additional_features) if additional_features else 'none'}

Creative Context: {creative_context if creative_context else 'Focus on Hyundai design language and modern automotive aesthetics'}

Requirements:
- Create a detailed prompt suitable for Stable Diffusion
- Include specific design elements, lighting, and composition details
- Ensure the prompt is optimized for 77 CLIP tokens
- Focus on automotive design and Hyundai brand characteristics

Format your response as:
PROMPT: [detailed stable diffusion prompt]
EXPLANATION: [brief explanation of design choices]

PROMPT:"""
        
        return prompt

    def _parse_sd_response(self, response: str) -> Dict[str, str]:
        """
        Parse the generated response to extract prompt and explanation.
        
        Args:
            response: Generated response text
            
        Returns:
            Dict: Parsed prompt and explanation
        """
        try:
            # Try to extract PROMPT and EXPLANATION sections
            if "PROMPT:" in response and "EXPLANATION:" in response:
                parts = response.split("EXPLANATION:")
                prompt_part = parts[0].replace("PROMPT:", "").strip()
                explanation_part = parts[1].strip()
                
                return {
                    "prompt": prompt_part,
                    "explanation": explanation_part
                }
            else:
                # If parsing fails, use the whole response as prompt
                return {
                    "prompt": response,
                    "explanation": "Generated prompt for car design visualization"
                }
                
        except Exception as e:
            print(f"Failed to parse SD response: {e}")
            return {
                "prompt": response,
                "explanation": "Parsed response for car design"
            }

    def _fallback_sd_query(self, categorized_query: Dict[str, Any], creative_context: str) -> Dict[str, str]:
        """
        Fallback SD query generation when model is not available.
        
        Args:
            categorized_query: Categorized query elements
            creative_context: Creative context
            
        Returns:
            Dict: Fallback prompt and explanation
        """
        car_name = categorized_query.get('car_name', 'Hyundai car')
        design_elements = categorized_query.get('design_elements', [])
        style = categorized_query.get('style', 'modern')
        
        # Create a basic prompt
        prompt_parts = [
            f"professional photograph of a {car_name}",
            f"{style} design",
            "high quality",
            "detailed",
            "studio lighting",
            "3/4 view",
            "automotive photography"
        ]
        
        if design_elements:
            prompt_parts.extend(design_elements)
        
        if creative_context:
            prompt_parts.append("inspired by modern automotive design trends")
        
        prompt = ", ".join(prompt_parts)
        
        return {
            "prompt": prompt,
            "explanation": f"Generated fallback prompt for {car_name} with {style} design elements"
        }

    def optimize_for_clip_tokens(self, prompt: str, max_tokens: int = 77) -> str:
        """
        Optimize prompt for CLIP token limit.
        
        Args:
            prompt: Original prompt
            max_tokens: Maximum CLIP tokens (default 77)
            
        Returns:
            str: Optimized prompt
        """
        # Simple token optimization (in a real implementation, you'd use CLIP tokenizer)
        words = prompt.split()
        
        # Estimate tokens (rough approximation: 1 word ≈ 1.3 tokens)
        estimated_tokens = len(words) * 1.3
        
        if estimated_tokens <= max_tokens:
            return prompt
        
        # Truncate if too long
        max_words = int(max_tokens / 1.3)
        optimized_words = words[:max_words]
        
        return " ".join(optimized_words)

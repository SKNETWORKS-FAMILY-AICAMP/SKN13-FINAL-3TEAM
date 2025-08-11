"""
Stable Diffusion Image Generation module: Generates images using Stable Diffusion 3.5 Medium.
"""
from diffusers import StableDiffusionPipeline
import torch
from typing import Dict, Any, Optional
import os

class StableDiffusionGenerator:
    def __init__(self, model_name: str = "stabilityai/stable-diffusion-3.5-medium"):
        """
        Initialize StableDiffusionGenerator with Hugging Face model.
        
        Args:
            model_name: Hugging Face model name for Stable Diffusion
        """
        self.model_name = model_name
        self.pipeline = None
        self._load_model()

    def _load_model(self):
        """Load the Stable Diffusion model."""
        try:
            print(f"Loading Stable Diffusion model: {self.model_name}")
            self.pipeline = StableDiffusionPipeline.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                use_safetensors=True,
                variant="fp16"
            )
            
            # Move to GPU if available
            if torch.cuda.is_available():
                self.pipeline = self.pipeline.to("cuda")
                print("Stable Diffusion model loaded on GPU")
            else:
                print("Stable Diffusion model loaded on CPU")
                
        except Exception as e:
            print(f"Failed to load Stable Diffusion model: {e}")
            self.pipeline = None

    def generate_image(self, prompt: str, negative_prompt: str = None, 
                      num_inference_steps: int = 30, guidance_scale: float = 7.5,
                      width: int = 1024, height: int = 1024) -> str:
        """
        Generate image using Stable Diffusion.
        
        Args:
            prompt: Text prompt for image generation
            negative_prompt: Negative prompt to avoid certain elements
            num_inference_steps: Number of denoising steps
            guidance_scale: Guidance scale for classifier-free guidance
            width: Image width
            height: Image height
            
        Returns:
            str: Path to generated image
        """
        if not self.pipeline:
            print("Stable Diffusion pipeline not available")
            return "placeholder_image_path.png"
        
        try:
            # Set default negative prompt if not provided
            if negative_prompt is None:
                negative_prompt = "blurry, low quality, distorted, deformed, ugly, bad anatomy"
            
            # Generate image
            image = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height
            ).images[0]
            
            # Save image
            output_dir = "generated_images"
            os.makedirs(output_dir, exist_ok=True)
            
            import uuid
            image_filename = f"sd_generated_{uuid.uuid4().hex[:8]}.png"
            image_path = os.path.join(output_dir, image_filename)
            
            image.save(image_path)
            print(f"Image saved to: {image_path}")
            
            return image_path
            
        except Exception as e:
            print(f"Image generation failed: {e}")
            return "error_image_path.png"

    def generate_with_metadata(self, prompt: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate image with additional metadata.
        
        Args:
            prompt: Text prompt for image generation
            metadata: Additional metadata for generation
            
        Returns:
            Dict: Contains image_path and generation metadata
        """
        # Extract parameters from metadata
        negative_prompt = metadata.get('negative_prompt') if metadata else None
        num_steps = metadata.get('num_inference_steps', 30)
        guidance = metadata.get('guidance_scale', 7.5)
        width = metadata.get('width', 1024)
        height = metadata.get('height', 1024)
        
        # Generate image
        image_path = self.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_steps,
            guidance_scale=guidance,
            width=width,
            height=height
        )
        
        return {
            "image_path": image_path,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "generation_params": {
                "num_inference_steps": num_steps,
                "guidance_scale": guidance,
                "width": width,
                "height": height
            }
        }

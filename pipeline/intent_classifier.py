"""
Intent classifier module: Classifies user query intent using LLM and keyword matching.
"""
import openai
from typing import Dict, List

class IntentClassifier:
    def __init__(self, openai_api_key: str = None):
        """
        Initialize IntentClassifier with OpenAI API key.
        
        Args:
            openai_api_key: OpenAI API key for GPT-4-mini
        """
        self.openai_api_key = openai_api_key
        if openai_api_key:
            openai.api_key = openai_api_key
        
        # Keyword mappings for different intents
        self.keyword_mappings = {
            'image': ['그려줘', 'image', '이미지', '그림', 'draw', 'generate image', 'create image'],
            '3d': ['3d', '3D', '입체', 'three dimensional', '3-dimensional', 'stereo'],
            'video': ['동영상', '영상', 'video', '비디오', 'movie', '4d', '4D', '움직이는', '움직임'],
            'text': ['텍스트', 'text', '답변', 'answer', '설명', 'explain', '알려줘', 'tell me']
        }

    def classify(self, query: str) -> str:
        """
        Classify the intent of the query using LLM and keyword matching.
        
        Args:
            query: User input query
            
        Returns:
            str: Intent classification ('text', 'image', '3d', 'video')
        """
        # First try keyword matching for efficiency
        keyword_intent = self._keyword_classify(query)
        if keyword_intent:
            return keyword_intent
        
        # If keyword matching fails, use LLM
        if self.openai_api_key:
            return self._llm_classify(query)
        else:
            # Fallback to keyword matching with more lenient matching
            return self._lenient_keyword_classify(query)

    def _keyword_classify(self, query: str) -> str:
        """
        Classify intent using keyword matching.
        
        Args:
            query: User input query
            
        Returns:
            str: Intent classification or None if no match
        """
        query_lower = query.lower()
        
        for intent, keywords in self.keyword_mappings.items():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    return intent
        
        return None

    def _lenient_keyword_classify(self, query: str) -> str:
        """
        More lenient keyword matching for fallback.
        
        Args:
            query: User input query
            
        Returns:
            str: Intent classification (defaults to 'text')
        """
        query_lower = query.lower()
        
        # Check for image-related words
        image_words = ['그려', '그림', 'draw', 'image', 'picture', 'photo']
        for word in image_words:
            if word in query_lower:
                return 'image'
        
        # Check for 3D-related words
        three_d_words = ['3d', '입체', 'three', 'dimensional']
        for word in three_d_words:
            if word in query_lower:
                return '3d'
        
        # Check for video-related words
        video_words = ['동영상', '영상', 'video', 'movie', '움직임', '4d']
        for word in video_words:
            if word in query_lower:
                return 'video'
        
        # Default to text
        return 'text'

    def _llm_classify(self, query: str) -> str:
        """
        Classify intent using GPT-4-mini.
        
        Args:
            query: User input query
            
        Returns:
            str: Intent classification
        """
        try:
            system_prompt = """
            You are an intent classifier for a chatbot pipeline. 
            Classify the user's query into one of these categories:
            
            - 'text': General questions, explanations, information requests
            - 'image': Requests for image generation, drawing, visual content
            - '3d': Requests for 3D models, three-dimensional content
            - 'video': Requests for video generation, moving content, 4D content
            
            Respond with only the category name (text, image, 3d, or video).
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4-0125-preview",  # GPT-4-mini equivalent
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Classify this query: {query}"}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            intent = response.choices[0].message.content.strip().lower()
            
            # Validate the response
            valid_intents = ['text', 'image', '3d', 'video']
            if intent in valid_intents:
                return intent
            else:
                # Fallback to keyword matching if LLM returns invalid intent
                return self._lenient_keyword_classify(query)
                
        except Exception as e:
            print(f"LLM classification failed: {e}")
            # Fallback to keyword matching
            return self._lenient_keyword_classify(query)

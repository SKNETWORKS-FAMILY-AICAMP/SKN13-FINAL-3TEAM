"""
Query analyzer module: Analyzes the query for additional data needs and search sufficiency.
"""
import openai
from typing import Dict, Any, Tuple, List
from . import OPENAI_API_KEY

class QueryAnalyzer:
    def __init__(self, openai_api_key: str = None):
        """
        Initialize QueryAnalyzer with OpenAI API key.
        
        Args:
            openai_api_key: OpenAI API key for analysis
        """
        self.openai_api_key = openai_api_key or OPENAI_API_KEY
        if self.openai_api_key:
            openai.api_key = self.openai_api_key

    def analyze_additional_data_needs(self, query: str) -> bool:
        """
        Analyze if additional data is needed for the query.
        Args:
            query: User input query
        Returns:
            bool: True if additional data is needed, False otherwise
        """
        if not self.openai_api_key:
            # Fallback: assume additional data is needed for complex queries
            return len(query.split()) > 5
        
        try:
            system_prompt = """
            You are a query analyzer. Determine if the user's query requires additional data beyond 
            what might be available in a local knowledge base.
            
            Return 'yes' if the query:
            - Asks about recent events, news, or current information
            - Requires real-time data or external sources
            - Asks about specific details not likely in a local database
            - Needs web search for comprehensive answers
            
            Return 'no' if the query:
            - Asks about general knowledge or facts
            - Can be answered from a local knowledge base
            - Is about historical or static information
            
            Respond with only 'yes' or 'no'.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {query}"}
                ],
                max_tokens=5,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip().lower()
            return result == 'yes'
            
        except Exception as e:
            print(f"Query analysis failed: {e}")
            # Fallback: assume additional data is needed
            return True

    def categorize_image_query(self, query: str) -> Dict[str, Any]:
        """
        Categorize image generation query into different elements.
        
        Args:
            query: User input query for image generation
            
        Returns:
            Dict: Categorized query elements
        """
        if not self.openai_api_key:
            # Fallback categorization
            return self._fallback_categorize(query)
        
        try:
            system_prompt = """
            You are an image query categorizer. Extract and categorize elements from the user's image generation request.
            
            Return a JSON object with the following structure:
            {
                "car_name": "specific car model or brand",
                "design_elements": ["list", "of", "design", "features"],
                "style": "design style (e.g., modern, classic, sporty)",
                "color": "color preferences",
                "perspective": "view angle (e.g., front, side, 3/4 view)",
                "background": "background setting",
                "additional_features": ["any", "other", "relevant", "features"]
            }
            
            If any field is not specified, use null or empty array.
            Focus on Hyundai cars and automotive design elements.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {query}"}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            import json
            result = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                categorized = json.loads(result)
                return categorized
            except json.JSONDecodeError:
                print(f"Failed to parse JSON response: {result}")
                return self._fallback_categorize(query)
                
        except Exception as e:
            print(f"Query categorization failed: {e}")
            return self._fallback_categorize(query)

    def _fallback_categorize(self, query: str) -> Dict[str, Any]:
        """
        Fallback categorization using simple keyword matching.
        
        Args:
            query: User input query
            
        Returns:
            Dict: Basic categorization
        """
        query_lower = query.lower()
        
        # Extract car name
        car_name = None
        hyundai_models = ['아반떼', '쏘나타', '그랜저', '투싼', '싼타페', '팰리세이드', '아이오닉', '캐스퍼']
        for model in hyundai_models:
            if model in query_lower:
                car_name = model
                break
        
        # Extract design elements
        design_elements = []
        design_keywords = ['suv', '세단', '해치백', '쿠페', '컨버터블', '전기차', '하이브리드']
        for keyword in design_keywords:
            if keyword in query_lower:
                design_elements.append(keyword)
        
        # Extract style
        style = None
        style_keywords = {
            'modern': ['모던', '현대적', '미래적'],
            'classic': ['클래식', '고전적'],
            'sporty': ['스포티', '운동성', '성능']
        }
        for style_name, keywords in style_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                style = style_name
                break
        
        return {
            "car_name": car_name,
            "design_elements": design_elements,
            "style": style,
            "color": None,
            "perspective": None,
            "background": None,
            "additional_features": []
        }

    def analyze_search_sufficiency(self, query: str, search_results: list) -> Tuple[bool, str]:
        """
        Analyze if the search results are sufficient for answering the query.
        
        Args:
            query: Original user query
            search_results: List of search results from Qdrant
            
        Returns:
            Tuple[bool, str]: (is_sufficient, refined_query)
        """
        if not search_results:
            return False, self._refine_query(query)
        
        if not self.openai_api_key:
            # Fallback: check if we have any results
            return len(search_results) > 0, query
        
        try:
            # Prepare search results summary
            results_summary = "\n".join([
                f"Result {i+1}: {result.get('content', '')[:200]}..."
                for i, result in enumerate(search_results[:3])  # Top 3 results
            ])
            
            system_prompt = """
            You are a search sufficiency analyzer. Determine if the search results are sufficient to answer the user's query.
            
            Return 'sufficient' if the results contain enough relevant information to provide a comprehensive answer.
            Return 'insufficient' if the results are lacking or irrelevant.
            
            If insufficient, also provide a refined query that would help find better results.
            Format your response as: 'sufficient' or 'insufficient: refined_query_here'
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {query}\n\nSearch Results:\n{results_summary}"}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            if result.startswith('sufficient'):
                return True, query
            elif result.startswith('insufficient:'):
                refined_query = result.split(':', 1)[1].strip()
                return False, refined_query
            else:
                return False, self._refine_query(query)
                
        except Exception as e:
            print(f"Search sufficiency analysis failed: {e}")
            return False, self._refine_query(query)

    def _refine_query(self, original_query: str) -> str:
        """
        Refine the query to improve search results.
        
        Args:
            original_query: Original user query
            
        Returns:
            str: Refined query
        """
        if not self.openai_api_key:
            # Simple fallback: add more specific terms
            return f"{original_query} detailed information"
        
        try:
            system_prompt = """
            You are a query refinement expert. Improve the user's query to get better search results.
            
            Make the query:
            - More specific and detailed
            - Include relevant keywords
            - Focus on the core information needed
            
            Return only the refined query.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Original query: {original_query}"}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Query refinement failed: {e}")
            return f"{original_query} detailed information"

    def analyze_answer_quality(self, query: str, answer: str) -> bool:
        """
        Analyze if the generated answer is correct and relevant to the query.
        
        Args:
            query: Original user query
            answer: Generated answer
            
        Returns:
            bool: True if answer is correct/relevant, False otherwise
        """
        if not self.openai_api_key:
            # Fallback: check if answer is not empty and contains relevant words
            query_words = set(query.lower().split())
            answer_words = set(answer.lower().split())
            return len(answer) > 10 and len(query_words.intersection(answer_words)) > 0
        
        try:
            system_prompt = """
            You are an answer quality analyzer. Determine if the generated answer is correct and relevant to the user's query.
            
            Return 'yes' if the answer:
            - Directly addresses the query
            - Contains relevant and accurate information
            - Is comprehensive enough
            
            Return 'no' if the answer:
            - Is irrelevant or off-topic
            - Contains incorrect information
            - Is too vague or incomplete
            
            Respond with only 'yes' or 'no'.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {query}\n\nAnswer: {answer}"}
                ],
                max_tokens=5,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip().lower()
            return result == 'yes'
            
        except Exception as e:
            print(f"Answer quality analysis failed: {e}")
            # Fallback: assume answer is good if it's not empty
            return len(answer.strip()) > 10

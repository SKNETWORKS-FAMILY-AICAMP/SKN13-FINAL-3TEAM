"""
Pipeline Manager: Controls the overall pipeline flow and module orchestration using LangGraph.
"""
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from typing import Dict, Any, TypedDict
from .chat_interface import ChatInterface
from .intent_classifier import IntentClassifier
from .query_analyzer import QueryAnalyzer
from .mcp_server.mcp_text import MCPTextQA
from .mcp_server.mcp_websearch import MCPWebSearch
from .exaone.generate_answer import ExaoneAnswerGenerator
from .exaone.generate_sd_query import ExaoneSDQueryGenerator
from .vector_db.qdrant_client import QdrantClient
from .image_pipeline.stable_diffusion import StableDiffusionGenerator
from .image_pipeline.trellis_shapee import ThreeDImageGenerator
from .image_pipeline.ltx_video import FourDVideoGenerator
from .image_pipeline.image_db import ImageDB
from .utils.logger import get_logger
from . import OPENAI_API_KEY, SERPAPI_KEY

class PipelineState(TypedDict):
    """State for the pipeline."""
    query: str
    intent: str
    response: str
    image: str
    video: str
    metadata: Dict[str, Any]
    search_results: list
    web_data: str
    refined_query: str
    answer_quality: bool
    categorized_query: Dict[str, Any]
    creative_context: str
    sd_prompt: str
    sd_explanation: str
    image_explanation: str

class PipelineManager:
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.chat = ChatInterface()
        self.intent_classifier = IntentClassifier(openai_api_key=OPENAI_API_KEY)
        self.query_analyzer = QueryAnalyzer(openai_api_key=OPENAI_API_KEY)
        self.mcp_text = MCPTextQA()
        self.mcp_web = MCPWebSearch(serpapi_key=SERPAPI_KEY)
        self.exaone_answer = ExaoneAnswerGenerator()  # No API key needed for Hugging Face model
        self.exaone_sd = ExaoneSDQueryGenerator()
        self.qdrant = QdrantClient()
        self.stable_diffusion = StableDiffusionGenerator()
        self.three_d = ThreeDImageGenerator()
        self.four_d = FourDVideoGenerator()
        self.image_db = ImageDB()
        
        # Build LangGraph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph pipeline."""
        workflow = StateGraph(PipelineState)
        
        # Add nodes for text processing
        workflow.add_node("classify_intent", self._classify_intent_node)
        workflow.add_node("analyze_query", self._analyze_query_node)
        workflow.add_node("web_search", self._web_search_node)
        workflow.add_node("qdrant_search", self._qdrant_search_node)
        workflow.add_node("refine_query", self._refine_query_node)
        workflow.add_node("generate_answer", self._generate_answer_node)
        workflow.add_node("analyze_answer", self._analyze_answer_node)
        
        # Add nodes for image processing
        workflow.add_node("categorize_image_query", self._categorize_image_query_node)
        workflow.add_node("creative_web_search", self._creative_web_search_node)
        workflow.add_node("generate_sd_query", self._generate_sd_query_node)
        workflow.add_node("generate_image", self._generate_image_node)
        workflow.add_node("generate_image_explanation", self._generate_image_explanation_node)
        
        # Add nodes for other intents
        workflow.add_node("process_3d", self._process_3d_node)
        workflow.add_node("process_video", self._process_video_node)
        
        # Add conditional edges for text processing
        workflow.add_conditional_edges(
            "classify_intent",
            self._route_by_intent,
            {
                "text": "analyze_query",
                "image": "categorize_image_query", 
                "3d": "process_3d",
                "video": "process_video"
            }
        )
        
        # Add conditional edges for query analysis
        workflow.add_conditional_edges(
            "analyze_query",
            self._route_by_data_needs,
            {
                "web_search": "web_search",
                "qdrant_search": "qdrant_search"
            }
        )
        
        # Add edges for text processing flow
        workflow.add_edge("web_search", "generate_answer")
        workflow.add_edge("qdrant_search", "generate_answer")
        workflow.add_edge("refine_query", "qdrant_search")
        workflow.add_edge("generate_answer", "analyze_answer")
        
        # Add conditional edges for answer analysis
        workflow.add_conditional_edges(
            "analyze_answer",
            self._route_by_answer_quality,
            {
                "accept": END,
                "refine": "refine_query"
            }
        )
        
        # Add edges for image processing flow
        workflow.add_edge("categorize_image_query", "creative_web_search")
        workflow.add_edge("creative_web_search", "generate_sd_query")
        workflow.add_edge("generate_sd_query", "generate_image")
        workflow.add_edge("generate_image", "generate_image_explanation")
        workflow.add_edge("generate_image_explanation", END)
        
        # Add end edges for other intents
        workflow.add_edge("process_3d", END)
        workflow.add_edge("process_video", END)
        
        return workflow.compile()

    def _classify_intent_node(self, state: PipelineState) -> PipelineState:
        """Classify the intent of the query."""
        self.logger.info(f"Classifying intent for query: {state['query']}")
        intent = self.intent_classifier.classify(state['query'])
        state['intent'] = intent
        self.logger.info(f"Classified intent: {intent}")
        return state

    def _route_by_intent(self, state: PipelineState) -> str:
        """Route to appropriate node based on intent."""
        return state['intent']

    def _analyze_query_node(self, state: PipelineState) -> PipelineState:
        """Analyze if additional data is needed."""
        self.logger.info("Analyzing query for additional data needs")
        needs_additional_data = self.query_analyzer.analyze_additional_data_needs(state['query'])
        
        if needs_additional_data:
            state['metadata']['data_source'] = 'web_search'
        else:
            state['metadata']['data_source'] = 'qdrant_search'
        
        self.logger.info(f"Data source determined: {state['metadata']['data_source']}")
        return state

    def _route_by_data_needs(self, state: PipelineState) -> str:
        """Route based on data needs analysis."""
        return state['metadata']['data_source']

    def _web_search_node(self, state: PipelineState) -> PipelineState:
        """Perform web search for additional data."""
        self.logger.info("Performing web search")
        web_results = self.mcp_web.search(state['query'])
        
        # Extract relevant information from web results
        if isinstance(web_results, dict) and 'organic_results' in web_results:
            snippets = []
            for result in web_results['organic_results'][:3]:  # Top 3 results
                if 'snippet' in result:
                    snippets.append(result['snippet'])
            state['web_data'] = " ".join(snippets)
        else:
            state['web_data'] = str(web_results)
        
        self.logger.info(f"Web search completed, data length: {len(state['web_data'])}")
        return state

    def _qdrant_search_node(self, state: PipelineState) -> PipelineState:
        """Search Qdrant vector database."""
        self.logger.info("Searching Qdrant database")
        search_results = self.qdrant.retrieve(state['query'])
        state['search_results'] = search_results
        
        # Analyze if search results are sufficient
        is_sufficient, refined_query = self.query_analyzer.analyze_search_sufficiency(
            state['query'], search_results
        )
        
        if not is_sufficient:
            state['refined_query'] = refined_query
            state['metadata']['needs_refinement'] = True
            self.logger.info(f"Search results insufficient, refined query: {refined_query}")
        else:
            state['metadata']['needs_refinement'] = False
            self.logger.info("Search results sufficient")
        
        return state

    def _refine_query_node(self, state: PipelineState) -> PipelineState:
        """Refine the query for better search results."""
        self.logger.info("Refining query")
        if 'refined_query' in state:
            state['query'] = state['refined_query']
        else:
            state['query'] = self.query_analyzer._refine_query(state['query'])
        
        self.logger.info(f"Query refined to: {state['query']}")
        return state

    def _generate_answer_node(self, state: PipelineState) -> PipelineState:
        """Generate answer using EXAONE."""
        self.logger.info("Generating answer with EXAONE")
        
        # Prepare context from search results or web data
        context = ""
        if state['metadata']['data_source'] == 'web_search':
            context = state.get('web_data', '')
        else:
            # Combine search results
            search_contents = [result.get('content', '') for result in state.get('search_results', [])]
            context = " ".join(search_contents)
        
        # Generate answer
        answer = self.exaone_answer.generate(state['query'], context)
        state['response'] = answer
        
        self.logger.info(f"Answer generated, length: {len(answer)}")
        return state

    def _analyze_answer_node(self, state: PipelineState) -> PipelineState:
        """Analyze answer quality."""
        self.logger.info("Analyzing answer quality")
        is_good = self.query_analyzer.analyze_answer_quality(state['query'], state['response'])
        state['answer_quality'] = is_good
        
        if is_good:
            self.logger.info("Answer quality: ACCEPTED")
        else:
            self.logger.info("Answer quality: NEEDS REFINEMENT")
        
        return state

    def _route_by_answer_quality(self, state: PipelineState) -> str:
        """Route based on answer quality analysis."""
        if state['answer_quality']:
            return "accept"
        else:
            return "refine"

    def _categorize_image_query_node(self, state: PipelineState) -> PipelineState:
        """Categorize image generation query."""
        self.logger.info("Categorizing image query")
        categorized = self.query_analyzer.categorize_image_query(state['query'])
        state['categorized_query'] = categorized
        
        self.logger.info(f"Query categorized: {categorized}")
        return state

    def _creative_web_search_node(self, state: PipelineState) -> PipelineState:
        """Perform creative web search for design inspiration."""
        self.logger.info("Performing creative web search")
        
        # Build creative search query based on categorized elements
        categorized = state['categorized_query']
        car_name = categorized.get('car_name', 'Hyundai')
        design_elements = categorized.get('design_elements', [])
        style = categorized.get('style', 'modern')
        
        # Create creative search query
        search_terms = [car_name, style, "automotive design", "car design trends"]
        if design_elements:
            search_terms.extend(design_elements)
        
        creative_query = f"{' '.join(search_terms)} design inspiration automotive trends"
        
        # Perform web search
        web_results = self.mcp_web.search(creative_query)
        
        # Extract creative context
        if isinstance(web_results, dict) and 'organic_results' in web_results:
            snippets = []
            for result in web_results['organic_results'][:5]:  # Top 5 results for creativity
                if 'snippet' in result:
                    snippets.append(result['snippet'])
            state['creative_context'] = " ".join(snippets)
        else:
            state['creative_context'] = f"Creative inspiration for {car_name} {style} design"
        
        self.logger.info(f"Creative context generated, length: {len(state['creative_context'])}")
        return state

    def _generate_sd_query_node(self, state: PipelineState) -> PipelineState:
        """Generate Stable Diffusion query using EXAONE."""
        self.logger.info("Generating SD query with EXAONE")
        
        categorized = state['categorized_query']
        creative_context = state.get('creative_context', '')
        
        # Generate SD query
        sd_result = self.exaone_sd.generate_sd_query(categorized, creative_context)
        
        state['sd_prompt'] = sd_result.get('prompt', '')
        state['sd_explanation'] = sd_result.get('explanation', '')
        
        # Optimize prompt for CLIP tokens
        optimized_prompt = self.exaone_sd.optimize_for_clip_tokens(state['sd_prompt'])
        state['sd_prompt'] = optimized_prompt
        
        self.logger.info(f"SD prompt generated: {state['sd_prompt'][:100]}...")
        return state

    def _generate_image_node(self, state: PipelineState) -> PipelineState:
        """Generate image using Stable Diffusion 3.5 Medium."""
        self.logger.info("Generating image with Stable Diffusion 3.5 Medium")
        
        prompt = state['sd_prompt']
        
        # Generate image using Stable Diffusion 3.5 Medium
        image_result = self.stable_diffusion.generate_with_metadata(prompt)
        
        state['image'] = image_result['image_path']
        state['metadata']['sd_generation_params'] = image_result['generation_params']
        
        self.logger.info(f"Image generated: {state['image']}")
        return state

    def _generate_image_explanation_node(self, state: PipelineState) -> PipelineState:
        """Generate human-readable explanation for the generated image."""
        self.logger.info("Generating image explanation with EXAONE")
        
        sd_prompt = state['sd_prompt']
        original_query = state['query']
        categorized_elements = state['categorized_query']
        
        # Generate explanation using EXAONE
        explanation = self.exaone_answer.generate_sd_explanation(
            sd_prompt, original_query, categorized_elements
        )
        
        state['image_explanation'] = explanation
        state['response'] = explanation  # Set as response for user display
        
        self.logger.info(f"Image explanation generated: {explanation[:100]}...")
        return state

    def _process_3d_node(self, state: PipelineState) -> PipelineState:
        """Process 3D generation queries."""
        self.logger.info("Processing 3D query")
        # TODO: Implement 3D generation logic
        state['image'] = "3D image placeholder"
        return state

    def _process_video_node(self, state: PipelineState) -> PipelineState:
        """Process video generation queries."""
        self.logger.info("Processing video query")
        # TODO: Implement video generation logic
        state['video'] = "Video placeholder"
        return state

    def run(self, user_query: str) -> Dict[str, Any]:
        """Run the pipeline with user query."""
        self.logger.info('Pipeline started.')
        
        # Initialize state
        initial_state = PipelineState(
            query=user_query,
            intent="",
            response="",
            image="",
            video="",
            metadata={},
            search_results=[],
            web_data="",
            refined_query="",
            answer_quality=False,
            categorized_query={},
            creative_context="",
            sd_prompt="",
            sd_explanation="",
            image_explanation=""
        )
        
        # Execute graph
        result = self.graph.invoke(initial_state)
        
        self.logger.info('Pipeline finished.')
        return result

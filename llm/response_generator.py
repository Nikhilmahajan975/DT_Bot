"""
AI Response Generator Module - Multi-Provider Support
Supports: OpenAI, Anthropic Claude, Google Gemini, Ollama (Local/Free), and Fallback
"""
from typing import Dict, List, Optional
from config.settings import config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class AIResponseGenerator:
    """Generate conversational responses using multiple AI providers"""
    
    def __init__(self, provider: str = None):
        """
        Initialize AI provider
        
        Args:
            provider: 'openai', 'anthropic', 'gemini', 'ollama', or 'fallback'
                     If None, auto-detects based on available API keys
        """
        self.provider = provider or self._detect_provider()
        self.client = None
        self.model = None
        
        # Initialize the selected provider
        self._initialize_provider()
        
        logger.info(f"AI Provider initialized: {self.provider}")
    
    def _detect_provider(self) -> str:
        """Auto-detect which AI provider to use based on available API keys"""
        
        # Check for API keys in order of preference
        if hasattr(config, 'ANTHROPIC_API_KEY') and config.ANTHROPIC_API_KEY:
            return 'anthropic'
        elif hasattr(config, 'GEMINI_API_KEY') and config.GEMINI_API_KEY:
            return 'gemini'
        elif hasattr(config, 'OPENAI_API_KEY') and config.OPENAI_API_KEY:
            return 'openai'
        elif hasattr(config, 'OLLAMA_ENABLED') and config.OLLAMA_ENABLED:
            return 'ollama'
        else:
            logger.warning("No AI API keys found, using fallback template responses")
            return 'fallback'
    
    def _initialize_provider(self):
        """Initialize the specific AI provider"""
        
        if self.provider == 'openai':
            self._init_openai()
        elif self.provider == 'anthropic':
            self._init_anthropic()
        elif self.provider == 'gemini':
            self._init_gemini()
        elif self.provider == 'ollama':
            self._init_ollama()
        else:
            logger.info("Using fallback template responses (no AI provider)")
    
    def _init_openai(self):
        """Initialize OpenAI (GPT-4, GPT-3.5)"""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            self.model = getattr(config, 'OPENAI_MODEL', 'gpt-3.5-turbo')  # Default to cheaper model
            logger.info(f"OpenAI initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            self.provider = 'fallback'
    
    def _init_anthropic(self):
        """Initialize Anthropic Claude"""
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            self.model = getattr(config, 'ANTHROPIC_MODEL', 'claude-3-haiku-20240307')  # Cheapest Claude
            logger.info(f"Anthropic initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic: {e}")
            self.provider = 'fallback'
    
    def _init_gemini(self):
        """Initialize Google Gemini (Free tier available!)"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.model = getattr(config, 'GEMINI_MODEL', 'gemini-pro')  # Free model
            self.client = genai.GenerativeModel(self.model)
            logger.info(f"Google Gemini initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.provider = 'fallback'
    
    def _init_ollama(self):
        """Initialize Ollama (100% Free, runs locally!)"""
        try:
            import requests
            # Test Ollama connection
            ollama_url = getattr(config, 'OLLAMA_URL', 'http://localhost:11434')
            response = requests.get(f"{ollama_url}/api/tags", timeout=2)
            
            if response.status_code == 200:
                self.client = ollama_url
                self.model = getattr(config, 'OLLAMA_MODEL', 'llama2')  # Default model
                logger.info(f"Ollama initialized with model: {self.model}")
            else:
                raise Exception("Ollama server not responding")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")
            logger.info("Install Ollama from https://ollama.ai for free local AI")
            self.provider = 'fallback'
    
    def generate_service_analysis(
        self,
        service_name: str,
        metrics: Dict,
        problems: List[Dict],
        insights: Dict,
        timeframe: str
    ) -> str:
        """
        Generate a natural language analysis of service health
        
        Args:
            service_name: Name of the service
            metrics: Metrics dictionary
            problems: List of problems
            insights: Analysis insights
            timeframe: Time period analyzed
            
        Returns:
            Natural language response
        """
        # Build context
        context = self._build_context(service_name, metrics, problems, insights, timeframe)
        
        # System prompt
        system_prompt = """You are a Dynatrace monitoring expert and helpful assistant. 
        Your role is to analyze service metrics and problems, then provide clear, 
        actionable insights in a conversational tone. Be concise but thorough.
        Focus on what's important and provide recommendations when issues are detected."""
        
        # User prompt
        user_prompt = f"""Analyze this service data and provide a summary:

{context}

Provide a clear, professional analysis that includes:
1. Overall health status
2. Key metrics summary
3. Any concerns or issues
4. Actionable recommendations (if applicable)

Keep it concise but informative."""
        
        # Call the appropriate provider
        try:
            if self.provider == 'openai':
                return self._call_openai(system_prompt, user_prompt)
            elif self.provider == 'anthropic':
                return self._call_anthropic(system_prompt, user_prompt)
            elif self.provider == 'gemini':
                return self._call_gemini(system_prompt, user_prompt)
            elif self.provider == 'ollama':
                return self._call_ollama(system_prompt, user_prompt)
            else:
                return self._fallback_response(service_name, metrics, problems, insights)
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._fallback_response(service_name, metrics, problems, insights)
    
    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    
    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Call Anthropic Claude API"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.content[0].text.strip()
    
    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Call Google Gemini API"""
        # Gemini doesn't have separate system prompt, combine them
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = self.client.generate_content(full_prompt)
        return response.text.strip()
    
    def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """Call Ollama local API"""
        import requests
        import json
        
        response = requests.post(
            f"{self.client}/api/generate",
            json={
                "model": self.model,
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['response'].strip()
        else:
            raise Exception(f"Ollama API error: {response.status_code}")
    
    def _build_context(
        self,
        service_name: str,
        metrics: Dict,
        problems: List[Dict],
        insights: Dict,
        timeframe: str
    ) -> str:
        """Build context string for the AI"""
        context_parts = [
            f"Service: {service_name}",
            f"Time Period: {timeframe}",
            "",
            "Metrics:",
            f"- Error Count: {metrics.get('error_count', 'N/A')}",
            f"- Response Time: {metrics.get('response_time', 'N/A')} ms",
            f"- Request Count: {metrics.get('request_count', 'N/A')}",
            f"- Failure Rate: {metrics.get('failure_rate', 'N/A')}%",
            "",
            f"Problems Detected: {len(problems)}",
        ]
        
        if problems:
            context_parts.append("Problem Details:")
            for i, prob in enumerate(problems[:3], 1):
                context_parts.append(
                    f"  {i}. {prob.get('title', 'Unknown')} ({prob.get('status', 'Unknown')})"
                )
        
        if insights.get("concerns"):
            context_parts.append("")
            context_parts.append("Concerns:")
            for concern in insights["concerns"]:
                context_parts.append(f"- {concern}")
        
        return "\n".join(context_parts)
    
    def _fallback_response(
        self,
        service_name: str,
        metrics: Dict,
        problems: List[Dict],
        insights: Dict
    ) -> str:
        """Generate a template-based response as fallback"""
        status = insights.get("status", "unknown")
        
        response_parts = [
            f"**Service Analysis: {service_name}**",
            "",
            f"**Status:** {status.upper()}",
            "",
            "**Metrics:**"
        ]
        
        for key, value in metrics.items():
            formatted_key = key.replace("_", " ").title()
            response_parts.append(f"- {formatted_key}: {value}")
        
        if problems:
            response_parts.append("")
            response_parts.append(f"**Problems Found:** {len(problems)}")
            for prob in problems[:3]:
                response_parts.append(f"- {prob.get('title', 'Unknown')}")
        else:
            response_parts.append("")
            response_parts.append("**No major problems detected.**")
        
        if insights.get("recommendations"):
            response_parts.append("")
            response_parts.append("**Recommendations:**")
            for rec in insights["recommendations"]:
                response_parts.append(f"- {rec}")
        
        return "\n".join(response_parts)
    
    def generate_service_list_response(self, services: List[Dict]) -> str:
        """
        Generate a response listing available services
        
        Args:
            services: List of service entities
            
        Returns:
            Formatted service list
        """
        if not services:
            return "No services found in your Dynatrace environment."
        
        response_parts = [
            f"I found **{len(services)}** services in your environment:",
            ""
        ]
        
        for i, service in enumerate(services[:20], 1):
            name = service.get("displayName", service.get("entityId", "Unknown"))
            service_type = service.get("properties", {}).get("serviceType", "Unknown")
            response_parts.append(f"{i}. {name} ({service_type})")
        
        if len(services) > 20:
            response_parts.append(f"\n...and {len(services) - 20} more services.")
        
        return "\n".join(response_parts)

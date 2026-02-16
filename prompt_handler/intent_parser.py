"""
AI-Powered Intent Parser Module
Uses AI to understand user queries naturally instead of hardcoded patterns
"""
import re
from typing import Dict, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class AIIntentParser:
    """
    AI-powered intent parser that uses LLM to understand user queries
    Falls back to pattern matching if AI is unavailable
    """
    
    def __init__(self, ai_client=None):
        """
        Initialize the parser
        
        Args:
            ai_client: Optional AI client for intelligent parsing
        """
        self.ai_client = ai_client
        self.use_ai = ai_client is not None
    
    def parse(self, user_input: str) -> Optional[Dict]:
        """
        Parse user input and extract intent using AI or pattern matching
        
        Args:
            user_input: Raw user query
            
        Returns:
            Intent dictionary with type, service_name, timeframe, etc.
        """
        if not user_input or not user_input.strip():
            return None
        
        user_input_clean = user_input.strip()
        
        # Try AI-powered parsing first
        if self.use_ai:
            try:
                intent = self._parse_with_ai(user_input_clean)
                if intent:
                    logger.info(f"AI parsed intent: {intent}")
                    return intent
            except Exception as e:
                logger.warning(f"AI parsing failed, falling back to patterns: {e}")
        
        # Fallback to pattern-based parsing
        intent = self._parse_with_patterns(user_input_clean)
        logger.info(f"Pattern parsed intent: {intent}")
        return intent
    
    def _parse_with_ai(self, user_input: str) -> Optional[Dict]:
        """
        Use AI to understand the user's intent
        
        Args:
            user_input: User's query
            
        Returns:
            Parsed intent dictionary
        """
        system_prompt = """You are an intent classifier for a Dynatrace monitoring chatbot.
Your job is to extract structured information from user queries.

Available intent types:
- check_abnormality: User wants to check service health, issues, problems, errors
- list_services: User wants to see all available services
- service_details: User wants detailed info about a specific service
- metrics_analysis: User wants to analyze performance metrics
- compare_services: User wants to compare multiple services
- troubleshoot: User wants help diagnosing an issue
- general_question: General question about monitoring or the system

Extract:
1. intent_type: One of the above types
2. service_name: The service name mentioned (if any)
3. timeframe: Time period like "2h", "30m", "7d" (default: "2h")
4. additional_context: Any other relevant information

Respond ONLY with valid JSON in this exact format:
{
  "intent_type": "check_abnormality",
  "service_name": "ordercontroller",
  "timeframe": "2h",
  "additional_context": ""
}

If no service name is mentioned, use null for service_name.
If no timeframe is mentioned, use "2h".
"""
        
        user_prompt = f"User query: {user_input}"
        
        try:
            # Call AI provider (works with any provider from our multi-provider setup)
            response = self._call_ai(system_prompt, user_prompt)
            
            # Parse JSON response
            import json
            # Clean up response (remove markdown code blocks if present)
            response_clean = response.strip()
            if response_clean.startswith('```'):
                # Remove ```json and ``` markers
                response_clean = re.sub(r'^```json\s*', '', response_clean)
                response_clean = re.sub(r'```\s*$', '', response_clean)
            
            intent_data = json.loads(response_clean)
            
            # Validate and normalize
            return {
                "type": intent_data.get("intent_type", "general_question"),
                "service_name": intent_data.get("service_name"),
                "timeframe": intent_data.get("timeframe", "2h"),
                "additional_context": intent_data.get("additional_context", ""),
                "raw_query": user_input
            }
            
        except Exception as e:
            logger.error(f"AI intent parsing error: {e}")
            return None
    
    def _call_ai(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call the AI provider to get intent
        Works with any provider (Gemini, Ollama, Claude, OpenAI)
        """
        provider = self.ai_client.provider
        
        if provider == 'openai':
            response = self.ai_client.client.chat.completions.create(
                model=self.ai_client.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent parsing
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        
        elif provider == 'anthropic':
            response = self.ai_client.client.messages.create(
                model=self.ai_client.model,
                max_tokens=200,
                temperature=0.3,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text.strip()
        
        elif provider == 'gemini':
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.ai_client.client.generate_content(full_prompt)
            return response.text.strip()
        
        elif provider == 'ollama':
            import requests
            response = requests.post(
                f"{self.ai_client.client}/api/generate",
                json={
                    "model": self.ai_client.model,
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()['response'].strip()
            else:
                raise Exception(f"Ollama error: {response.status_code}")
        
        else:
            raise Exception(f"Unsupported AI provider: {provider}")
    
    def _parse_with_patterns(self, text: str) -> Optional[Dict]:
        """
        Fallback pattern-based parsing (more flexible than before)
        
        Args:
            text: Lowercased user input
            
        Returns:
            Intent dictionary or None
        """
        text_lower = text.lower()
        
        # Detect intent type with more flexible patterns
        intent_type = self._detect_intent_type_flexible(text_lower)
        
        # Extract entities
        service_name = self._extract_service_name_flexible(text_lower)
        timeframe = self._extract_timeframe_flexible(text_lower)
        
        if not intent_type:
            intent_type = "general_question"
        
        return {
            "type": intent_type,
            "service_name": service_name,
            "timeframe": timeframe,
            "additional_context": "",
            "raw_query": text
        }
    
    def _detect_intent_type_flexible(self, text: str) -> str:
        """
        Detect intent type with flexible matching
        """
        # Keywords for each intent (expanded and more flexible)
        intent_keywords = {
            "check_abnormality": [
                'check', 'status', 'health', 'issue', 'problem', 'error', 
                'alert', 'wrong', 'failing', 'down', 'broken', 'not working',
                'abnormal', 'anomaly', 'investigate', 'look into', 'whats up with',
                'how is', 'how are', 'happening with', 'going on'
            ],
            "list_services": [
                'list', 'show all', 'show me', 'get all', 'what services',
                'available services', 'which services', 'all services',
                'what do we have', 'what applications', 'show services'
            ],
            "service_details": [
                'details about', 'info about', 'information on', 'tell me about',
                'what is', 'describe', 'explain', 'more about'
            ],
            "metrics_analysis": [
                'metrics', 'performance', 'stats', 'statistics', 'kpi',
                'how fast', 'response time', 'latency', 'throughput',
                'cpu', 'memory', 'disk', 'analyze', 'analysis'
            ],
            "compare_services": [
                'compare', 'comparison', 'versus', 'vs', 'difference between',
                'which is better', 'against', 'relative to'
            ],
            "troubleshoot": [
                'troubleshoot', 'diagnose', 'debug', 'fix', 'solve',
                'why is', 'root cause', 'reason for', 'causing',
                'slow', 'help with', 'figure out'
            ]
        }
        
        # Score each intent type
        scores = {}
        for intent, keywords in intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[intent] = score
        
        # Return highest scoring intent
        if scores:
            return max(scores, key=scores.get)
        
        return "general_question"
    
    def _extract_service_name_flexible(self, text: str) -> Optional[str]:
        """
        Extract service name with flexible patterns
        """
        # Pattern 1: "for <service>" or "for: <service>"
        match = re.search(r'\bfor[:\s]+([a-zA-Z0-9\-_.]+)', text)
        if match:
            return match.group(1)
        
        # Pattern 2: "of <service>" or "about <service>"
        match = re.search(r'\b(?:of|about)[:\s]+([a-zA-Z0-9\-_.]+)', text)
        if match:
            return match.group(1)
        
        # Pattern 3: "service <service>" or "<service> service"
        match = re.search(r'\bservice[:\s]+([a-zA-Z0-9\-_.]+)', text)
        if match:
            return match.group(1)
        
        match = re.search(r'([a-zA-Z0-9\-_.]+)\s+service\b', text)
        if match:
            return match.group(1)
        
        # Pattern 4: Quoted names
        match = re.search(r'["\']([a-zA-Z0-9\-_.]+)["\']', text)
        if match:
            return match.group(1)
        
        # Pattern 5: Common service patterns (api, controller, etc.)
        service_patterns = [
            r'\b([a-zA-Z0-9\-_]+(?:api|service|controller|backend|frontend|gateway|proxy))\b',
            r'\b(?:api|service|controller)[-_]([a-zA-Z0-9\-_]+)\b'
        ]
        for pattern in service_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        # Pattern 6: After action words
        action_words = ['check', 'analyze', 'monitor', 'debug', 'fix', 'look', 'see', 'show']
        for action in action_words:
            pattern = rf'\b{action}\s+(?:the\s+)?([a-zA-Z0-9\-_.]+)\b'
            match = re.search(pattern, text)
            if match:
                candidate = match.group(1)
                # Avoid common words
                if candidate not in ['service', 'services', 'status', 'health', 'metrics', 'issues']:
                    return candidate
        
        return None
    
    def _extract_timeframe_flexible(self, text: str) -> str:
        """
        Extract timeframe with flexible patterns
        """
        # Pattern 1: Explicit format "2h", "30m", "7d"
        match = re.search(r'\b(\d+)\s*([mhdw])\b', text)
        if match:
            return f"{match.group(1)}{match.group(2)}"
        
        # Pattern 2: "last/past X minutes/hours/days"
        match = re.search(
            r'\b(?:last|past|previous|recent)\s+(\d+)\s*(minute|hour|day|week)s?\b',
            text
        )
        if match:
            value = match.group(1)
            unit = match.group(2)[0]  # First letter
            return f"{value}{unit}"
        
        # Pattern 3: "in the last X"
        match = re.search(
            r'\bin\s+the\s+(?:last|past)\s+(\d+)\s*(minute|hour|day|week)s?\b',
            text
        )
        if match:
            value = match.group(1)
            unit = match.group(2)[0]
            return f"{value}{unit}"
        
        # Pattern 4: Time keywords
        time_keywords = {
            'today': '24h',
            'yesterday': '48h',
            'this week': '7d',
            'this month': '30d',
            'recent': '2h',
            'recently': '2h'
        }
        for keyword, timeframe in time_keywords.items():
            if keyword in text:
                return timeframe
        
        # Default
        return "2h"


# Backward compatible class name
class IntentParser(AIIntentParser):
    """Alias for backward compatibility"""
    pass

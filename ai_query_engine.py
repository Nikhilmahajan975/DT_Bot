"""
AI Query Engine - Universal Question Answering System
Uses knowledge base + AI to answer ANY analytical question about services
"""
import json
import re
from typing import Dict, List, Any, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class AIQueryEngine:
    """
    Intelligent query engine that can answer analytical questions
    by querying the knowledge base and using AI for insights
    """
    
    def __init__(self, knowledge_base, ai_generator):
        self.kb = knowledge_base
        self.ai = ai_generator
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer ANY question about services
        
        Args:
            question: Natural language question
            
        Returns:
            Dict with answer, data, and metadata
        """
        logger.info(f"Processing question: {question}")
        
        # Check if KB is ready
        if not self.kb.is_ready():
            return {
                'answer': "I'm still gathering data from all services. Please wait a moment...",
                'status': 'building',
                'data': None
            }
        
        try:
            # Step 1: Parse question to structured query
            query = self._parse_question_to_query(question)
            logger.info(f"Parsed query: {query}")
            
            # Step 2: Execute query on knowledge base
            data = self._execute_query(query)
            logger.info(f"Query returned {len(data) if isinstance(data, list) else 'aggregate'} results")
            
            # Step 3: Generate natural language answer
            answer = self._generate_answer(question, query, data)
            
            return {
                'answer': answer,
                'status': 'success',
                'data': data,
                'query_type': query.get('action')
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {e}", exc_info=True)
            return {
                'answer': f"I had trouble processing that question. Could you rephrase it?",
                'status': 'error',
                'data': None,
                'error': str(e)
            }
    
    def _parse_question_to_query(self, question: str) -> Dict:
        """
        Parse natural language question to structured query using AI
        """
        # First try pattern matching for common queries
        query = self._pattern_match_query(question)
        if query:
            return query
        
        # Fall back to AI parsing for complex queries
        return self._ai_parse_query(question)
    
    def _pattern_match_query(self, question: str) -> Optional[Dict]:
        """Fast pattern matching for common query types"""
        q_lower = question.lower()
        
        # Ranking queries
        if any(word in q_lower for word in ['highest', 'worst', 'most', 'top']):
            if 'failure' in q_lower or 'fail' in q_lower:
                return {'action': 'rank', 'metric': 'failure_rate', 'order': 'desc', 'limit': 5}
            elif 'error' in q_lower:
                return {'action': 'rank', 'metric': 'error_count', 'order': 'desc', 'limit': 5}
            elif 'slow' in q_lower or 'response' in q_lower:
                return {'action': 'rank', 'metric': 'response_time', 'order': 'desc', 'limit': 5}
            elif 'problem' in q_lower:
                return {'action': 'rank', 'metric': 'problem_count', 'order': 'desc', 'limit': 5}
            elif 'unhealthy' in q_lower or 'bad' in q_lower:
                return {'action': 'rank', 'metric': 'health_score', 'order': 'asc', 'limit': 5}
        
        # Best/healthiest queries
        if any(word in q_lower for word in ['best', 'healthiest', 'lowest']):
            if 'health' in q_lower:
                return {'action': 'rank', 'metric': 'health_score', 'order': 'desc', 'limit': 5}
            elif 'error' in q_lower:
                return {'action': 'rank', 'metric': 'error_count', 'order': 'asc', 'limit': 5}
        
        # Overview/summary queries
        if any(word in q_lower for word in ['overview', 'summary', 'today', 'all', 'everything', 'status']):
            if 'health' in q_lower or 'status' in q_lower or 'overview' in q_lower:
                return {'action': 'aggregate', 'scope': 'all'}
        
        # Filter queries
        if 'with' in q_lower or 'having' in q_lower:
            if 'problem' in q_lower or 'issue' in q_lower:
                return {'action': 'filter', 'condition': 'problem_count > 0'}
            elif 'error' in q_lower:
                # Extract number if present
                numbers = re.findall(r'\d+', question)
                threshold = int(numbers[0]) if numbers else 100
                return {'action': 'filter', 'condition': f'error_count > {threshold}'}
        
        # List queries
        if any(word in q_lower for word in ['show', 'list', 'which']):
            if 'critical' in q_lower:
                return {'action': 'filter', 'condition': "status == 'critical'"}
            elif 'warning' in q_lower:
                return {'action': 'filter', 'condition': "status == 'warning'"}
            elif 'problem' in q_lower:
                return {'action': 'filter', 'condition': 'problem_count > 0'}
        
        # Count queries
        if any(word in q_lower for word in ['how many', 'count']):
            return {'action': 'count', 'scope': 'all'}
        
        return None
    
    def _ai_parse_query(self, question: str) -> Dict:
        """Use AI to parse complex questions"""
        
        system_prompt = """You are a query parser for a Dynatrace monitoring system.
Convert natural language questions to structured queries.

Available query types:
1. rank - Sort services by a metric
2. filter - Filter services by condition
3. aggregate - Get overall statistics
4. compare - Compare specific services
5. count - Count services matching criteria

Available metrics: health_score, failure_rate, error_count, response_time, problem_count
Available statuses: healthy, warning, critical

Return ONLY valid JSON, no other text:
{
  "action": "rank|filter|aggregate|compare|count",
  "metric": "metric_name",
  "order": "desc|asc",
  "condition": "expression",
  "limit": number,
  "services": ["service1", "service2"]
}"""
        
        user_prompt = f"""Question: "{question}"

Examples:
"Which has highest failure?" -> {{"action":"rank","metric":"failure_rate","order":"desc","limit":5}}
"Services with errors>100" -> {{"action":"filter","condition":"error_count > 100"}}
"What's today's health?" -> {{"action":"aggregate","scope":"all"}}
"Show critical services" -> {{"action":"filter","condition":"status == 'critical'"}}

Convert the question to query JSON:"""
        
        try:
            if self.ai.provider == 'fallback':
                # Fallback to pattern matching
                return {'action': 'aggregate', 'scope': 'all'}
            
            response = self._call_ai(system_prompt, user_prompt)
            
            # Clean response
            response = response.strip()
            response = re.sub(r'^```json\s*', '', response)
            response = re.sub(r'```\s*$', '', response)
            
            query = json.loads(response)
            return query
            
        except Exception as e:
            logger.warning(f"AI parsing failed, using fallback: {e}")
            return {'action': 'aggregate', 'scope': 'all'}
    
    def _call_ai(self, system_prompt: str, user_prompt: str) -> str:
        """Call AI provider"""
        provider = self.ai.provider
        
        if provider == 'openai':
            response = self.ai.client.chat.completions.create(
                model=self.ai.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        
        elif provider == 'anthropic':
            response = self.ai.client.messages.create(
                model=self.ai.model,
                max_tokens=300,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            return response.content[0].text.strip()
        
        elif provider == 'gemini':
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.ai.client.generate_content(full_prompt)
            return response.text.strip()
        
        elif provider == 'ollama':
            import requests
            response = requests.post(
                f"{self.ai.client}/api/generate",
                json={
                    "model": self.ai.model,
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()['response'].strip()
        
        return "{}"
    
    def _execute_query(self, query: Dict) -> Any:
        """Execute structured query on knowledge base"""
        action = query.get('action')
        
        if action == 'rank':
            return self._rank_services(query)
        elif action == 'filter':
            return self._filter_services(query)
        elif action == 'aggregate':
            return self._aggregate_stats(query)
        elif action == 'compare':
            return self._compare_services(query)
        elif action == 'count':
            return self._count_services(query)
        else:
            return self._aggregate_stats({'scope': 'all'})
    
    def _rank_services(self, query: Dict) -> List[Dict]:
        """Rank services by metric"""
        metric = query.get('metric', 'health_score')
        order = query.get('order', 'desc')
        limit = query.get('limit', 5)
        
        services = list(self.kb.get_all_services().values())
        
        # Handle nested metrics
        def get_metric_value(service):
            if metric in ['error_count', 'response_time', 'failure_rate', 'request_count']:
                return service['metrics'].get(metric, 0)
            else:
                return service.get(metric, 0)
        
        # Sort
        sorted_services = sorted(
            services,
            key=get_metric_value,
            reverse=(order == 'desc')
        )
        
        return sorted_services[:limit]
    
    def _filter_services(self, query: Dict) -> List[Dict]:
        """Filter services by condition"""
        condition = query.get('condition', '')
        services = list(self.kb.get_all_services().values())
        
        filtered = []
        for service in services:
            if self._evaluate_condition(service, condition):
                filtered.append(service)
        
        return filtered
    
    def _evaluate_condition(self, service: Dict, condition: str) -> bool:
        """Evaluate condition against service"""
        try:
            # Simple condition parser
            condition = condition.strip()
            
            # Handle status comparison
            if "status ==" in condition:
                match = re.search(r"status == ['\"](\w+)['\"]", condition)
                if match:
                    return service['status'] == match.group(1)
            
            # Handle numeric comparisons
            if '>' in condition:
                parts = condition.split('>')
                metric = parts[0].strip()
                threshold = float(parts[1].strip())
                
                if metric in ['error_count', 'response_time', 'failure_rate']:
                    value = service['metrics'].get(metric, 0)
                else:
                    value = service.get(metric, 0)
                
                return isinstance(value, (int, float)) and value > threshold
            
            if '<' in condition:
                parts = condition.split('<')
                metric = parts[0].strip()
                threshold = float(parts[1].strip())
                
                if metric in ['error_count', 'response_time', 'failure_rate']:
                    value = service['metrics'].get(metric, 0)
                else:
                    value = service.get(metric, 0)
                
                return isinstance(value, (int, float)) and value < threshold
            
            return False
            
        except Exception as e:
            logger.warning(f"Condition evaluation error: {e}")
            return False
    
    def _aggregate_stats(self, query: Dict) -> Dict:
        """Get aggregate statistics"""
        return self.kb.get_stats()
    
    def _compare_services(self, query: Dict) -> List[Dict]:
        """Compare specific services"""
        service_names = query.get('services', [])
        services = []
        
        for name in service_names:
            service = self.kb.get_service(name)
            if service:
                services.append(service)
        
        return services
    
    def _count_services(self, query: Dict) -> Dict:
        """Count services"""
        services = list(self.kb.get_all_services().values())
        condition = query.get('condition')
        
        if condition:
            services = [s for s in services if self._evaluate_condition(s, condition)]
        
        return {
            'count': len(services),
            'services': services
        }
    
    def _generate_answer(self, question: str, query: Dict, data: Any) -> str:
        """Generate natural language answer using AI"""
        action = query.get('action')
        
        # Build context for AI
        if action == 'rank':
            context = self._build_ranking_context(data)
        elif action == 'filter':
            context = self._build_filter_context(data)
        elif action == 'aggregate':
            context = self._build_aggregate_context(data)
        elif action == 'compare':
            context = self._build_compare_context(data)
        elif action == 'count':
            context = self._build_count_context(data)
        else:
            context = str(data)
        
        # Generate answer with AI
        if self.ai.provider != 'fallback':
            try:
                answer = self._generate_ai_answer(question, context, action)
                return answer
            except Exception as e:
                logger.warning(f"AI answer generation failed: {e}")
        
        # Fallback to template
        return self._generate_template_answer(question, query, data)
    
    def _build_ranking_context(self, services: List[Dict]) -> str:
        """Build context for ranking results"""
        lines = []
        for i, svc in enumerate(services[:10], 1):
            name = svc['display_name']
            health = svc['health_score']
            status = svc['status']
            problems = svc['problem_count']
            
            metrics = svc['metrics']
            error_count = metrics.get('error_count', 'N/A')
            response_time = metrics.get('response_time', 'N/A')
            failure_rate = metrics.get('failure_rate', 'N/A')
            
            lines.append(
                f"{i}. {name}: health={health}, status={status}, "
                f"errors={error_count}, response={response_time}ms, "
                f"failure={failure_rate}%, problems={problems}"
            )
        
        return "\n".join(lines)
    
    def _build_filter_context(self, services: List[Dict]) -> str:
        """Build context for filtered results"""
        if not services:
            return "No services match the criteria"
        
        lines = [f"Found {len(services)} matching services:"]
        for svc in services[:10]:
            lines.append(f"- {svc['display_name']} ({svc['status']})")
        
        if len(services) > 10:
            lines.append(f"... and {len(services) - 10} more")
        
        return "\n".join(lines)
    
    def _build_aggregate_context(self, stats: Dict) -> str:
        """Build context for aggregate stats"""
        return f"""
Total services: {stats.get('total_services', 0)}
Healthy: {stats.get('healthy_count', 0)} ({stats.get('healthy_percentage', 0):.1f}%)
Warning: {stats.get('warning_count', 0)}
Critical: {stats.get('critical_count', 0)}
Average health score: {stats.get('avg_health_score', 0)}/100
Total problems: {stats.get('total_problems', 0)}
Services with problems: {stats.get('services_with_problems', 0)}
Average errors: {stats.get('avg_error_count', 0)}
Average response time: {stats.get('avg_response_time', 0)}ms
"""
    
    def _build_compare_context(self, services: List[Dict]) -> str:
        """Build context for comparison"""
        return self._build_ranking_context(services)
    
    def _build_count_context(self, data: Dict) -> str:
        """Build context for count"""
        return f"Count: {data.get('count', 0)} services"
    
    def _generate_ai_answer(self, question: str, context: str, action: str) -> str:
        """Generate answer using AI"""
        
        system_prompt = """You are a friendly Dynatrace monitoring assistant.
Generate natural, conversational answers based on the data provided.
Be concise but informative. Use emojis sparingly for emphasis."""
        
        user_prompt = f"""Question: "{question}"

Data:
{context}

Generate a natural, helpful answer. If there are critical issues, mention them first.
If comparing services, highlight key differences.
Keep it conversational and friendly."""
        
        return self._call_ai(system_prompt, user_prompt)
    
    def _generate_template_answer(self, question: str, query: Dict, data: Any) -> str:
        """Generate template-based answer as fallback"""
        action = query.get('action')
        
        if action == 'rank' and isinstance(data, list):
            if not data:
                return "No services found matching that criteria."
            
            metric = query.get('metric', 'health_score')
            lines = [f"Here are the top {len(data)} services by {metric.replace('_', ' ')}:\n"]
            
            for i, svc in enumerate(data, 1):
                name = svc['display_name']
                status_emoji = "🟢" if svc['status'] == 'healthy' else "⚠️" if svc['status'] == 'warning' else "🔴"
                
                if metric in svc['metrics']:
                    value = svc['metrics'][metric]
                else:
                    value = svc.get(metric, 'N/A')
                
                lines.append(f"{i}. {status_emoji} **{name}** - {metric.replace('_', ' ')}: {value}")
            
            return "\n".join(lines)
        
        elif action == 'aggregate' and isinstance(data, dict):
            return f"""**Overall Service Health:**

📊 **Summary:**
• Total Services: {data.get('total_services', 0)}
• Healthy: {data.get('healthy_count', 0)} ({data.get('healthy_percentage', 0):.1f}%)
• Warning: {data.get('warning_count', 0)}
• Critical: {data.get('critical_count', 0)}

💯 **Average Health Score:** {data.get('avg_health_score', 0)}/100

🚨 **Problems:**
• Total Problems: {data.get('total_problems', 0)}
• Services Affected: {data.get('services_with_problems', 0)}

📈 **Metrics:**
• Avg Errors: {data.get('avg_error_count', 0)}
• Avg Response Time: {data.get('avg_response_time', 0)}ms"""
        
        elif action == 'filter' and isinstance(data, list):
            if not data:
                return "No services match that criteria."
            
            lines = [f"Found **{len(data)}** services:\n"]
            for svc in data[:10]:
                status_emoji = "🟢" if svc['status'] == 'healthy' else "⚠️" if svc['status'] == 'warning' else "🔴"
                lines.append(f"• {status_emoji} {svc['display_name']} ({svc['status']})")
            
            if len(data) > 10:
                lines.append(f"\n...and {len(data) - 10} more services")
            
            return "\n".join(lines)
        
        return str(data)

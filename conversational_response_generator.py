"""
Enhanced AI Response Generator with Conversational Personality
Makes responses feel natural, warm, and human-like
"""
import random
from typing import Dict, List
from config.settings import config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ConversationalResponseGenerator:
    """Generate natural, conversational responses with personality"""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.provider = ai_client.provider if ai_client else 'fallback'
    
    # Conversational openers (varied responses)
    ANALYSIS_OPENERS = [
        "Let me take a look at {service} for you...",
        "Checking {service} now...",
        "Alright, diving into {service}...",
        "On it! Looking at {service}...",
        "Sure thing! Let me check {service}...",
    ]
    
    ACKNOWLEDGMENTS = [
        "Got it!",
        "Sure thing!",
        "Absolutely!",
        "On it!",
        "You bet!",
        "No problem!",
    ]
    
    THINKING_PHRASES = [
        "Let me see...",
        "Hmm, interesting...",
        "Okay, so...",
        "Alright...",
        "Looking at this...",
    ]
    
    def generate_service_analysis(
        self,
        service_name: str,
        metrics: Dict,
        problems: List[Dict],
        insights: Dict,
        timeframe: str,
        context: Dict = None
    ) -> str:
        """
        Generate natural, conversational analysis
        
        Args:
            service_name: Service name
            metrics: Metrics data
            problems: Problems list
            insights: Analysis insights
            timeframe: Time period
            context: Conversation context (for personalization)
        """
        # Build conversational response
        response_parts = []
        
        # 1. Natural opening
        opening = self._generate_opening(service_name, context)
        if opening:
            response_parts.append(opening)
        
        # 2. Main analysis with personality
        analysis = self._generate_natural_analysis(
            service_name, metrics, problems, insights, timeframe
        )
        response_parts.append(analysis)
        
        # 3. Proactive next steps
        next_steps = self._suggest_next_steps(
            service_name, metrics, problems, insights, context
        )
        if next_steps:
            response_parts.append("\n" + next_steps)
        
        return "\n\n".join(response_parts)
    
    def _generate_opening(self, service_name: str, context: Dict = None) -> str:
        """Generate conversational opening"""
        # Check if this is a follow-up
        if context and context.get("is_followup"):
            return random.choice([
                f"Sure, looking at {service_name} again...",
                f"Okay, checking {service_name} with the new timeframe...",
                f"Got it, let me refresh the data for {service_name}...",
            ])
        
        # Check if user frequently checks this service
        if context and context.get("frequently_checked"):
            return random.choice([
                f"Checking {service_name} again - you've been keeping a close eye on this one!",
                f"Back to {service_name} - let's see how it's doing now...",
                f"{service_name} check coming up - this one's on your radar today!",
            ])
        
        # Standard opening
        return random.choice(self.ANALYSIS_OPENERS).format(service=service_name)
    
    def _generate_natural_analysis(
        self,
        service_name: str,
        metrics: Dict,
        problems: List[Dict],
        insights: Dict,
        timeframe: str
    ) -> str:
        """Generate natural language analysis"""
        status = insights.get("status", "unknown")
        concerns = insights.get("concerns", [])
        
        # Start with status-appropriate opening
        if status == "healthy" and not problems:
            return self._generate_healthy_response(service_name, metrics, timeframe)
        elif status == "warning":
            return self._generate_warning_response(service_name, metrics, problems, concerns, timeframe)
        elif status == "critical":
            return self._generate_critical_response(service_name, metrics, problems, concerns, timeframe)
        else:
            return self._generate_unknown_response(service_name, metrics, timeframe)
    
    def _generate_healthy_response(self, service_name: str, metrics: Dict, timeframe: str) -> str:
        """Generate response for healthy service"""
        openers = [
            f"Great news! {service_name} is running smoothly.",
            f"Looking good! {service_name} is healthy.",
            f"All clear with {service_name}!",
            f"{service_name} is doing well!",
        ]
        
        error_count = metrics.get("error_count", "N/A")
        response_time = metrics.get("response_time", "N/A")
        
        details = []
        if isinstance(error_count, int) and error_count < 10:
            details.append(f"minimal errors ({error_count})")
        if isinstance(response_time, (int, float)) and response_time < 500:
            details.append(f"good response times ({response_time}ms)")
        
        response = random.choice(openers)
        
        if details:
            response += f" Over the {timeframe}, I'm seeing {' and '.join(details)}."
        else:
            response += f" No issues detected over the {timeframe}."
        
        response += " Everything looks solid! 🎉"
        
        return response
    
    def _generate_warning_response(
        self, 
        service_name: str, 
        metrics: Dict, 
        problems: List[Dict],
        concerns: List[str],
        timeframe: str
    ) -> str:
        """Generate response for service with warnings"""
        openers = [
            f"I found something worth noting with {service_name}.",
            f"{service_name} has some issues that need attention.",
            f"Okay, I see a few concerns with {service_name}.",
            f"{service_name} is mostly okay, but I spotted some issues.",
        ]
        
        response = random.choice(openers)
        response += f" Over the {timeframe}:\n\n"
        
        # Add metrics with context
        error_count = metrics.get("error_count", "N/A")
        response_time = metrics.get("response_time", "N/A")
        failure_rate = metrics.get("failure_rate", "N/A")
        
        if isinstance(error_count, int):
            response += f"• **{error_count} errors** recorded"
            if error_count > 100:
                response += " (that's quite a bit)"
            response += "\n"
        
        if isinstance(response_time, (int, float)):
            response += f"• **Response time at {response_time}ms**"
            if response_time > 500:
                response += " (slower than ideal)"
            response += "\n"
        
        if isinstance(failure_rate, (int, float)):
            response += f"• **Failure rate: {failure_rate}%**"
            if failure_rate > 1:
                response += " (higher than normal)"
            response += "\n"
        
        # Add problems if any
        if problems:
            response += f"\n**{len(problems)} open problem(s):**\n"
            for i, problem in enumerate(problems[:3], 1):
                response += f"{i}. {problem.get('title', 'Unknown issue')}\n"
        
        # Add concerns
        if concerns:
            response += "\n**What caught my attention:**\n"
            for concern in concerns[:3]:
                response += f"• {concern}\n"
        
        return response.strip()
    
    def _generate_critical_response(
        self,
        service_name: str,
        metrics: Dict,
        problems: List[Dict],
        concerns: List[str],
        timeframe: str
    ) -> str:
        """Generate response for critical service issues"""
        openers = [
            f"⚠️ We have a situation with {service_name}.",
            f"🚨 {service_name} needs immediate attention.",
            f"This is concerning - {service_name} has critical issues.",
            f"Not good news on {service_name} - found some serious problems.",
        ]
        
        response = random.choice(openers)
        response += f" Here's what I'm seeing over the {timeframe}:\n\n"
        
        # Highlight critical metrics
        error_count = metrics.get("error_count", "N/A")
        response_time = metrics.get("response_time", "N/A")
        failure_rate = metrics.get("failure_rate", "N/A")
        
        if isinstance(failure_rate, (int, float)) and failure_rate > 5:
            response += f"🔴 **Failure rate is at {failure_rate}%** - that's critical!\n"
        
        if isinstance(error_count, int) and error_count > 100:
            response += f"🔴 **{error_count} errors** - significantly elevated\n"
        
        if isinstance(response_time, (int, float)) and response_time > 1000:
            response += f"🔴 **Response time spiked to {response_time}ms** - extremely slow\n"
        
        # Critical problems
        if problems:
            response += f"\n**🚨 {len(problems)} Critical Problem(s):**\n"
            for i, problem in enumerate(problems[:3], 1):
                relevance = problem.get("relevance", "")
                icon = "🔴" if relevance == "root_cause" else "⚠️"
                response += f"{icon} {problem.get('title', 'Unknown')}\n"
        
        # What to do
        response += "\n**This needs urgent attention.** "
        
        return response
    
    def _generate_unknown_response(self, service_name: str, metrics: Dict, timeframe: str) -> str:
        """Generate response when status is unclear"""
        response = f"I checked {service_name} over the {timeframe}. Here's what I found:\n\n"
        
        for key, value in metrics.items():
            formatted_key = key.replace("_", " ").title()
            response += f"• {formatted_key}: {value}\n"
        
        response += "\nThe metrics are a bit mixed - not clearly healthy or problematic."
        
        return response
    
    def _suggest_next_steps(
        self,
        service_name: str,
        metrics: Dict,
        problems: List[Dict],
        insights: Dict,
        context: Dict = None
    ) -> str:
        """Suggest proactive next steps"""
        status = insights.get("status", "unknown")
        suggestions = []
        
        if status == "critical" or status == "warning":
            # Suggest investigation steps
            if problems:
                suggestions.append("• Look into when these problems started?")
                suggestions.append("• Check if other services are affected?")
            
            failure_rate = metrics.get("failure_rate", 0)
            if isinstance(failure_rate, (int, float)) and failure_rate > 2:
                suggestions.append("• Review error logs for patterns?")
            
            response_time = metrics.get("response_time", 0)
            if isinstance(response_time, (int, float)) and response_time > 800:
                suggestions.append("• Check database or downstream services?")
            
            suggestions.append("• See metrics over a longer timeframe?")
        
        elif status == "healthy":
            # Suggest monitoring or comparison
            suggestions.append("• Compare with yesterday's performance?")
            suggestions.append("• Check other services?")
            suggestions.append("• Set up monitoring for changes?")
        
        if suggestions:
            intro = random.choice([
                "**Want me to:**",
                "**What would you like to do next?**",
                "**I can help with:**",
                "**Next steps:**",
            ])
            return intro + "\n" + "\n".join(suggestions)
        
        return ""
    
    def generate_service_list_response(
        self, 
        services: List[Dict],
        context: Dict = None
    ) -> str:
        """Generate natural service list response"""
        if not services:
            return "Hmm, I couldn't find any services. That's odd - want me to try again?"
        
        # Group by type
        services_by_type = {}
        for service in services:
            service_type = service.get("properties", {}).get("serviceType", "Unknown")
            if service_type not in services_by_type:
                services_by_type[service_type] = []
            services_by_type[service_type].append(
                service.get("displayName", service.get("entityId", "Unknown"))
            )
        
        # Natural opening
        opener = random.choice([
            f"I found **{len(services)} services** in your environment:",
            f"You've got **{len(services)} services** here:",
            f"Here's what I found - **{len(services)} services** total:",
            f"Okay! I see **{len(services)} services**:",
        ])
        
        response = opener + "\n\n"
        
        # List by type
        for service_type, names in sorted(services_by_type.items()):
            response += f"**{service_type}** ({len(names)}):\n"
            for name in sorted(names[:10]):
                response += f"• {name}\n"
            if len(names) > 10:
                response += f"  _...and {len(names) - 10} more_\n"
            response += "\n"
        
        # Friendly closing
        closing = random.choice([
            "Which one would you like me to check?",
            "Want me to analyze any of these?",
            "I can check any of these for you - just say the word!",
            "Need details on any particular service?",
        ])
        
        response += f"💡 {closing}"
        
        return response
    
    def generate_clarification_request(
        self,
        issue: str,
        suggestions: List[str] = None,
        context: Dict = None
    ) -> str:
        """Generate natural clarification question"""
        
        if issue == "no_service_name":
            openers = [
                "Which service would you like me to check?",
                "I'd be happy to help! Which service should I look at?",
                "Sure thing! Which service are you interested in?",
                "Got it! What service should I analyze?",
            ]
            
            response = random.choice(openers)
            
            if suggestions:
                response += f"\n\nRecently mentioned:\n"
                for svc in suggestions:
                    response += f"• {svc}\n"
                response += "\nOr type 'show all' to see everything!"
            
            return response
        
        elif issue == "service_not_found":
            return "I couldn't find that service. Could you double-check the name, or type 'show all' to see what's available?"
        
        elif issue == "ambiguous_query":
            return "I'm not quite sure what you're asking. Could you be a bit more specific? Or type 'help' to see what I can do!"
        
        return "I'm not sure I understood that. Could you rephrase?"
    
    def generate_error_response(self, error_type: str, details: str = "") -> str:
        """Generate friendly error messages"""
        
        if error_type == "api_error":
            return random.choice([
                "Oops! I'm having trouble connecting to Dynatrace. Can you try again in a moment?",
                "Hmm, Dynatrace isn't responding. Mind trying that again?",
                "Something went wrong on my end. Want to give it another shot?",
            ])
        
        elif error_type == "no_data":
            return "I couldn't find any data for that timeframe. Try a different time period?"
        
        elif error_type == "general":
            return f"Something unexpected happened. {details if details else 'Please try again!'}"
        
        return "Oops! Something went wrong. Mind trying again?"
    
    def generate_help_response(self, context: Dict = None) -> str:
        """Generate contextual help message"""
        
        intro = random.choice([
            "I'm here to help! Here's what I can do:",
            "Happy to help! I can assist with:",
            "Sure thing! Here are my capabilities:",
            "No problem! I can help you with:",
        ])
        
        help_text = f"""{intro}

**🔍 Check Service Health**
• "How is ordercontroller doing?"
• "Check payment-api"
• "Any issues with checkout-service?"

**📋 List Services**
• "Show me all services"
• "What services do I have?"

**📊 Analyze Metrics**
• "What's the performance of auth-service?"
• "Show me metrics for the last 4 hours"

**🔧 Troubleshoot**
• "Why is inventory-api slow?"
• "What's wrong with my services?"

**💡 Tip:** Just talk naturally - I understand conversational queries!

What would you like to know?"""
        
        return help_text

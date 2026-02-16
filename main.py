"""
Dynatrace AI Assistant - Universal Query System
Now answers ANY analytical question about services!
"""
import streamlit as st
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from config.settings import config
from utils.logger import setup_logger
from utils.timeframe import human_readable_timeframe
from prompt_handler.intent_parser import AIIntentParser
from dynatrace_api.services import DynatraceServicesAPI
from dynatrace_api.metrics import DynatraceMetricsAPI
from dynatrace_api.problems import DynatraceProblemsAPI
from llm.response_generator import AIResponseGenerator

# Import new components
from service_knowledge_base import ServiceKnowledgeBase
from ai_query_engine import AIQueryEngine

logger = setup_logger(__name__)

# Initialize standard components
services_api = DynatraceServicesAPI()
metrics_api = DynatraceMetricsAPI()
problems_api = DynatraceProblemsAPI()
ai_generator = AIResponseGenerator()
intent_parser = AIIntentParser(ai_client=ai_generator)

# Import conversational generator
try:
    from conversational_response_generator import ConversationalResponseGenerator
    conversational_gen = ConversationalResponseGenerator(ai_generator)
    USE_CONVERSATIONAL = True
except:
    USE_CONVERSATIONAL = False
    conversational_gen = None

# Initialize knowledge base and query engine (singleton per session)
@st.cache_resource
def get_knowledge_base():
    """Initialize and cache knowledge base"""
    kb = ServiceKnowledgeBase()
    return kb

@st.cache_resource
def get_query_engine():
    """Initialize and cache query engine"""
    kb = get_knowledge_base()
    query_engine = AIQueryEngine(kb, ai_generator)
    return query_engine

def initialize_session_state():
    """Initialize session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
        welcome_msg = """👋 Hey! I'm your Dynatrace AI Assistant with **superpowers**!

I can now answer **any question** about your services:

**New Capabilities:**
• "Which service has the highest failure rate?"
• "Show me all services with problems"
• "What's today's overall health?"
• "Which are my worst 5 services?"
• "How many services have errors?"

**Plus all the usual:**
• "Check ordercontroller"
• "Show all services"
• "Any issues?"

Just ask me anything! 😊"""
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": welcome_msg,
            "timestamp": datetime.now()
        })
    
    if "conversation_context" not in st.session_state:
        st.session_state.conversation_context = {
            "last_service": None,
            "last_intent": None,
            "last_timeframe": "2h",
            "service_check_count": {},
            "last_analysis_time": None,
            "user_preferences": {
                "prefers_detailed": False,
                "frequently_checked_services": []
            }
        }
    
    if "kb_initialized" not in st.session_state:
        st.session_state.kb_initialized = False

def add_message(role: str, content: str):
    """Add message to chat"""
    st.session_state.messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now()
    })
    
    if len(st.session_state.messages) > config.MAX_CHAT_HISTORY:
        welcome = st.session_state.messages[0]
        recent = st.session_state.messages[-(config.MAX_CHAT_HISTORY-1):]
        st.session_state.messages = [welcome] + recent

def is_analytical_query(user_input: str) -> bool:
    """Detect if query is analytical (needs knowledge base)"""
    analytical_keywords = [
        'which', 'what', 'show me all', 'list all', 'compare',
        'highest', 'lowest', 'worst', 'best', 'most',
        'today', 'overview', 'summary', 'health', 'status',
        'how many', 'count', 'all services', 'everything',
        'with problems', 'with errors', 'critical', 'warning'
    ]
    
    q_lower = user_input.lower()
    return any(keyword in q_lower for keyword in analytical_keywords)

def handle_analytical_query(user_input: str, query_engine) -> str:
    """Handle analytical queries using query engine"""
    kb = get_knowledge_base()
    
    # Check KB status
    if not kb.is_ready():
        if kb.is_building:
            return "🔄 I'm still gathering data from all your services (this takes 30-60 seconds on first run). Please wait a moment..."
        else:
            return "⏳ Let me gather data from all your services first. This will take about 30-60 seconds..."
    
    # Use query engine
    with st.spinner("🔍 Analyzing all services..."):
        result = query_engine.answer_question(user_input)
        return result.get('answer', 'Sorry, I had trouble with that query.')

def handle_single_service_query(intent: dict) -> str:
    """Handle single service queries (existing logic)"""
    service_name = intent.get("service_name")
    timeframe = intent.get("timeframe", "2h")
    
    if not service_name:
        recent = get_recent_services_from_history()
        if USE_CONVERSATIONAL and conversational_gen:
            return conversational_gen.generate_clarification_request(
                "no_service_name",
                suggestions=recent
            )
        return "Which service would you like me to check?"
    
    entity_id = services_api.get_service_entity_id(service_name)
    
    if not entity_id:
        similar = find_similar_services(service_name)
        if similar:
            return (
                f"Hmm, I couldn't find '{service_name}' exactly.\n\n"
                f"**Did you mean one of these?**\n" + 
                "\n".join([f"• {s}" for s in similar[:3]])
            )
        return f"I couldn't find '{service_name}'. Try 'show all services' to see what's available."
    
    with st.spinner(f"🔍 Analyzing {service_name}..."):
        problems = problems_api.get_problems_for_service(service_name, entity_id, timeframe)
        metrics = metrics_api.get_service_metrics(entity_id, timeframe)
        insights = metrics_api.analyze_metrics(metrics)
        
        update_context(intent, service_name)
        display_metrics_ui(service_name, metrics, problems, insights)
        
        if USE_CONVERSATIONAL and conversational_gen:
            conv_context = get_conversational_context()
            response = conversational_gen.generate_service_analysis(
                service_name=service_name,
                metrics=metrics,
                problems=problems,
                insights=insights,
                timeframe=human_readable_timeframe(timeframe),
                context=conv_context
            )
        else:
            response = ai_generator.generate_service_analysis(
                service_name=service_name,
                metrics=metrics,
                problems=problems,
                insights=insights,
                timeframe=human_readable_timeframe(timeframe)
            )
        
        return response

def update_context(intent: dict, service_name: str = None):
    """Update conversation context"""
    context = st.session_state.conversation_context
    
    if service_name:
        context["last_service"] = service_name
        if service_name not in context["service_check_count"]:
            context["service_check_count"][service_name] = 0
        context["service_check_count"][service_name] += 1
    
    if intent.get("type"):
        context["last_intent"] = intent["type"]
    if intent.get("timeframe"):
        context["last_timeframe"] = intent["timeframe"]
    
    context["last_analysis_time"] = datetime.now()

def get_conversational_context() -> dict:
    """Get context for conversational responses"""
    context = st.session_state.conversation_context
    last_service = context.get("last_service")
    
    return {
        "is_followup": False,
        "frequently_checked": context["service_check_count"].get(last_service, 0) >= 3 if last_service else False,
        "recent_services": list(context["service_check_count"].keys())[-3:]
    }

def get_recent_services_from_history() -> list:
    """Get recently mentioned services"""
    context = st.session_state.conversation_context
    return [svc for svc, count in sorted(
        context["service_check_count"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]]

def find_similar_services(service_name: str) -> list:
    """Find similar service names"""
    try:
        all_services = services_api.list_services(limit=100)
        similar = []
        service_lower = service_name.lower()
        
        for service in all_services:
            name = service.get("displayName", "").lower()
            if service_lower in name or name in service_lower:
                similar.append(service.get("displayName"))
        
        return similar[:5]
    except:
        return []

def display_metrics_ui(service_name: str, metrics: dict, problems: list, insights: dict):
    """Display metrics visually"""
    st.markdown(f"### 📊 {service_name}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Errors", metrics.get("error_count", "N/A"))
    with col2:
        rt = metrics.get("response_time", "N/A")
        st.metric("Response Time", f"{rt}ms" if isinstance(rt, (int, float)) else rt)
    with col3:
        st.metric("Requests", metrics.get("request_count", "N/A"))
    with col4:
        fr = metrics.get("failure_rate", "N/A")
        st.metric("Failure Rate", f"{fr}%" if isinstance(fr, (int, float)) else fr)
    
    if problems:
        with st.expander(f"🚨 {len(problems)} Problem(s)", expanded=len(problems) <= 3):
            for problem in problems[:5]:
                relevance = problem.get("relevance", "")
                icon = "🔴" if relevance == "root_cause" else "⚠️"
                st.markdown(f"{icon} **{problem.get('title', 'Unknown')}**")
    
    status = insights.get("status", "unknown")
    if status == "healthy":
        st.success("✅ Healthy")
    elif status == "warning":
        st.warning("⚠️ Warning")
    elif status == "critical":
        st.error("🔴 Critical")

def process_user_input(user_input: str) -> str:
    """Process user input - route to appropriate handler"""
    try:
        query_engine = get_query_engine()
        
        # Check if analytical query
        if is_analytical_query(user_input):
            return handle_analytical_query(user_input, query_engine)
        
        # Parse intent for single service queries
        intent = intent_parser.parse(user_input)
        
        if not intent:
            return "I'm not sure what you're asking. Try 'help' or ask about a specific service!"
        
        intent_type = intent.get("type")
        
        # Handle different intent types
        if intent_type in ["check_abnormality", "service_details", "metrics_analysis"]:
            return handle_single_service_query(intent)
        elif intent_type == "list_services":
            return handle_analytical_query("show me all services", query_engine)
        elif intent_type == "general_question":
            q_lower = user_input.lower()
            if any(w in q_lower for w in ['help', 'what can you do']):
                return get_help_text()
            return "Try asking about a specific service or 'what's today's health?'"
        else:
            return "That feature is coming soon! For now, try checking a service or asking analytical questions."
    
    except Exception as e:
        logger.error(f"Error processing input: {e}", exc_info=True)
        return "Oops! Something went wrong. Mind trying again?"

def get_help_text() -> str:
    """Help text"""
    return """**What I can do:**

🔍 **Analytical Queries** (NEW!)
• "Which service has the highest failure rate?"
• "Show me all services with problems"
• "What's today's overall health?"
• "How many services have errors?"

📊 **Single Service Checks**
• "Check ordercontroller"
• "Any issues with payment-api?"
• "How's checkout doing?"

Just ask naturally - I'll understand! 😊"""

def main():
    """Main application"""
    st.set_page_config(
        page_title="Dynatrace AI Assistant",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Dynatrace AI Assistant")
    st.markdown("**Universal Query System** - Ask me anything about your services! 💬")
    
    initialize_session_state()
    
    # Initialize knowledge base in background
    kb = get_knowledge_base()
    query_engine = get_query_engine()
    
    if not st.session_state.kb_initialized and not kb.is_ready():
        with st.spinner("🔄 Initializing knowledge base (gathering data from all services)... This takes 30-60 seconds on first run."):
            kb.build()
            st.session_state.kb_initialized = True
            st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 💡 New Capabilities!")
        st.markdown("""
        **Ask comparative questions:**
        - "Which has highest failure?"
        - "Show critical services"
        - "What's today's health?"
        - "How many have problems?"
        
        **Or check individual services:**
        - "Check ordercontroller"
        - "Any issues?"
        """)
        
        # KB Status
        kb_status = kb.get_status()
        if kb_status['is_ready']:
            st.success(f"✅ KB Ready ({kb_status['service_count']} services)")
            if st.button("🔄 Refresh Data"):
                with st.spinner("Refreshing..."):
                    kb.build()
                st.success("Data refreshed!")
                st.rerun()
        elif kb_status['is_building']:
            st.warning("⏳ Building knowledge base...")
        else:
            st.error("❌ KB not ready")
        
        st.markdown("### 🤖 AI Provider")
        provider = ai_generator.provider.title()
        if provider == "Fallback":
            st.warning("⚠️ No AI (templates)")
        else:
            st.success(f"✅ {provider}")
        
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.session_state.conversation_context = {
                "last_service": None,
                "last_intent": None,
                "last_timeframe": "2h",
                "service_check_count": {},
                "last_analysis_time": None,
                "user_preferences": {}
            }
            st.rerun()
    
    # Display chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask anything... (e.g., 'Which service has most errors?')"):
        add_message("user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                response = process_user_input(prompt)
                st.markdown(response)
                add_message("assistant", response)
            except Exception as e:
                error_msg = "I ran into an issue. Could you try rephrasing?"
                logger.error(f"Error: {e}", exc_info=True)
                st.error(error_msg)
                add_message("assistant", error_msg)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"App error: {e}", exc_info=True)
        st.error("Something went wrong. Please refresh!")

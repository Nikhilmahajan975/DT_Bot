"""
Configuration Management Module - Multi-Provider AI Support
Supports: OpenAI, Anthropic Claude, Google Gemini, Ollama (Free/Local)
"""
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

class Config:
    """Application configuration with validation and multi-AI provider support"""
    
    def __init__(self):
        # Dynatrace Configuration
        self.DT_API_TOKEN = os.getenv("DT_API_TOKEN")
        self.DT_BASE_URL = os.getenv("DT_BASE_URL", "").rstrip('/')
        
        # AI Provider Configuration
        self._setup_ai_providers()
        
        # Application Configuration
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.MAX_CHAT_HISTORY = int(os.getenv("MAX_CHAT_HISTORY", "50"))
        self.DEFAULT_TIMEFRAME = os.getenv("DEFAULT_TIMEFRAME", "2h")
        
        # Validate required configs
        self._validate_dynatrace_config()
        self._validate_ai_config()
    
    def _setup_ai_providers(self):
        """Setup all AI provider configurations"""
        
        # OpenAI (GPT-3.5, GPT-4)
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # Cheaper than GPT-4
        
        # Anthropic Claude
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
        self.ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")  # Cheapest
        
        # Google Gemini (FREE tier available!)
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")  # Free model
        
        # Ollama (100% FREE, runs locally)
        self.OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "false").lower() == "true"
        self.OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
        
        # AI Provider Selection (auto-detect if not specified)
        self.AI_PROVIDER = os.getenv("AI_PROVIDER", "auto")  # auto, openai, anthropic, gemini, ollama, fallback
    
    def _validate_dynatrace_config(self):
        """Validate Dynatrace configuration"""
        required_vars = ["DT_API_TOKEN", "DT_BASE_URL"]
        missing_vars = [var for var in required_vars if not getattr(self, var)]
        
        if missing_vars:
            raise ValueError(
                f"Missing required Dynatrace environment variables: {', '.join(missing_vars)}\n"
                "Please set them in your .env file"
            )
    
    def _validate_ai_config(self):
        """Validate AI configuration - at least one provider should be available"""
        has_openai = bool(self.OPENAI_API_KEY)
        has_anthropic = bool(self.ANTHROPIC_API_KEY)
        has_gemini = bool(self.GEMINI_API_KEY)
        has_ollama = self.OLLAMA_ENABLED
        
        if not any([has_openai, has_anthropic, has_gemini, has_ollama]):
            print("⚠️  WARNING: No AI provider configured!")
            print("The chatbot will use template-based responses (less intelligent).")
            print("")
            print("To enable AI responses, set one of these in your .env file:")
            print("  • GEMINI_API_KEY=your_key (FREE - Get from https://makersuite.google.com/app/apikey)")
            print("  • OLLAMA_ENABLED=true (FREE - Install from https://ollama.ai)")
            print("  • ANTHROPIC_API_KEY=your_key (Paid)")
            print("  • OPENAI_API_KEY=your_key (Paid)")
            print("")
    
    def get_auth_headers(self):
        """Get Dynatrace authentication headers"""
        return {
            "Authorization": f"Api-Token {self.DT_API_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def get_active_ai_provider(self) -> str:
        """Get the active AI provider name"""
        if self.AI_PROVIDER != "auto":
            return self.AI_PROVIDER
        
        # Auto-detect in order of preference (free first!)
        if self.GEMINI_API_KEY:
            return "gemini"
        elif self.OLLAMA_ENABLED:
            return "ollama"
        elif self.ANTHROPIC_API_KEY:
            return "anthropic"
        elif self.OPENAI_API_KEY:
            return "openai"
        else:
            return "fallback"

# Singleton instance
config = Config()

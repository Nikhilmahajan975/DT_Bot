# 🆓 FREE AI Alternatives Guide for Dynatrace AI Assistant

## Overview

Your Dynatrace AI Assistant now supports **4 AI providers**, including **2 completely FREE options**!

---

## 🎯 Quick Comparison

| Provider | Cost | Setup Difficulty | Quality | Speed | Best For |
|----------|------|------------------|---------|-------|----------|
| **Google Gemini** | 🟢 FREE | ⭐ Easy | ⭐⭐⭐⭐ | ⚡⚡⚡ | **RECOMMENDED** |
| **Ollama** | 🟢 FREE | ⭐⭐ Medium | ⭐⭐⭐⭐ | ⚡⚡ | Privacy-focused |
| Anthropic Claude | 💰 Paid | ⭐ Easy | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ | Best quality |
| OpenAI GPT | 💰 Paid | ⭐ Easy | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ | Most popular |

---

## 🟢 OPTION 1: Google Gemini (RECOMMENDED - FREE!) ⭐

### ✅ Why Choose Gemini?
- **100% FREE** with generous limits (60 requests/minute)
- **No credit card required**
- **Easy setup** (5 minutes)
- **Great quality** responses
- **Fast** API responses

### 📋 Setup Instructions

#### Step 1: Get Your FREE API Key
1. Go to: https://makersuite.google.com/app/apikey
2. Click "Get API Key"
3. Click "Create API key in new project"
4. Copy your API key

#### Step 2: Configure Your .env File
```bash
# Add to your .env file
GEMINI_API_KEY=your_actual_api_key_here
GEMINI_MODEL=gemini-pro
AI_PROVIDER=auto
```

#### Step 3: Install Required Package
```bash
pip install google-generativeai --break-system-packages
```

#### Step 4: Run the App
```bash
streamlit run main.py
```

### 📊 Free Tier Limits
- **60 requests per minute**
- **1,500 requests per day**
- **1 million requests per month**

Perfect for development and small-to-medium usage!

### 🎓 Example Response Quality
**User:** "Check issues for ordercontroller"

**Gemini Response:**
"I've analyzed the ordercontroller service over the past 2 hours. The service is experiencing some concerning issues:

The error count stands at 150 errors, with a failure rate of 5.2%. Response times have climbed to 1200ms, which is significantly above optimal levels. I've identified 2 open problems that require attention.

Recommendations:
1. Investigate recent deployments or code changes
2. Review application logs for error patterns
3. Check database query performance and connection pools
4. Monitor resource utilization (CPU, memory)

Would you like me to analyze any specific metrics in more detail?"

---

## 🟢 OPTION 2: Ollama (100% FREE - Runs Locally) 🏠

### ✅ Why Choose Ollama?
- **100% FREE** forever
- **No API limits** - runs on your machine
- **Complete privacy** - data never leaves your computer
- **No internet required** after initial setup
- **Multiple models** available (Llama 2, Mistral, etc.)

### ⚠️ Requirements
- **RAM:** Minimum 8GB (16GB recommended)
- **Disk Space:** 4-10GB per model
- **OS:** Windows, macOS, or Linux

### 📋 Setup Instructions

#### Step 1: Install Ollama
**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from: https://ollama.ai/download

#### Step 2: Download a Model
```bash
# Llama 2 (7B parameters - recommended for starting)
ollama pull llama2

# OR Mistral (7B parameters - faster)
ollama pull mistral

# OR Llama 2 13B (better quality, needs 16GB RAM)
ollama pull llama2:13b
```

#### Step 3: Start Ollama Server
```bash
ollama serve
```

#### Step 4: Configure Your .env File
```bash
# Add to your .env file
OLLAMA_ENABLED=true
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2
AI_PROVIDER=auto
```

#### Step 5: Run the App
```bash
streamlit run main.py
```

### 🎓 Example Response Quality
**User:** "Check issues for ordercontroller"

**Ollama (Llama2) Response:**
"Based on my analysis of the ordercontroller service over the last 2 hours, I've identified several concerns:

The service has recorded 150 errors with a failure rate of 5.2%, which is elevated. Response times have increased to 1200ms, indicating potential performance issues. There are currently 2 open problems requiring attention.

I recommend:
- Reviewing recent deployments for potential bugs
- Examining error logs to identify common patterns
- Checking database performance and query optimization
- Monitoring server resources for bottlenecks"

### 🎯 Available Models

| Model | Size | RAM Required | Quality | Speed |
|-------|------|--------------|---------|-------|
| llama2:7b | 3.8GB | 8GB | ⭐⭐⭐ | ⚡⚡⚡ |
| mistral:7b | 4.1GB | 8GB | ⭐⭐⭐⭐ | ⚡⚡⚡ |
| llama2:13b | 7.3GB | 16GB | ⭐⭐⭐⭐ | ⚡⚡ |
| codellama:7b | 3.8GB | 8GB | ⭐⭐⭐⭐ | ⚡⚡⚡ |

### 💡 Switching Models
```bash
# Download new model
ollama pull mistral

# Update .env
OLLAMA_MODEL=mistral

# Restart app
```

---

## 💰 OPTION 3: Anthropic Claude (Paid)

### ✅ Why Choose Claude?
- **High quality** responses
- **Long context window**
- **Great at analysis**
- **Reliable API**

### 💵 Pricing
- Claude 3 Haiku: $0.25 / 1M input tokens (cheapest)
- Claude 3 Sonnet: $3.00 / 1M input tokens
- Claude 3 Opus: $15.00 / 1M input tokens

### 📋 Setup
1. Get API key: https://console.anthropic.com/
2. Add to .env:
   ```bash
   ANTHROPIC_API_KEY=your_key_here
   ANTHROPIC_MODEL=claude-3-haiku-20240307
   ```
3. Install: `pip install anthropic --break-system-packages`

---

## 💰 OPTION 4: OpenAI (Paid)

### ✅ Why Choose OpenAI?
- **Most popular**
- **Well-documented**
- **Consistent quality**

### 💵 Pricing
- GPT-3.5 Turbo: $0.50 / 1M input tokens (cheaper)
- GPT-4 Turbo: $10.00 / 1M input tokens
- GPT-4: $30.00 / 1M input tokens

### 📋 Setup
1. Get API key: https://platform.openai.com/api-keys
2. Add to .env:
   ```bash
   OPENAI_API_KEY=your_key_here
   OPENAI_MODEL=gpt-3.5-turbo
   ```

---

## 🔄 Switching Between Providers

### Method 1: Auto-Detection (Recommended)
```bash
# In .env
AI_PROVIDER=auto
```
The system will automatically use the first available provider in this order:
1. Gemini (if API key present)
2. Ollama (if enabled)
3. Anthropic (if API key present)
4. OpenAI (if API key present)
5. Fallback (template responses)

### Method 2: Manual Selection
```bash
# In .env
AI_PROVIDER=gemini    # Force use Gemini
AI_PROVIDER=ollama    # Force use Ollama
AI_PROVIDER=anthropic # Force use Claude
AI_PROVIDER=openai    # Force use OpenAI
AI_PROVIDER=fallback  # Force use templates (no AI)
```

---

## 🎯 Which Should You Choose?

### 🏆 For Most People: **Google Gemini**
- Free, easy setup, good quality
- Perfect balance of cost and performance
- No installation, works immediately

### 🔒 For Privacy Concerns: **Ollama**
- Data stays on your machine
- No internet required
- 100% free forever

### 💼 For Production/Enterprise: **Claude or GPT-4**
- Highest quality responses
- Better reliability
- Professional support

### 💸 For Testing/Development: **Gemini or Ollama**
- Both completely free
- Perfect for learning and prototyping

---

## 🚫 No AI Provider? No Problem!

If you don't configure any AI provider, the chatbot will still work using **template-based responses**:

```
Service Analysis: ordercontroller

Status: WARNING

Metrics:
- Error Count: 150
- Response Time: 1200 ms
- Request Count: 1500
- Failure Rate: 5.2%

Problems Found: 2
- High error rate (OPEN)
- Slow response (OPEN)

Recommendations:
- Investigate recent deployments
- Review error logs for common patterns
- Check database query performance
```

Still useful, just less conversational!

---

## 📊 Installation Summary

### For Gemini (Easiest):
```bash
pip install google-generativeai --break-system-packages
# Add GEMINI_API_KEY to .env
# Done!
```

### For Ollama (Free, Local):
```bash
# Install Ollama from https://ollama.ai
ollama pull llama2
ollama serve
# Add OLLAMA_ENABLED=true to .env
```

### For Claude:
```bash
pip install anthropic --break-system-packages
# Add ANTHROPIC_API_KEY to .env
```

### For OpenAI:
```bash
pip install openai --break-system-packages
# Add OPENAI_API_KEY to .env
```

---

## 🆘 Troubleshooting

### Gemini Issues
**Error: "API key not valid"**
- Get a new key from https://makersuite.google.com/app/apikey
- Make sure no extra spaces in .env file

**Error: "Resource exhausted"**
- You hit the rate limit (60/min)
- Wait a minute or upgrade to paid tier

### Ollama Issues
**Error: "Connection refused"**
- Make sure Ollama is running: `ollama serve`
- Check URL is correct: `http://localhost:11434`

**Error: "Model not found"**
- Pull the model first: `ollama pull llama2`
- Check model name matches in .env

**Slow responses:**
- Use smaller model (llama2:7b instead of 13b)
- Check RAM usage
- Close other applications

---

## 📈 Cost Comparison (1000 requests/month)

| Provider | Monthly Cost | Notes |
|----------|--------------|-------|
| **Gemini** | **$0** | FREE (within limits) |
| **Ollama** | **$0** | FREE (uses your hardware) |
| Claude Haiku | ~$5 | Cheapest Claude |
| GPT-3.5 | ~$10 | Cheapest OpenAI |
| GPT-4 | ~$50 | Most expensive |

---

## 🎓 Recommendation

**Start with Gemini** - It's free, easy, and good quality!

If you need more control or privacy → Switch to Ollama

If you go to production → Consider Claude or GPT-4

---

## 🔗 Useful Links

- **Gemini API:** https://makersuite.google.com/app/apikey
- **Ollama:** https://ollama.ai
- **Anthropic:** https://console.anthropic.com/
- **OpenAI:** https://platform.openai.com/

---

**Questions? The chatbot will tell you which provider it's using when it starts!**

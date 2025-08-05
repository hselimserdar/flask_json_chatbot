# 🧰 Chatbot Tool Calling Features

Your Flask chatbot now has **web search** and **mathematical calculation** capabilities powered by Gemini 2.0 Flash with tool calling!

## ✨ New Features

### 🔍 Web Search
- **What it does**: Searches the web for current information using DuckDuckGo API
- **When to use**: Ask questions about current events, recent information, facts, or anything that requires up-to-date knowledge
- **Examples**:
  - "What's the latest news about AI?"
  - "Search for Python Flask tutorials"
  - "Find information about the weather in New York"

### 🧮 Math Calculations
- **What it does**: Performs mathematical calculations and evaluations
- **When to use**: Ask for calculations, math problems, or mathematical expressions
- **Supported functions**: Basic arithmetic, trigonometry, logarithms, square roots, and more
- **Examples**:
  - "Calculate 15 * 8 + 32"
  - "What is the square root of 144?"
  - "Calculate sin(π/4)"

## 🛠️ Technical Implementation

### Files Modified
- `tools.py` - Contains the tool implementations
- `gemini_api.py` - Updated to support tool calling with Gemini 2.0 Flash
- `chatbot_manage.py` - Modified to enable tools for main conversations

### How It Works
1. **User sends a message** that might benefit from tools
2. **Gemini AI analyzes** the message and determines if tools are needed
3. **Tools are automatically called** (web search or math calculation)
4. **Results are integrated** into the AI's response seamlessly
5. **User receives** a comprehensive answer with real-time data or calculations

### Security Features
- **Math calculations**: Uses safe evaluation with restricted functions
- **Web search**: Rate-limited and uses trusted DuckDuckGo API
- **Error handling**: Graceful fallbacks if tools fail

## 🚀 Usage Examples

### Web Search Examples
**User**: "What are the latest developments in artificial intelligence?"  
**Bot**: *[Searches web and provides current AI news and developments]*

**User**: "Find me information about Flask web framework"  
**Bot**: *[Searches and provides comprehensive Flask information]*

### Math Calculation Examples
**User**: "I need to calculate 25% of 840"  
**Bot**: *[Calculates: 0.25 * 840 = 210]*

**User**: "What's the area of a circle with radius 7?"  
**Bot**: *[Calculates: π * 7² ≈ 153.94]*

## 📝 Notes
- Tools work for both **authenticated users** and **guest users**
- **Automatic detection**: The AI decides when to use tools based on context
- **Seamless integration**: Tool results are naturally incorporated into responses
- **Fallback handling**: If tools fail, the chatbot continues with its base knowledge

Enjoy your enhanced chatbot with real-time search and calculation capabilities! 🎉

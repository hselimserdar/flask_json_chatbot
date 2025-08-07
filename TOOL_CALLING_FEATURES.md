# Chatbot Tool Calling Features

The Flask chatbot includes web search and mathematical calculation capabilities powered by Gemini 2.0 Flash with tool calling functionality.

## Features Overview

### Web Search
- **Functionality**: Searches the web for current information using DuckDuckGo API
- **Use Cases**: Current events, recent information, facts, or any queries requiring up-to-date knowledge
- **Examples**:
  - "What's the latest news about AI?"
  - "Search for Python Flask tutorials"
  - "Find information about the weather in New York"

### Mathematical Calculations
- **Functionality**: Performs mathematical calculations and evaluations
- **Use Cases**: Calculations, math problems, or mathematical expressions
- **Supported Operations**: Basic arithmetic, trigonometry, logarithms, square roots, and advanced mathematical functions
- **Examples**:
  - "Calculate 15 * 8 + 32"
  - "What is the square root of 144?"
  - "Calculate sin(π/4)"

## Technical Implementation

### Modified Files
- `tools.py` - Contains the tool implementations
- `gemini_api.py` - Updated to support tool calling with Gemini 2.0 Flash
- `chatbot_manage.py` - Modified to enable tools for main conversations

### Process Flow
1. **Message Analysis**: User sends a message that may benefit from tool usage
2. **Tool Detection**: Gemini AI analyzes the message and determines if tools are required
3. **Tool Execution**: Appropriate tools are automatically invoked (web search or mathematical calculation)
4. **Result Integration**: Tool results are seamlessly incorporated into the AI's response
5. **Response Delivery**: User receives a comprehensive answer with real-time data or calculations

### Security Implementation
- **Mathematical Calculations**: Uses safe evaluation with restricted function access
- **Web Search**: Rate-limited requests using trusted DuckDuckGo API
- **Error Handling**: Graceful fallback mechanisms when tools are unavailable

## Usage Examples

### Web Search Examples
**User Query**: "What are the latest developments in artificial intelligence?"  
**System Response**: Searches web and provides current AI news and developments

**User Query**: "Find me information about Flask web framework"  
**System Response**: Searches and provides comprehensive Flask information

### Mathematical Calculation Examples
**User Query**: "I need to calculate 25% of 840"  
**System Response**: Calculates: 0.25 * 840 = 210

**User Query**: "What's the area of a circle with radius 7?"  
**System Response**: Calculates: π * 7² ≈ 153.94

## System Notes
- Tools are available for both authenticated users and guest users
- **Automatic Detection**: The AI determines when to use tools based on message context
- **Seamless Integration**: Tool results are naturally incorporated into responses
- **Fallback Handling**: If tools are unavailable, the chatbot continues with its base knowledge

The enhanced chatbot provides real-time search and calculation capabilities to improve user experience and information accuracy.

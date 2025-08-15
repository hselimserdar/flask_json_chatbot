# Tool Calling Features

AI-powered tool calling capabilities using Gemini 2.0 Flash/Deepseek V3 for web search and mathematical calculations.

## Available Tools

### Web Search Tool
Real-time web search using DuckDuckGo API for current information and facts.

**Detailed Use Cases:**
- **Current Events**: "What happened in the latest SpaceX launch?"
- **Weather Information**: "What's the current weather in Tokyo?"
- **Stock Prices**: "What is Tesla's current stock price?"
- **News Updates**: "Latest developments in renewable energy"
- **Product Information**: "Reviews of iPhone 15 Pro"
- **Technical Documentation**: "Python Flask best practices 2024"
- **Travel Information**: "Flight delays at JFK airport today"
- **Sports Results**: "Latest Premier League match results"
- **Technology News**: "Recent AI breakthroughs this week"
- **Academic Research**: "Latest studies on climate change"
- **Market Trends**: "Cryptocurrency market analysis today"
- **Health Information**: "WHO guidelines on vaccination"

### Mathematical Calculation Tool
Safe mathematical evaluation for calculations, equations, and mathematical analysis.

**Detailed Use Cases:**
- **Basic Arithmetic**: "Calculate 15% tip on $85.50"
- **Percentage Calculations**: "What is 30% of 250?"
- **Unit Conversions**: "Convert 75 Fahrenheit to Celsius"
- **Geometry**: "Area of a circle with radius 12.5 cm"
- **Financial Calculations**: "Compound interest on $5000 at 3.5% for 10 years"
- **Trigonometry**: "Calculate sin(45°) + cos(30°)"
- **Logarithms**: "What is log base 10 of 1000?"
- **Square Roots**: "Square root of 289"
- **Statistical Calculations**: "Standard deviation of [10, 15, 20, 25, 30]"
- **Physics Calculations**: "Kinetic energy with mass 5kg and velocity 10m/s"
- **Engineering Calculations**: "Power consumption: 12V × 3.5A"
- **Scientific Notation**: "Express 0.000045 in scientific notation"

## How Tool Calling Works

### Automatic Detection Process
1. **Message Analysis**: AI analyzes user query for tool usage indicators
2. **Tool Selection**: Determines which tool(s) are needed (search, calculate, or both)
3. **Tool Execution**: Automatically invokes appropriate tools with extracted parameters
4. **Result Integration**: Seamlessly incorporates tool results into AI response
5. **Enhanced Response**: User receives comprehensive answer with real-time data

### Tool Integration
- **Seamless Operation**: Tools work transparently without user intervention
- **Smart Context**: AI understands when tools add value to responses
- **Multiple Tools**: Can use both search and calculation in single response
- **Error Handling**: Graceful fallback to base knowledge if tools fail
- **Performance**: Fast execution with minimal response delays

## Technical Implementation

### Core Files
- `tools.py` - Tool function implementations
- `gemini_api.py` - Gemini 2.0 Flash integration with tool calling
- `chatbot_manage.py` - Tool enablement for conversations

### Security & Safety
- **Safe Math Evaluation**: Restricted function access prevents code execution
- **Rate Limiting**: Web search requests are rate-limited for stability
- **API Security**: Secure DuckDuckGo API integration
- **Error Boundaries**: Robust error handling prevents system crashes
- **Input Validation**: All tool inputs are validated before execution

## Example Interactions

**Complex Query Example:**
```
User: "I need to calculate mortgage payments for a $300,000 loan at 6.5% interest for 30 years, and also find current mortgage rates in California"

AI Response: 
1. Calculates monthly payment: $1,896.20
2. Searches web for current CA mortgage rates
3. Provides comprehensive answer with both calculation and current market data
```

**Multi-Tool Usage:**
```
User: "What's the current Bitcoin price and how much would 0.5 BTC be worth?"

AI Response:
1. Searches for current Bitcoin price
2. Calculates 0.5 × current price
3. Provides both current market data and calculated value
```

## Tool Availability
- Available for both authenticated users and guest users
- Works across all conversation types and sessions
- Integrated with conversation branching and editing features
- Maintains tool context across message edits and branches

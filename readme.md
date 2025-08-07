# Flask JSON Chatbot

A modern Flask-based chatbot application with ChatGPT-style conversation branching, tool calling capabilities, and user authentication.

## Features

- **Conversation Branching**: ChatGPT-style message editing and branch navigation
- **Tool Calling**: Web search and mathematical calculations powered by Gemini 2.0 Flash
- **User Authentication**: Secure login/register system with JWT tokens
- **Session Management**: Save and manage conversation sessions
- **Guest Mode**: Try the chatbot without registration
- **Responsive Design**: Modern UI that works on desktop and mobile

## Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/hselimserdar/flask_json_chatbot
   cd flask_json_chatbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   - Rename `.env.example` to `.env`
   - Follow the detailed [API Keys Setup Guide](API_KEYS_SETUP.md) to obtain and configure:
     ```
     GEMINI_API_KEY=your_gemini_api_key_here
     SECRET_KEY=your_secret_key_here
     ```
   - See [API_KEYS_SETUP.md](API_KEYS_SETUP.md) for step-by-step instructions

4. **Run the application**
   ```bash
   python __init__.py
   ```

5. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - Register a new account or use guest mode

## Usage

- **Chat**: Type messages and receive AI responses
- **Branch Conversations**: Edit previous messages to create conversation branches
- **Navigate Branches**: Use navigation controls to switch between different conversation paths
- **Search Web**: Ask questions that require current information
- **Calculate**: Request mathematical calculations and evaluations

## Advanced Features

For detailed information about tool calling capabilities, web search, and mathematical calculations, see [TOOL_CALLING_FEATURES.md](TOOL_CALLING_FEATURES.md).

## Requirements

- Python 3.8+
- Flask
- Google Gemini API access
- Modern web browser

## Security Notes

- Never commit your `.env` file with real API keys
- Change default secret keys before production deployment
- API keys are required for full functionality

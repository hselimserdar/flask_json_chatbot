# API Keys Setup Guide

This guide will help you obtain the necessary API keys and configure your environment for the Flask JSON Chatbot.

## AI Provider Selection

You can choose between **Gemini** and **DeepSeek R1** as your AI provider by setting the `AI_PROVIDER` environment variable:

- Set `AI_PROVIDER=gemini` to use Google Gemini (default)
- Set `AI_PROVIDER=deepseek` to use DeepSeek R1

## Required API Keys

### 1. Google Gemini API Key (if using Gemini)

The Gemini API key is required for AI-powered conversations and tool calling features.

#### How to Get Your Gemini API Key:

1. **Visit Google AI Studio**
   - Go to [https://aistudio.google.com/](https://aistudio.google.com/)
   - Sign in with your Google account

2. **Access API Keys Section**
   - Click on "Get API key" in the left sidebar
   - Or navigate directly to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

3. **Create a New API Key**
   - Click "Create API key"
   - Select "Create API key in new project" (recommended) or choose an existing project
   - Wait for the key to be generated

4. **Copy Your API Key**
   - Copy the generated API key (it will look like: `AIza...`)
   - ⚠️ **Important**: Store this key securely and never share it publicly

#### Gemini API Features:
- Free tier with generous limits
- Supports text generation, conversation, and tool calling
- No billing setup required for basic usage

### 2. DeepSeek API Key (if using DeepSeek)

The DeepSeek API key is required when using DeepSeek R1 as your AI provider.

#### How to Get Your DeepSeek API Key:

1. **Visit DeepSeek Platform**
   - Go to [https://platform.deepseek.com/](https://platform.deepseek.com/)
   - Sign up for an account or sign in

2. **Access API Keys**
   - Navigate to your account dashboard
   - Look for "API Keys" or "API Management" section

3. **Create a New API Key**
   - Click "Create API Key" or similar
   - Give your key a name (e.g., "Flask Chatbot")
   - Copy the generated key

4. **Copy Your API Key**
   - Copy the generated API key (it will look like: `sk-...`)
   - ⚠️ **Important**: Store this key securely and never share it publicly

#### DeepSeek R1 Features:
- Advanced reasoning capabilities
- Competitive pricing
- High-quality responses

## Environment Configuration

### 1. Create Environment File

1. **Copy the Example File**
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env File**
   Open `.env` in your text editor and add your configuration:
   
   **For Gemini (default):**
   ```
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```
   
   **For DeepSeek R1:**
   ```
   AI_PROVIDER=deepseek
   DEEPSEEK_API_KEY=your_actual_deepseek_api_key_here
   ```

### 2. Optional Environment Variables

You can also configure these optional settings in your `.env` file:

```
# Server Configuration
flaskIP=127.0.0.1
flaskPort=5000

# Debugging (set to "true" for development)
debugging=false
flaskDebugging=false

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key_here
```

## Example .env Files

### For Gemini:
```
# AI Provider Selection
AI_PROVIDER=gemini

# Required API Keys
GEMINI_API_KEY=AIzaSyC1234567890abcdefghijklmnopqrstuvwxyz

# Optional Server Configuration
flaskIP=127.0.0.1
flaskPort=5000

# Development Settings
debugging=false
flaskDebugging=false

# JWT Secret (for secure authentication)
JWT_SECRET_KEY=Kd8fJls9fj2LmPqR7vN4yBx3Wz6AeH2rT9mQ5kL8pX1nC4vS
```

### For DeepSeek R1:
```
# AI Provider Selection
AI_PROVIDER=deepseek

# Required API Keys
DEEPSEEK_API_KEY=sk-1234567890abcdefghijklmnopqrstuvwxyz

# Optional Server Configuration
flaskIP=127.0.0.1
flaskPort=5000

# Development Settings
debugging=false
flaskDebugging=false

# JWT Secret (for secure authentication)
JWT_SECRET_KEY=Kd8fJls9fj2LmPqR7vN4yBx3Wz6AeH2rT9mQ5kL8pX1nC4vS
```
```

## Security Best Practices

### ✅ Do:
- Keep your `.env` file in `.gitignore`
- Use different keys for development and production
- Regenerate keys if they're accidentally exposed
- Use environment variables in production deployments
- Keep API keys secure and private

### ❌ Don't:
- Commit `.env` files to version control
- Share API keys in chat, email, or public forums
- Use simple or predictable secret keys
- Leave debugging enabled in production
- Use the same keys across multiple projects

## Troubleshooting

### Common Issues:

1. **"GEMINI_API_KEY environment variable is not set"**
   - Ensure your `.env` file exists in the project root
   - Check that the key name matches exactly: `GEMINI_API_KEY`
   - Verify the API key is valid and copied correctly

2. **"Invalid API key" errors**
   - Double-check your Gemini API key in Google AI Studio
   - Ensure there are no extra spaces or characters
   - Try regenerating the API key if needed

3. **JWT token errors**
   - Verify your JWT_SECRET_KEY is set and at least 32 characters
   - Clear browser cookies and try again

4. **Import errors for python-dotenv**
   - Run: `pip install python-dotenv`
   - Ensure your virtual environment is activated

## Testing Your Setup

Once configured, test your setup by running:

```bash
python __init__.py
```

If everything is configured correctly:
- The server should start without errors
- You should see: "Debugging is enabled" and "Using JWT_SECRET_KEY" messages
- The application should be accessible at `http://localhost:5000`

## Need Help?

If you encounter issues:
1. Check the [Troubleshooting](#troubleshooting) section above
2. Verify all environment variables are set correctly
3. Ensure your virtual environment has all required packages installed
4. Check the application logs for specific error messages

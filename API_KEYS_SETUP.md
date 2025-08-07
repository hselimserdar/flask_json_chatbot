# API Keys Setup Guide

This guide will help you obtain the necessary API keys and configure your environment for the Flask JSON Chatbot.

## Required API Keys

### 1. Google Gemini API Key

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

### 2. Secret Key for JWT Authentication

The SECRET_KEY is used for secure JWT token generation and session management.

#### How to Generate a Secure Secret Key:

**Option 1: Python (Recommended)**
```python
import secrets
print(secrets.token_urlsafe(32))
```

**Option 2: OpenSSL Command Line**
```bash
openssl rand -base64 32
```

**Option 3: Online Generator**
- Use a secure online generator like [https://randomkeygen.com/](https://randomkeygen.com/)
- Choose "CodeIgniter Encryption Keys" or similar 32+ character option

#### Secret Key Requirements:
- Should be at least 32 characters long
- Use random, unpredictable characters
- Keep it secret and never commit to version control
- Generate a new one for each deployment environment

## Environment Configuration

### 1. Create Environment File

1. **Copy the Example File**
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env File**
   Open `.env` in your text editor and add your keys:
   ```
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   SECRET_KEY=your_generated_secret_key_here
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

## Example .env File

Here's what your complete `.env` file should look like:

```
# Required API Keys
GEMINI_API_KEY=AIzaSyC1234567890abcdefghijklmnopqrstuvwxyz
SECRET_KEY=Kd8fJls9fj2LmPqR7vN4yBx3Wz6AeH2rT9mQ5kL8pX1nC4vS

# Optional Server Configuration
flaskIP=127.0.0.1
flaskPort=5000

# Development Settings
debugging=false
flaskDebugging=false

# JWT Secret (can be same as SECRET_KEY)
JWT_SECRET_KEY=Kd8fJls9fj2LmPqR7vN4yBx3Wz6AeH2rT9mQ5kL8pX1nC4vS
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
   - Verify your SECRET_KEY is set and at least 32 characters
   - Check that JWT_SECRET_KEY is configured
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

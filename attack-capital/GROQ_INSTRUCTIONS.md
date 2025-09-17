# Using Groq with Attack Capital

This project has been updated to support Groq's LLM API as an alternative to Google's Gemini. There are two implementations:

1. Direct Groq API implementation (`simple_server_groq.py`)
2. LangChain integration with Groq (`simple_server_langchain_groq.py`)

## Setup Instructions

1. Install the required packages:
```bash
cd backend
pip install -r requirements_groq.txt
```

2. Get a Groq API key from [Groq's console](https://console.groq.com/)

3. Create a `.env` file in the backend directory (or copy from `.env.example`):
```
GROQ_API_KEY=your_groq_api_key_here
MEM0_API_KEY=m0-BIIaaD4yTCeKto4g3R9piQHwUvbWkvYAixCaCj2k
LIVEKIT_API_KEY=your_livekit_key
LIVEKIT_API_SECRET=your_livekit_secret
LIVEKIT_URL=your_livekit_url
PORT=8000
FRONTEND_URL=http://localhost:3000
```

4. Run one of the Groq-enabled servers:

For direct Groq API:
```bash
cd backend
python simple_server_groq.py
```

For LangChain + Groq:
```bash
cd backend
python simple_server_langchain_groq.py
```

## Available Models

The implementation uses the Llama 3 70B model by default (`llama3-70b-8192`), but you can change this to other models supported by Groq such as:

- `llama3-8b-8192` - Smaller, faster model
- `llama3-70b-8192` - Larger, more capable model
- `mixtral-8x7b-32768` - Mixtral model with longer context
- `gemma-7b-it` - Google's Gemma model

To change the model, update the model name in the respective server file.

## Advantages of Groq

- Fast inference speeds
- Support for multiple open models
- Longer context lengths
- Simple API similar to OpenAI

## Troubleshooting

If you encounter API key errors:
1. Double check that your GROQ_API_KEY is correctly set in the .env file
2. Make sure your account has sufficient credits
3. Check that you're calling the API with the correct model name

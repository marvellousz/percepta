#!/usr/bin/env python3
"""
Helper script to run the MemoryBot backend with proper setup checks
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_env_file():
    """Check if .env file exists and contains required variables"""
    env_file = Path(__file__).parent / ".env"
    example_env_file = Path(__file__).parent / ".env.example"
    
    if not env_file.exists():
        if example_env_file.exists():
            logger.error("❌ .env file not found. Please create one based on .env.example")
            logger.info("You can copy the example file: cp .env.example .env")
        else:
            logger.error("❌ Neither .env nor .env.example files found!")
        return False
    
    load_dotenv(env_file)
    
    # Check required environment variables
    required_vars = [
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "GEMINI_API_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("Using dummy values for missing variables for testing purposes")
        
        # Set dummy values for missing variables
        if "LIVEKIT_API_KEY" in missing_vars:
            os.environ["LIVEKIT_API_KEY"] = "devkey"
        if "LIVEKIT_API_SECRET" in missing_vars:
            os.environ["LIVEKIT_API_SECRET"] = "secret"
        if "LIVEKIT_URL" in missing_vars:
            os.environ["LIVEKIT_URL"] = "ws://localhost:7880"
        if "GEMINI_API_KEY" in missing_vars:
            os.environ["GEMINI_API_KEY"] = "dummy_gemini_api_key"
    
    # Check optional environment variables
    optional_vars = ["MEM0_API_KEY"]
    missing_optional = [var for var in optional_vars if not os.environ.get(var)]
    
    if missing_optional:
        logger.warning(f"⚠️ Missing optional environment variables: {', '.join(missing_optional)}")
        logger.info("MemoryBot will use fallback implementation for missing services")
    
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import livekit
        import google.generativeai
        logger.info("✅ Core dependencies verified")
        
        # Check for optional dependencies
        try:
            import mem0ai
            logger.info("✅ mem0ai module found")
        except ImportError:
            logger.warning("⚠️ mem0ai module not found, will use fallback memory implementation")
        
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("✅ sentence_transformers module found")
        except ImportError:
            logger.warning("⚠️ sentence_transformers module not found, fallback memory will be limited")
            
        try:
            import faiss
            logger.info("✅ faiss module found")
        except ImportError:
            logger.warning("⚠️ faiss module not found, fallback memory will be limited")
            
        return True
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.info("Please install all dependencies: pip install -r requirements.txt")
        return False

def main():
    """Run checks and start the application"""
    logger.info("Running MemoryBot backend setup checks...")
    
    if not check_env_file() or not check_dependencies():
        logger.error("❌ Setup checks failed. Please fix the issues above and try again.")
        return 1
    
    logger.info("✅ All setup checks passed!")
    logger.info("Starting the MemoryBot backend server...")
    
    # Start the server using uvicorn
    try:
        subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", "--reload"], check=True)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

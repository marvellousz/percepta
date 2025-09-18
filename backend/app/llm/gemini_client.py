# gemini_client.py
import os
import logging
import textwrap
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from functools import partial
from time import sleep

import google.generativeai as genai

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class GeminiClient:
    """
    Async-friendly wrapper around the google.generativeai SDK's GenerativeModel.
    - Configures the SDK once using GEMINI_API_KEY.
    - Creates a model instance once and reuses it.
    - Runs blocking generate_content calls in a ThreadPoolExecutor.
    - Provides robust extraction of returned text from common response shapes.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash",
        max_workers: int = 4,
        retry_attempts: int = 2,
        retry_backoff_seconds: float = 0.5,
    ):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        genai.configure(api_key=api_key)
        self.model_name = model_name
        logger.info("Configuring Gemini model: %s", self.model_name)

        # create model instance once (SDK permitting)
        try:
            self.model = genai.GenerativeModel(self.model_name)
        except Exception:
            logger.exception("Failed to create GenerativeModel instance")
            raise

        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._retry_attempts = retry_attempts
        self._retry_backoff_seconds = retry_backoff_seconds

    async def generate_response(
        self, message: str, username: str, context: Optional[str] = None
    ) -> str:
        """
        Asynchronously generate response for given message and username.
        The underlying SDK call is executed in a thread to avoid blocking the event loop.
        """
        prompt = self._create_prompt(message, username, context)

        loop = asyncio.get_running_loop()
        # use partial for picklable callable
        func = partial(self._generate_and_extract, prompt)

        attempt = 0
        while attempt <= self._retry_attempts:
            try:
                response = await loop.run_in_executor(self._executor, func)
                return response
            except Exception:
                attempt += 1
                logger.exception("Gemini generation attempt %d failed", attempt)
                if attempt > self._retry_attempts:
                    break
                await asyncio.sleep(self._retry_backoff_seconds * attempt)

        return "I'm sorry — I couldn't generate a response at this time."

    def _generate_and_extract(self, prompt: str) -> str:
        """
        Blocking function that calls the SDK and extracts text robustly.
        Executed inside a ThreadPoolExecutor.
        """
        try:
            raw = self.model.generate_content(prompt)
        except Exception:
            logger.exception("Error calling model.generate_content")
            raise

        # Try multiple ways to extract a useful string from the response object.
        try:
            # 1) common attribute `text`
            if hasattr(raw, "text") and raw.text:
                return raw.text

            # 2) sometimes there's `result`
            if hasattr(raw, "result") and raw.result:
                return str(raw.result)

            # 3) some SDK shapes provide candidates array/list
            if hasattr(raw, "candidates") and raw.candidates:
                first = raw.candidates[0]
                # candidate might have `content`, `text`, or be a dict-like
                if hasattr(first, "content") and first.content:
                    return first.content
                if hasattr(first, "text") and first.text:
                    return first.text
                # fallback to string conversion
                return str(first)

            # 4) some implementations include `output` or `.outputs`
            if hasattr(raw, "output") and raw.output:
                return str(raw.output)
            if hasattr(raw, "outputs") and raw.outputs:
                return str(raw.outputs)

            # 5) last-resort: string conversion
            return str(raw)
        except Exception:
            logger.exception("Failed to extract text from response object")
            raise

    def _create_prompt(self, message: str, username: str, context: Optional[str]) -> str:
        base = f"""
        You are an AI assistant in a chat application for Percepta.
        Your goal is to be helpful, friendly, and personalized in your responses.

        Username: {username}
        """

        if context:
            base += f"\n\nPrevious conversation context:\n{context}\n"

        base += f"\n{username}'s current message: {message}\n\nYour response:"
        return textwrap.dedent(base).strip()

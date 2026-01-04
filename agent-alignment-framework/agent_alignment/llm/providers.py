"""LLM provider implementations for different services.

This module contains concrete implementations of LLM providers for
OpenAI, Anthropic, and local model services.
"""

import os
from typing import Any, Dict, Optional

from .client import LLMError, LLMProvider, LLMRateLimitError, LLMTimeoutError, LLMUnavailableError


class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
    ):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if None)
            model: Model name to use
            base_url: Custom base URL for API
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY env var")
        
        self.model = model
        self.base_url = base_url
        
        # Import OpenAI client
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        except ImportError:
            raise ImportError("openai package is required for OpenAI provider")
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
        **kwargs
    ) -> str:
        """Generate text using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            error_str = str(e).lower()
            
            if "rate limit" in error_str or "429" in error_str:
                raise LLMRateLimitError(f"OpenAI rate limit exceeded: {e}")
            elif "timeout" in error_str or "504" in error_str:
                raise LLMTimeoutError(f"OpenAI request timed out: {e}")
            elif "503" in error_str or "502" in error_str or "unavailable" in error_str:
                raise LLMUnavailableError(f"OpenAI service unavailable: {e}")
            else:
                raise LLMError(f"OpenAI API error: {e}")
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return f"openai-{self.model}"


class AnthropicProvider(LLMProvider):
    """Anthropic API provider implementation."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-haiku-20240307",
    ):
        """Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if None)
            model: Model name to use
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key must be provided or set in ANTHROPIC_API_KEY env var")
        
        self.model = model
        
        # Import Anthropic client
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package is required for Anthropic provider")
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
        **kwargs
    ) -> str:
        """Generate text using Anthropic API."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            error_str = str(e).lower()
            
            if "rate limit" in error_str or "429" in error_str:
                raise LLMRateLimitError(f"Anthropic rate limit exceeded: {e}")
            elif "timeout" in error_str or "504" in error_str:
                raise LLMTimeoutError(f"Anthropic request timed out: {e}")
            elif "503" in error_str or "502" in error_str or "unavailable" in error_str:
                raise LLMUnavailableError(f"Anthropic service unavailable: {e}")
            else:
                raise LLMError(f"Anthropic API error: {e}")
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return f"anthropic-{self.model}"


class LocalProvider(LLMProvider):
    """Local model provider implementation (e.g., Ollama, vLLM)."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2",
        api_format: str = "ollama",  # "ollama" or "openai"
    ):
        """Initialize local provider.
        
        Args:
            base_url: Base URL for the local model service
            model: Model name to use
            api_format: API format ("ollama" or "openai")
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_format = api_format
        
        # Import requests for HTTP calls
        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("requests package is required for Local provider")
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
        **kwargs
    ) -> str:
        """Generate text using local model service."""
        try:
            if self.api_format == "ollama":
                return self._generate_ollama(prompt, max_tokens, temperature, **kwargs)
            elif self.api_format == "openai":
                return self._generate_openai_compatible(prompt, max_tokens, temperature, **kwargs)
            else:
                raise ValueError(f"Unsupported API format: {self.api_format}")
                
        except Exception as e:
            error_str = str(e).lower()
            
            if "connection" in error_str or "refused" in error_str:
                raise LLMUnavailableError(f"Local model service unavailable: {e}")
            elif "timeout" in error_str:
                raise LLMTimeoutError(f"Local model request timed out: {e}")
            else:
                raise LLMError(f"Local model error: {e}")
    
    def _generate_ollama(self, prompt: str, max_tokens: int, temperature: float, **kwargs) -> str:
        """Generate using Ollama API format."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                **kwargs
            }
        }
        
        response = self.requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "").strip()
    
    def _generate_openai_compatible(self, prompt: str, max_tokens: int, temperature: float, **kwargs) -> str:
        """Generate using OpenAI-compatible API format."""
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        
        response = self.requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return f"local-{self.model}"


class XAIProvider(LLMProvider):
    """X.AI (Grok) API provider implementation."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "grok-3",
        base_url: str = "https://api.x.ai/v1",
    ):
        """Initialize X.AI provider.
        
        Args:
            api_key: X.AI API key (uses XAI_API_KEY env var if None)
            model: Model name to use
            base_url: Base URL for X.AI API
        """
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("X.AI API key must be provided or set in XAI_API_KEY env var")
        
        self.model = model
        self.base_url = base_url
        
        # Import requests for HTTP calls
        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("requests package is required for XAI provider")
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
        **kwargs
    ) -> str:
        """Generate text using X.AI API."""
        try:
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }
            
            response = self.requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            error_str = str(e).lower()
            
            if "rate limit" in error_str or "429" in error_str:
                raise LLMRateLimitError(f"X.AI rate limit exceeded: {e}")
            elif "timeout" in error_str or "504" in error_str:
                raise LLMTimeoutError(f"X.AI request timed out: {e}")
            elif "503" in error_str or "502" in error_str or "unavailable" in error_str:
                raise LLMUnavailableError(f"X.AI service unavailable: {e}")
            else:
                raise LLMError(f"X.AI API error: {e}")
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return f"xai-{self.model}"
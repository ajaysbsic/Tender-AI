"""
LLM Client for Tender-AI using LangChain

Supports multiple LLM providers (OpenAI, Anthropic, etc.) with unified interface.
No API keys required for implementation - tested structure first.
"""

import os
import json
from typing import Optional, Dict, Any, Type
from enum import Enum
import logging

from langchain.llms.base import BaseLLM
from langchain_openai import ChatOpenAI
try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"  # Future support


class LLMModel(str, Enum):
    """Supported models"""
    # OpenAI
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT35_TURBO = "gpt-3.5-turbo"
    
    # Anthropic
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"


class LLMConfig(BaseModel):
    """Configuration for LLM client"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    provider: LLMProvider = LLMProvider.OPENAI
    model: LLMModel = LLMModel.GPT4_TURBO
    temperature: float = 0.0  # Low temp for deterministic extraction
    max_tokens: int = 4096
    timeout: int = 60
    
    # Optional API key (if not in env)
    api_key: Optional[str] = None


class LLMClient:
    """
    Unified LLM client interface for Tender-AI.
    
    Supports multiple providers with consistent interface.
    Handles both structured (JSON) and text outputs.
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize LLM client with config"""
        self.config = config or LLMConfig()
        self.client = self._initialize_client()
        self.model_name = self.config.model.value
        
    def _initialize_client(self) -> BaseLLM:
        """Initialize appropriate LLM client based on config"""
        
        if self.config.provider == LLMProvider.OPENAI:
            return self._init_openai()
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return self._init_anthropic()
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    def _init_openai(self) -> ChatOpenAI:
        """Initialize OpenAI chat client"""
        try:
            api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                logger.warning(
                    "OPENAI_API_KEY not found. LLM will fail at runtime. "
                    "Set OPENAI_API_KEY environment variable or pass api_key in config."
                )
            
            return ChatOpenAI(
                model_name=self.config.model.value,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                api_key=api_key,
                request_timeout=self.config.timeout,
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    def _init_anthropic(self) -> ChatAnthropic:
        """Initialize Anthropic Claude client"""
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "langchain-anthropic not installed. "
                "Install with: pip install langchain-anthropic"
            )
        
        try:
            api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
            
            if not api_key:
                logger.warning(
                    "ANTHROPIC_API_KEY not found. LLM will fail at runtime. "
                    "Set ANTHROPIC_API_KEY environment variable or pass api_key in config."
                )
            
            return ChatAnthropic(
                model=self.config.model.value,
                temperature=self.config.temperature,
                max_tokens_to_sample=self.config.max_tokens,
                anthropic_api_key=api_key,
                timeout=self.config.timeout,
            )
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise
    
    def generate_text(self, prompt: str) -> str:
        """Generate text response from LLM"""
        try:
            response = self.client.invoke(prompt)
            # Extract text from response
            if hasattr(response, 'content'):
                return response.content
            return str(response)
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise
    
    def generate_json(self, prompt: str, output_schema: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate structured JSON response from LLM.
        
        Uses JSON mode (OpenAI) or explicit JSON schema instructions (Anthropic).
        """
        try:
            # Enhance prompt with JSON schema instruction
            schema_json = json.dumps(output_schema.model_json_schema(), indent=2)
            
            enhanced_prompt = f"""{prompt}

IMPORTANT: You MUST respond with ONLY valid JSON that matches this schema:
{schema_json}

Do not include any text outside the JSON. Start with {{ and end with }}."""
            
            response_text = self.generate_text(enhanced_prompt)
            
            # Parse JSON from response
            try:
                # Try to extract JSON if wrapped in markdown code blocks
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                json_data = json.loads(response_text)
                
                # Validate against schema
                validated_output = output_schema(**json_data)
                return validated_output.model_dump()
            
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {response_text}")
                raise ValueError(f"LLM did not return valid JSON: {e}")
        
        except Exception as e:
            logger.error(f"Error generating structured JSON: {e}")
            raise
    
    def batch_generate_json(
        self,
        prompts: list[str],
        output_schema: Type[BaseModel]
    ) -> list[Dict[str, Any]]:
        """
        Generate multiple structured JSON responses.
        
        Note: In production, consider using batch API for cost efficiency.
        """
        results = []
        for i, prompt in enumerate(prompts):
            try:
                logger.info(f"Processing batch item {i+1}/{len(prompts)}")
                result = self.generate_json(prompt, output_schema)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process batch item {i}: {e}")
                results.append({"error": str(e)})
        
        return results
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        try:
            if self.config.provider == LLMProvider.OPENAI:
                # Use tiktoken for OpenAI
                import tiktoken
                encoding = tiktoken.encoding_for_model(self.config.model.value)
                return len(encoding.encode(text))
            else:
                # Rough estimate: ~4 chars per token
                return len(text) // 4
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}")
            return len(text) // 4  # Fallback estimate


class LLMClientFactory:
    """Factory for creating configured LLM clients"""
    
    _instances: Dict[str, LLMClient] = {}
    _default_config: LLMConfig = None
    
    @classmethod
    def set_default_config(cls, config: LLMConfig):
        """Set default configuration for all clients"""
        cls._default_config = config
    
    @classmethod
    def get_client(
        cls,
        provider: Optional[LLMProvider] = None,
        model: Optional[LLMModel] = None,
        use_cached: bool = True
    ) -> LLMClient:
        """Get or create LLM client"""
        
        config = cls._default_config or LLMConfig()
        
        if provider:
            config.provider = provider
        if model:
            config.model = model
        
        # Create cache key
        cache_key = f"{config.provider}:{config.model}"
        
        # Return cached instance if requested
        if use_cached and cache_key in cls._instances:
            return cls._instances[cache_key]
        
        # Create new instance
        client = LLMClient(config)
        
        if use_cached:
            cls._instances[cache_key] = client
        
        return client
    
    @classmethod
    def get_default_client(cls) -> LLMClient:
        """Get default client (OpenAI GPT-4-turbo)"""
        return cls.get_client()


# Convenience functions
def get_llm_client(
    provider: LLMProvider = LLMProvider.OPENAI,
    model: LLMModel = LLMModel.GPT4_TURBO
) -> LLMClient:
    """Convenience function to get LLM client"""
    return LLMClientFactory.get_client(provider=provider, model=model)


def get_default_llm_client() -> LLMClient:
    """Get default LLM client (OpenAI GPT-4-turbo)"""
    return LLMClientFactory.get_default_client()

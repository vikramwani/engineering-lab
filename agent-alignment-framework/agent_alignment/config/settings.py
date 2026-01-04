"""Configuration settings for the agent alignment framework.

This module provides configuration classes for framework settings,
agent configurations, and alignment parameters.
"""

import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FrameworkSettings(BaseModel):
    """Main framework configuration settings."""
    
    # Logging configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    log_to_console: bool = Field(default=True, description="Whether to log to console")
    use_json_logging: bool = Field(default=True, description="Whether to use JSON log format")
    
    # LLM configuration
    llm_provider: str = Field(default="openai", description="LLM provider to use")
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model name")
    llm_api_key: Optional[str] = Field(default=None, description="LLM API key")
    llm_base_url: Optional[str] = Field(default=None, description="Custom LLM base URL")
    
    # Request configuration
    max_retries: int = Field(default=3, description="Maximum retries for failed requests")
    timeout_seconds: int = Field(default=30, description="Request timeout in seconds")
    retry_delay: float = Field(default=1.0, description="Base delay between retries")
    
    # Agent configuration
    default_max_tokens: int = Field(default=500, description="Default max tokens for agents")
    default_temperature: float = Field(default=0.1, description="Default temperature for agents")
    
    # Alignment configuration
    soft_disagreement_threshold: float = Field(default=0.2, description="Threshold for soft disagreement")
    hard_disagreement_threshold: float = Field(default=0.4, description="Threshold for hard disagreement")
    insufficient_signal_threshold: float = Field(default=0.5, description="Threshold for insufficient signal")
    min_confidence_for_consensus: float = Field(default=0.7, description="Minimum confidence for consensus")
    
    # Human-in-the-loop configuration
    enable_hitl: bool = Field(default=True, description="Whether to enable HITL functionality")
    hitl_confidence_threshold: float = Field(default=0.7, description="Confidence threshold for HITL")
    hitl_disagreement_threshold: float = Field(default=0.3, description="Disagreement threshold for HITL")
    
    @classmethod
    def from_env(cls) -> "FrameworkSettings":
        """Create settings from environment variables.
        
        Returns:
            FrameworkSettings: Configuration loaded from environment
        """
        return cls(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE"),
            log_to_console=os.getenv("LOG_TO_CONSOLE", "true").lower() == "true",
            use_json_logging=os.getenv("USE_JSON_LOGGING", "true").lower() == "true",
            
            llm_provider=os.getenv("LLM_PROVIDER", "openai"),
            llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            llm_api_key=os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("XAI_API_KEY"),
            llm_base_url=os.getenv("LLM_BASE_URL"),
            
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", "30")),
            retry_delay=float(os.getenv("RETRY_DELAY", "1.0")),
            
            default_max_tokens=int(os.getenv("DEFAULT_MAX_TOKENS", "500")),
            default_temperature=float(os.getenv("DEFAULT_TEMPERATURE", "0.1")),
            
            soft_disagreement_threshold=float(os.getenv("SOFT_DISAGREEMENT_THRESHOLD", "0.2")),
            hard_disagreement_threshold=float(os.getenv("HARD_DISAGREEMENT_THRESHOLD", "0.4")),
            insufficient_signal_threshold=float(os.getenv("INSUFFICIENT_SIGNAL_THRESHOLD", "0.5")),
            min_confidence_for_consensus=float(os.getenv("MIN_CONFIDENCE_FOR_CONSENSUS", "0.7")),
            
            enable_hitl=os.getenv("ENABLE_HITL", "true").lower() == "true",
            hitl_confidence_threshold=float(os.getenv("HITL_CONFIDENCE_THRESHOLD", "0.7")),
            hitl_disagreement_threshold=float(os.getenv("HITL_DISAGREEMENT_THRESHOLD", "0.3")),
        )


class AgentConfig(BaseModel):
    """Configuration for individual agents."""
    
    name: str = Field(..., description="Unique agent name")
    role_type: str = Field(..., description="Agent role type")
    instruction: str = Field(..., description="Agent instruction")
    prompt_template: Optional[str] = Field(default=None, description="Path to prompt template")
    max_tokens: int = Field(default=500, description="Maximum tokens for this agent")
    temperature: float = Field(default=0.1, description="Temperature for this agent")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Agent metadata")


class AlignmentConfig(BaseModel):
    """Configuration for alignment analysis."""
    
    soft_disagreement_threshold: float = Field(default=0.2, description="Soft disagreement threshold")
    hard_disagreement_threshold: float = Field(default=0.4, description="Hard disagreement threshold")
    insufficient_signal_threshold: float = Field(default=0.5, description="Insufficient signal threshold")
    min_confidence_for_consensus: float = Field(default=0.7, description="Minimum confidence for consensus")
    
    # Weights for consensus calculation
    decision_agreement_weight: float = Field(default=0.4, description="Weight for decision agreement")
    confidence_spread_weight: float = Field(default=0.3, description="Weight for confidence spread")
    avg_confidence_weight: float = Field(default=0.3, description="Weight for average confidence")
    
    # Thresholds for specific disagreement detection
    reasoning_overlap_threshold: float = Field(default=0.3, description="Minimum reasoning overlap")
    evidence_similarity_threshold: float = Field(default=0.2, description="Minimum evidence similarity")


class EvaluationConfig(BaseModel):
    """Configuration for evaluation processes."""
    
    # Agent execution
    max_agent_retries: int = Field(default=3, description="Maximum retries per agent")
    agent_timeout_seconds: int = Field(default=30, description="Timeout per agent")
    require_all_agents: bool = Field(default=False, description="Whether all agents must succeed")
    
    # Parallel execution
    enable_parallel_execution: bool = Field(default=False, description="Whether to run agents in parallel")
    max_parallel_agents: int = Field(default=3, description="Maximum parallel agents")
    
    # Output validation
    validate_agent_decisions: bool = Field(default=True, description="Whether to validate agent decisions")
    strict_json_parsing: bool = Field(default=False, description="Whether to require strict JSON")
    
    # Synthesis
    synthesis_strategy: str = Field(default="judge_priority", description="Strategy for decision synthesis")
    confidence_aggregation: str = Field(default="weighted_average", description="Method for confidence aggregation")


class HITLConfig(BaseModel):
    """Configuration for human-in-the-loop functionality."""
    
    enabled: bool = Field(default=True, description="Whether HITL is enabled")
    
    # Trigger thresholds
    confidence_threshold: float = Field(default=0.7, description="Confidence threshold for HITL")
    disagreement_threshold: float = Field(default=0.3, description="Disagreement threshold for HITL")
    
    # Review configuration
    default_priority: str = Field(default="medium", description="Default review priority")
    review_timeout_hours: int = Field(default=24, description="Default review timeout in hours")
    
    # Notification settings
    notify_on_disagreement: bool = Field(default=True, description="Whether to notify on disagreement")
    notification_channels: List[str] = Field(default_factory=list, description="Notification channels")
    
    # Integration settings
    review_system_url: Optional[str] = Field(default=None, description="External review system URL")
    webhook_url: Optional[str] = Field(default=None, description="Webhook for review notifications")


class FrameworkConfig(BaseModel):
    """Complete framework configuration."""
    
    framework: FrameworkSettings = Field(default_factory=FrameworkSettings)
    alignment: AlignmentConfig = Field(default_factory=AlignmentConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    hitl: HITLConfig = Field(default_factory=HITLConfig)
    
    agents: List[AgentConfig] = Field(default_factory=list, description="Agent configurations")
    
    @classmethod
    def from_file(cls, config_path: str) -> "FrameworkConfig":
        """Load configuration from a file.
        
        Args:
            config_path: Path to configuration file (JSON or YAML)
            
        Returns:
            FrameworkConfig: Loaded configuration
        """
        import json
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                try:
                    import yaml
                    config_data = yaml.safe_load(f)
                except ImportError:
                    raise ImportError("PyYAML is required to load YAML configuration files")
            else:
                config_data = json.load(f)
        
        return cls(**config_data)
    
    @classmethod
    def from_env_and_file(cls, config_path: Optional[str] = None) -> "FrameworkConfig":
        """Load configuration from environment variables and optional file.
        
        Args:
            config_path: Optional path to configuration file
            
        Returns:
            FrameworkConfig: Merged configuration
        """
        # Start with environment-based settings
        framework_settings = FrameworkSettings.from_env()
        config = cls(framework=framework_settings)
        
        # Override with file settings if provided
        if config_path and os.path.exists(config_path):
            file_config = cls.from_file(config_path)
            
            # Merge configurations (file overrides environment)
            config.alignment = file_config.alignment
            config.evaluation = file_config.evaluation
            config.hitl = file_config.hitl
            config.agents = file_config.agents
            
            # Merge framework settings (keep env vars for sensitive data)
            for field_name, field_value in file_config.framework.dict().items():
                if field_name not in ["llm_api_key"] and field_value is not None:
                    setattr(config.framework, field_name, field_value)
        
        return config
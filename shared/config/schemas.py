"""
Configuration schemas using Pydantic for validation and type safety.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
import os


class APIRetryConfig(BaseModel):
    """HTTP retry configuration."""
    status_codes: List[int] = Field(default=[429, 500, 502, 503, 504])
    allowed_methods: List[str] = Field(default=["HEAD", "GET", "OPTIONS"])
    backoff_factor: int = Field(default=1, ge=0)
    total_attempts: int = Field(default=3, ge=1, le=10)


class APIJitterConfig(BaseModel):
    """Request jitter configuration."""
    min: float = Field(default=0.1, ge=0.0, le=1.0)
    max: float = Field(default=0.5, ge=0.0, le=2.0)
    
    @field_validator('max')
    @classmethod
    def max_must_be_greater_than_min(cls, v, info):
        if info.data and 'min' in info.data and v <= info.data['min']:
            raise ValueError('max must be greater than min')
        return v


class APIConfig(BaseModel):
    """API configuration settings."""
    base_url: str = Field(default="https://character-service.dndbeyond.com/character/v5/character/")
    user_agent: str = Field(default="DnDBeyond-Enhanced-Scraper/6.0.0")
    timeout: int = Field(default=30, ge=1, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay: float = Field(default=30.0, ge=30.0)
    
    # HTTP Headers
    headers: Dict[str, str] = Field(default_factory=lambda: {
        "accept": "application/json",
        "accept_language": "en-US,en;q=0.9"
    })
    
    # Retry configuration
    retry: APIRetryConfig = Field(default_factory=APIRetryConfig)
    
    # Request timing
    jitter: APIJitterConfig = Field(default_factory=APIJitterConfig)
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url must start with http:// or https://')
        return v.rstrip('/')


class OutputConfig(BaseModel):
    """Output configuration settings."""
    verbose: bool = Field(default=False)
    include_raw_data: bool = Field(default=False)
    format: str = Field(default="json", pattern="^(json|yaml)$")


class CalculationConfig(BaseModel):
    """Calculation constants."""
    spell_save_dc_base: int = Field(default=8, ge=8, le=15)
    exponential_backoff_base: int = Field(default=2, ge=2, le=10)
    default_character_size: int = Field(default=3, ge=1, le=6)
    default_size_name: str = Field(default="Medium")


class ProjectConfig(BaseModel):
    """Project metadata."""
    name: str = Field(default="DnD Beyond Character Scraper")
    version: str = Field(default="6.0.0")
    description: str = Field(default="Enhanced D&D Beyond character scraper")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(
        default="INFO", 
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Logging level - controls verbosity of log output",
        examples=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    )
    capture_for_analysis: bool = Field(
        default=False,
        description="Capture logs for analysis and debugging purposes"
    )
    # Note: log_to_file and log_file_path are handled in environment-specific configs
    # Note: include_timestamps and include_traceback were unused and removed
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v):
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v not in valid_levels:
            raise ValueError(
                f'Invalid logging level: {v}. '
                f'Valid options are: {", ".join(sorted(valid_levels))}. '
                f'Use DEBUG for development, INFO for production.'
            )
        return v


class TestingConfig(BaseModel):
    """Testing configuration."""
    use_mock_clients: bool = Field(default=False)
    enable_coverage: bool = Field(default=False)
    strict_validation: bool = Field(default=False)
    test_character_ids: List[int] = Field(default_factory=list)
    expected_results: Dict[str, Any] = Field(default_factory=dict)
    mock_api_responses: bool = Field(default=False)
    use_cached_responses: bool = Field(default=False)


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    requests_per_minute: int = Field(default=3, ge=1, le=60)
    delay_between_requests: int = Field(default=5, ge=1, le=300)


class ErrorHandlingConfig(BaseModel):
    """Error handling configuration."""
    graceful_degradation: bool = Field(default=True)
    retry_on_failure: bool = Field(default=True)
    continue_on_error: bool = Field(default=True)


class BatchProcessingConfig(BaseModel):
    """Batch processing configuration."""
    default_character_ids: List[int] = Field(default_factory=list)
    output_directory: str = Field(default="output/")
    backup_directory: str = Field(default="backup/")


class PerformanceConfig(BaseModel):
    """Performance configuration."""
    enable_caching: bool = Field(
        default=False,
        description="Enable calculation result caching for improved performance. "
                   "Uses more memory but speeds up repeated calculations."
    )
    memory_optimization: bool = Field(
        default=True,
        description="Enable memory usage optimizations. "
                   "Recommended to keep enabled unless debugging memory issues."
    )
    # Note: cleanup_temp_files was unused and removed


class DiscordConfig(BaseModel):
    """Discord notification configuration."""
    enabled: bool = Field(default=False)
    webhook_url: Optional[str] = Field(default=None)
    username: str = Field(default="D&D Beyond Scraper")
    avatar_url: Optional[str] = Field(default=None)
    format_type: str = Field(default="detailed")
    notify_on_save: bool = Field(default=True)
    create_snapshots: bool = Field(default=True)
    config_file: str = Field(default="discord/discord_config.yml")
    min_priority: str = Field(default="LOW")
    change_types: List[str] = Field(default_factory=lambda: [
        "level", "experience", "hit_points", "armor_class", "ability_scores",
        "spells_known", "spell_slots", "inventory_items", "equipment", "currency",
        "skills", "proficiencies", "feats", "class_features", "appearance", "background"
    ])
    
    @field_validator('format_type')
    @classmethod
    def validate_format_type(cls, v):
        valid_types = {'compact', 'detailed', 'json'}
        if v not in valid_types:
            raise ValueError(
                f'Invalid format_type: {v}. '
                f'Valid options are: {", ".join(sorted(valid_types))}. '
                f'Use "detailed" for rich Discord embeds, "compact" for simple messages.'
            )
        return v
    
    @field_validator('min_priority')
    @classmethod
    def validate_min_priority(cls, v):
        valid_priorities = {'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'}
        if v not in valid_priorities:
            raise ValueError(
                f'Invalid min_priority: {v}. '
                f'Valid options are: {", ".join(sorted(valid_priorities))}. '
                f'Use LOW to see all changes, HIGH to see only important changes.'
            )
        return v


class EnvironmentConfig(BaseModel):
    """Environment-specific configuration."""
    api: Optional[APIConfig] = Field(default=None)
    output: Optional[OutputConfig] = Field(default=None)
    logging: Optional[LoggingConfig] = Field(default=None)
    testing: Optional[TestingConfig] = Field(default=None)
    rate_limit: Optional[RateLimitConfig] = Field(default=None)
    error_handling: Optional[ErrorHandlingConfig] = Field(default=None)
    batch_processing: Optional[BatchProcessingConfig] = Field(default=None)
    performance: Optional[PerformanceConfig] = Field(default=None)
    discord: Optional[DiscordConfig] = Field(default=None)


class AppConfig(BaseModel):
    """Main application configuration."""
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    calculations: CalculationConfig = Field(default_factory=CalculationConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    testing: TestingConfig = Field(default_factory=TestingConfig)
    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    error_handling: ErrorHandlingConfig = Field(default_factory=ErrorHandlingConfig)
    batch_processing: BatchProcessingConfig = Field(default_factory=BatchProcessingConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    
    # Environment configurations
    environments: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Additional sections for organized structure
    environment: Optional[str] = Field(default="production")
    debug: Optional[bool] = Field(default=False)
    paths: Optional[Dict[str, str]] = Field(default_factory=dict)
    features: Optional[Dict[str, bool]] = Field(default_factory=dict)
    parser: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Allow additional fields for extensibility
    model_config = ConfigDict(extra="allow")
        
    @field_validator('environments')
    @classmethod
    def validate_environments(cls, v):
        valid_envs = {'development', 'testing', 'production'}
        for env in v.keys():
            if env not in valid_envs:
                raise ValueError(f'Unknown environment: {env}. Valid: {valid_envs}')
        return v


class RuleVersionConfig(BaseModel):
    """Rule version configuration."""
    source_2024_ids: List[int] = Field(default_factory=list)


class AbilityConfig(BaseModel):
    """Ability score configuration."""
    names: List[str] = Field(default_factory=list)
    id_mappings: Dict[int, str] = Field(default_factory=dict)
    choice_mappings: Dict[int, str] = Field(default_factory=dict)


class SpellcastingConfig(BaseModel):
    """Spellcasting configuration."""
    abilities: Dict[int, str] = Field(default_factory=dict)


class ClassConfig(BaseModel):
    """Character class configuration."""
    hit_dice: Dict[str, int] = Field(default_factory=dict)
    full_casters: List[str] = Field(default_factory=list)
    half_casters: List[str] = Field(default_factory=list)
    third_casters: List[str] = Field(default_factory=list)


class SkillConfig(BaseModel):
    """Skill configuration."""
    ability_mappings: Dict[str, str] = Field(default_factory=dict)


class FieldNameConfig(BaseModel):
    """Field name constants."""
    name: str = Field(default="name")
    level: str = Field(default="level")
    definition: str = Field(default="definition")
    source_id: str = Field(default="sourceId")


class GameConstantsConfig(BaseModel):
    """Game constants configuration."""
    rule_versions: RuleVersionConfig = Field(default_factory=RuleVersionConfig)
    abilities: AbilityConfig = Field(default_factory=AbilityConfig)
    spellcasting: SpellcastingConfig = Field(default_factory=SpellcastingConfig)
    classes: ClassConfig = Field(default_factory=ClassConfig)
    proficiency_bonus: Dict[int, int] = Field(default_factory=dict)
    skills: SkillConfig = Field(default_factory=SkillConfig)
    alignments: Dict[int, str] = Field(default_factory=dict)
    field_names: FieldNameConfig = Field(default_factory=FieldNameConfig)
    
    model_config = ConfigDict(extra="allow")


class SpellProgressionConfig(BaseModel):
    """Spell slot progression configuration."""
    full_caster: Dict[int, List[int]] = Field(default_factory=dict)
    half_caster: Dict[int, List[int]] = Field(default_factory=dict)
    artificer_2014: Optional[Dict[int, List[int]]] = Field(default=None)
    artificer_2024: Optional[Dict[int, List[int]]] = Field(default=None)


class FeatConfig(BaseModel):
    """Feat system configuration."""
    categories: List[str] = Field(default_factory=list)


class RuleSpecificConfig(BaseModel):
    """Rule-specific configuration (2014/2024)."""
    spell_progressions: SpellProgressionConfig = Field(default_factory=SpellProgressionConfig)
    features: Dict[str, Any] = Field(default_factory=dict)
    feat_categories: Optional[List[str]] = Field(default=None)
    class_updates: Optional[Dict[str, Any]] = Field(default=None)
    
    model_config = ConfigDict(extra="allow")
"""
Tests for the configuration manager.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from src.config.manager import ConfigManager, ConfigPaths, reset_config_manager
from src.config.schemas import AppConfig, GameConstantsConfig


class TestConfigPaths:
    """Test configuration path resolution."""
    
    def test_default_paths(self):
        """Test default path configuration."""
        paths = ConfigPaths()
        
        assert paths.config_dir.name == "config"
        assert paths.main_config.name == "main.yaml"
        assert paths.constants_config.name == "constants.yaml"
        assert paths.rules_2014.name == "2014.yaml"
        assert paths.rules_2024.name == "2024.yaml"


class TestConfigManager:
    """Test configuration manager functionality."""
    
    def setup_method(self):
        """Reset config manager before each test."""
        reset_config_manager()
    
    def test_initialization(self):
        """Test config manager initialization."""
        manager = ConfigManager(environment="testing")
        
        assert manager.environment == "testing"
        assert isinstance(manager.paths, ConfigPaths)
    
    def test_environment_from_env_var(self):
        """Test environment detection from environment variable."""
        with patch.dict(os.environ, {"DNDBS_ENVIRONMENT": "development"}):
            manager = ConfigManager()
            assert manager.environment == "development"
    
    def test_load_yaml_file_success(self, tmp_path):
        """Test successful YAML file loading."""
        # Create test YAML file
        test_file = tmp_path / "test.yaml"
        test_file.write_text("""
project:
  name: "Test Project"
  version: "1.0.0"
api:
  timeout: 30
""")
        
        manager = ConfigManager()
        data = manager.load_yaml_file(test_file)
        
        assert data["project"]["name"] == "Test Project"
        assert data["project"]["version"] == "1.0.0"
        assert data["api"]["timeout"] == 30
    
    def test_load_yaml_file_not_found(self):
        """Test YAML file loading with missing file."""
        manager = ConfigManager()
        
        with pytest.raises(FileNotFoundError):
            manager.load_yaml_file(Path("nonexistent.yaml"))
    
    def test_load_yaml_file_invalid_yaml(self, tmp_path):
        """Test YAML file loading with invalid YAML."""
        # Create invalid YAML file
        test_file = tmp_path / "invalid.yaml"
        test_file.write_text("invalid: yaml: content:")
        
        manager = ConfigManager()
        
        with pytest.raises(ValueError, match="Invalid YAML"):
            manager.load_yaml_file(test_file)
    
    def test_apply_environment_overrides(self):
        """Test environment variable overrides."""
        config_data = {
            "api": {"timeout": 30},
            "output": {"verbose": False}
        }
        
        with patch.dict(os.environ, {
            "DNDBS_API_TIMEOUT": "60",
            "DNDBS_OUTPUT_VERBOSE": "true"
        }):
            manager = ConfigManager()
            result = manager.apply_environment_overrides(config_data)
        
        assert result["api"]["timeout"] == 60
        assert result["output"]["verbose"] is True
    
    def test_merge_configs(self):
        """Test configuration merging."""
        base = {
            "api": {"timeout": 30, "retries": 3},
            "output": {"verbose": False}
        }
        
        override = {
            "api": {"timeout": 60},
            "logging": {"level": "DEBUG"}
        }
        
        manager = ConfigManager()
        result = manager.merge_configs(base, override)
        
        assert result["api"]["timeout"] == 60
        assert result["api"]["retries"] == 3  # Preserved from base
        assert result["output"]["verbose"] is False  # Preserved from base
        assert result["logging"]["level"] == "DEBUG"  # From override
    
    def test_get_config_value(self):
        """Test configuration value retrieval."""
        # Mock the configuration loading
        with patch.object(ConfigManager, 'get_app_config') as mock_config:
            mock_config.return_value.dict.return_value = {
                "api": {"timeout": 30, "retries": 3},
                "output": {"verbose": False}
            }
            
            manager = ConfigManager()
            
            assert manager.get_config_value("api", "timeout") == 30
            assert manager.get_config_value("api", "retries") == 3
            assert manager.get_config_value("nonexistent", default="default") == "default"
    
    def test_validate_config_missing_files(self):
        """Test configuration validation with missing files."""
        manager = ConfigManager()
        
        # Mock file existence checks to return False
        with patch.object(Path, 'exists', return_value=False):
            results = manager.validate_config()
        
        assert not results["valid"]
        assert len(results["errors"]) > 0
        assert any("missing" in error.lower() for error in results["errors"])
    
    def test_get_config_summary(self):
        """Test configuration summary generation."""
        # Mock the configuration
        with patch.object(ConfigManager, 'get_app_config') as mock_config:
            # Create a mock config object
            mock_app_config = AppConfig()
            mock_config.return_value = mock_app_config
            
            manager = ConfigManager(environment="testing")
            summary = manager.get_config_summary()
        
        assert summary["environment"] == "testing"
        assert "project" in summary
        assert "api" in summary
        assert "output" in summary
        assert "config_files" in summary
    
    def test_reload_config(self):
        """Test configuration reloading."""
        manager = ConfigManager()
        
        # Set some cached configs
        manager._app_config = AppConfig()
        manager._constants_config = GameConstantsConfig()
        
        # Reload
        manager.reload_config()
        
        # Check that cached configs are cleared
        assert manager._app_config is None
        assert manager._constants_config is None


class TestEnvironmentVariableOverrides:
    """Test environment variable override functionality."""
    
    def test_boolean_conversion(self):
        """Test boolean environment variable conversion."""
        manager = ConfigManager()
        config_data = {"output": {"verbose": False}}
        
        # Test true values
        for true_val in ["true", "True", "TRUE"]:
            with patch.dict(os.environ, {"DNDBS_OUTPUT_VERBOSE": true_val}):
                result = manager.apply_environment_overrides(config_data.copy())
                assert result["output"]["verbose"] is True
        
        # Test false values
        for false_val in ["false", "False", "FALSE"]:
            with patch.dict(os.environ, {"DNDBS_OUTPUT_VERBOSE": false_val}):
                result = manager.apply_environment_overrides(config_data.copy())
                assert result["output"]["verbose"] is False
    
    def test_numeric_conversion(self):
        """Test numeric environment variable conversion."""
        manager = ConfigManager()
        config_data = {"api": {"timeout": 30}}
        
        # Test integer
        with patch.dict(os.environ, {"DNDBS_API_TIMEOUT": "60"}):
            result = manager.apply_environment_overrides(config_data.copy())
            assert result["api"]["timeout"] == 60
            assert isinstance(result["api"]["timeout"], int)
    
    def test_string_values(self):
        """Test string environment variable handling."""
        manager = ConfigManager()
        config_data = {"api": {"user_agent": "default"}}
        
        with patch.dict(os.environ, {"DNDBS_API_USER_AGENT": "custom-agent/1.0"}):
            result = manager.apply_environment_overrides(config_data.copy())
            assert result["api"]["user_agent"] == "custom-agent/1.0"


@pytest.fixture
def mock_config_files(tmp_path):
    """Create mock configuration files for testing."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    # Create main config
    main_config = config_dir / "main.yaml"
    main_config.write_text("""
project:
  name: "Test Scraper"
  version: "6.0.0"
logging:
  level: "INFO"
""")
    
    # Create scraper config
    scraper_config = config_dir / "scraper.yaml"
    scraper_config.write_text("""
api:
  timeout: 30
  max_retries: 3
output:
  verbose: false
""")
    
    # Create discord config
    discord_config = config_dir / "discord.yaml"
    discord_config.write_text("""
enabled: false
webhook_url: null
""")
    
    # Create parser config (optional for tests)
    parser_config = config_dir / "parser.yaml"
    parser_config.write_text("""
parser:
  defaults:
    enhance_spells: true
""")
    
    # Create constants config
    rules_dir = config_dir / "rules"
    rules_dir.mkdir()
    
    constants_config = rules_dir / "constants.yaml"
    constants_config.write_text("""
rule_versions:
  source_2024_ids: [145, 146, 147]
abilities:
  names: ["strength", "dexterity", "constitution"]
""")
    
    # Create rule configs
    rules_2014 = rules_dir / "2014.yaml"
    rules_2014.write_text("""
spell_progressions:
  full_caster:
    1: [2, 0, 0]
features:
  species_terminology: "race"
""")
    
    rules_2024 = rules_dir / "2024.yaml"
    rules_2024.write_text("""
spell_progressions:
  full_caster:
    1: [2, 0, 0]
features:
  species_terminology: "species"
""")
    
    return config_dir


class TestIntegrationWithRealFiles:
    """Integration tests with actual configuration files."""
    
    def test_load_all_configs(self, mock_config_files):
        """Test loading all configuration files."""
        manager = ConfigManager(config_dir=str(mock_config_files))
        
        # Test app config
        app_config = manager.get_app_config()
        assert app_config.project.name == "Test Scraper"
        assert app_config.api.timeout == 30
        
        # Test constants config
        constants_config = manager.get_constants_config()
        assert constants_config.rule_versions.source_2024_ids == [145, 146, 147]
        
        # Test rule configs
        rules_2014 = manager.get_rules_config("2014")
        assert rules_2014.features["species_terminology"] == "race"
        
        rules_2024 = manager.get_rules_config("2024")
        assert rules_2024.features["species_terminology"] == "species"
    
    def test_validation_with_real_files(self, mock_config_files):
        """Test validation with real configuration files."""
        manager = ConfigManager(config_dir=str(mock_config_files))
        
        results = manager.validate_config()
        
        assert results["valid"]
        assert len(results["errors"]) == 0
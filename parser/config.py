"""
Parser Configuration Manager

Handles loading and managing parser-specific configuration from YAML files.
Integrates with the main project config system while providing parser-specific defaults.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Import main config system
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.config.manager import ConfigManager as MainConfigManager


class ParserConfigManager:
    """
    Parser-specific configuration manager.
    
    Combines main project config with parser-specific settings and CLI overrides.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize parser config manager."""
        self.main_config = MainConfigManager()
        
        # Find parser config file
        if config_file:
            self.parser_config_path = Path(config_file)
        else:
            # Default location relative to this file
            project_root = Path(__file__).parent.parent
            self.parser_config_path = project_root / "config" / "parser.yaml"
        
        self._parser_config_data = None
        self._load_parser_config()
    
    def _load_parser_config(self):
        """Load parser-specific configuration from YAML file."""
        try:
            if self.parser_config_path.exists():
                with open(self.parser_config_path, 'r', encoding='utf-8') as f:
                    self._parser_config_data = yaml.safe_load(f) or {}
            else:
                self._parser_config_data = {}
        except Exception as e:
            print(f"Warning: Could not load parser config from {self.parser_config_path}: {e}")
            self._parser_config_data = {}
    
    def get_parser_config(self, *keys: str, default: Any = None) -> Any:
        """Get a parser-specific configuration value using dot notation."""
        current = self._parser_config_data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def get_main_config(self, *keys: str, default: Any = None) -> Any:
        """Get a value from the main project configuration."""
        return self.main_config.get_config_value(*keys, default=default)
    
    def get_default(self, setting: str, default: Any = None) -> Any:
        """Get a default setting value."""
        return self.get_parser_config("parser", "defaults", setting, default=default)
    
    def get_template_setting(self, setting: str, default: Any = None) -> Any:
        """Get a template-related setting."""
        return self.get_parser_config("parser", "templates", setting, default=default)
    
    def get_output_setting(self, setting: str, default: Any = None) -> Any:
        """Get an output formatting setting."""
        return self.get_parser_config("parser", "output", setting, default=default)
    
    def get_spell_setting(self, setting: str, default: Any = None) -> Any:
        """Get a spell enhancement setting."""
        return self.get_parser_config("parser", "spell_enhancement", setting, default=default)
    
    def get_logging_setting(self, setting: str, default: Any = None) -> Any:
        """Get a logging setting."""
        return self.get_parser_config("parser", "logging", setting, default=setting)
    
    def resolve_paths(self) -> Dict[str, Path]:
        """Resolve all relevant file paths."""
        # Get project root
        project_root = Path(__file__).parent.parent
        
        # Get paths from main config
        scraper_path = self.get_main_config("paths", "scraper", default="scraper/enhanced_dnd_scraper.py")
        spells_path = self.get_main_config("paths", "spells_folder", default="obsidian/spells")
        
        # Get JSX component directory from parser config
        jsx_dir = self.get_template_setting("jsx_components_dir", default="z_Templates")
        
        return {
            "project_root": project_root,
            "scraper": project_root / scraper_path,
            "spells": project_root / spells_path,
            "jsx_components": Path(jsx_dir),  # This might be relative to Obsidian vault
            "parser_config": self.parser_config_path
        }
    
    def get_datacorejsx_template(self, component_type: str, **kwargs) -> str:
        """Get a datacorejsx code block template with variable substitution."""
        template = self.get_parser_config("parser", "templates", "datacorejsx", component_type)
        
        if template and kwargs:
            # Simple template variable substitution
            for key, value in kwargs.items():
                template = template.replace(f"{{{key}}}", str(value))
        
        return template or ""
    
    def should_enhance_spells(self) -> bool:
        """Check if spell enhancement is enabled."""
        return self.get_spell_setting("enabled", default=True)
    
    def get_spell_file_suffix(self) -> str:
        """Get the expected suffix for spell files."""
        return self.get_spell_setting("file_suffix", default="-xphb.md")
    
    def get_logging_level(self) -> str:
        """Get the logging level."""
        return self.get_logging_setting("level", default="INFO")
    
    def apply_cli_overrides(self, **cli_args):
        """Apply command-line argument overrides to config."""
        # This method allows CLI args to override config defaults
        # Implementation would update internal state based on CLI args
        pass
    
    def get_effective_config(self, **cli_overrides) -> Dict[str, Any]:
        """Get the effective configuration after applying CLI overrides."""
        config = {
            "enhance_spells": self.get_default("enhance_spells", True),
            "use_dnd_ui_toolkit": self.get_default("use_dnd_ui_toolkit", False),
            "use_yaml_frontmatter": self.get_default("use_yaml_frontmatter", False),
            "verbose": self.get_default("verbose", False),
            "rule_version": self.get_default("rule_version", "auto"),
        }
        
        # Apply CLI overrides
        config.update(cli_overrides)
        
        return config


def get_parser_config(config_file: Optional[str] = None) -> ParserConfigManager:
    """Factory function to create a parser config manager."""
    return ParserConfigManager(config_file)
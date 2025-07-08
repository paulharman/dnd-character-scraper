#!/usr/bin/env python3
"""
Configuration System Test Script

Quick test script to validate the configuration management system.
"""

import sys
import json
from pathlib import Path

# Add src to path for importing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.manager import ConfigManager


def test_configuration():
    """Test the configuration system."""
    print("D&D Beyond Character Scraper - Configuration Test")
    print("=" * 50)
    
    try:
        # Test different environments
        environments = ["development", "testing", "production"]
        
        for env in environments:
            print(f"\n🧪 Testing {env} environment...")
            
            try:
                manager = ConfigManager(environment=env)
                
                # Validate configuration
                validation = manager.validate_config()
                if validation["valid"]:
                    print(f"✅ {env} configuration is valid")
                else:
                    print(f"❌ {env} configuration has errors:")
                    for error in validation["errors"]:
                        print(f"   - {error}")
                    if validation["warnings"]:
                        print(f"⚠️  Warnings:")
                        for warning in validation["warnings"]:
                            print(f"   - {warning}")
                
                # Get configuration summary
                summary = manager.get_config_summary()
                print(f"📋 Configuration Summary for {env}:")
                print(f"   - Project: {summary['project']['name']} v{summary['project']['version']}")
                print(f"   - API Timeout: {summary['api']['timeout']}s")
                print(f"   - Max Retries: {summary['api']['max_retries']}")
                print(f"   - Verbose Output: {summary['output']['verbose']}")
                
                # Test specific config values
                api_config = manager.get_app_config().api
                print(f"   - Base URL: {api_config.base_url}")
                print(f"   - User Agent: {api_config.user_agent}")
                
            except Exception as e:
                print(f"❌ Error testing {env}: {str(e)}")
        
        # Test game constants
        print(f"\n🎲 Testing game constants...")
        try:
            manager = ConfigManager(environment="testing")
            constants = manager.get_constants_config()
            
            print(f"✅ Game constants loaded successfully")
            print(f"   - Ability names: {len(constants.abilities.names)} abilities")
            print(f"   - Classes with hit dice: {len(constants.classes.hit_dice)} classes")
            print(f"   - 2024 source IDs: {constants.rule_versions.source_2024_ids}")
            
        except Exception as e:
            print(f"❌ Error loading game constants: {str(e)}")
        
        # Test rule-specific configs
        print(f"\n📜 Testing rule-specific configurations...")
        try:
            manager = ConfigManager(environment="testing")
            
            # Test 2014 rules
            rules_2014 = manager.get_rules_config("2014")
            print(f"✅ 2014 rules loaded - Species terminology: {rules_2014.features.get('species_terminology', 'N/A')}")
            
            # Test 2024 rules
            rules_2024 = manager.get_rules_config("2024")
            print(f"✅ 2024 rules loaded - Species terminology: {rules_2024.features.get('species_terminology', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Error loading rule configs: {str(e)}")
        
        print(f"\n🎉 Configuration system test completed!")
        return True
        
    except Exception as e:
        print(f"💥 Critical error: {str(e)}")
        return False


def test_environment_variables():
    """Test environment variable overrides."""
    import os
    
    print(f"\n🌍 Testing environment variable overrides...")
    
    # Set test environment variables
    test_env_vars = {
        "DNDBS_API_TIMEOUT": "60",
        "DNDBS_OUTPUT_VERBOSE": "true",
        "DNDBS_LOG_LEVEL": "DEBUG"
    }
    
    # Store original values
    original_values = {}
    for key in test_env_vars:
        original_values[key] = os.environ.get(key)
    
    try:
        # Set test values
        for key, value in test_env_vars.items():
            os.environ[key] = value
        
        manager = ConfigManager(environment="testing")
        config = manager.get_app_config()
        
        print(f"✅ Environment variables applied:")
        print(f"   - API Timeout: {config.api.timeout} (should be 60)")
        print(f"   - Verbose Output: {config.output.verbose} (should be True)")
        print(f"   - Log Level: {config.logging.level} (should be DEBUG)")
        
        # Verify values
        assert config.api.timeout == 60, f"Expected timeout 60, got {config.api.timeout}"
        assert config.output.verbose is True, f"Expected verbose True, got {config.output.verbose}"
        assert config.logging.level == "DEBUG", f"Expected log level DEBUG, got {config.logging.level}"
        
        print(f"✅ All environment variable overrides working correctly!")
        
    finally:
        # Restore original values
        for key, value in original_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    success = test_configuration()
    test_environment_variables()
    
    if success:
        print(f"\n✨ All tests passed! Configuration system is ready.")
        sys.exit(0)
    else:
        print(f"\n💥 Tests failed! Check configuration files.")
        sys.exit(1)
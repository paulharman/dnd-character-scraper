#!/usr/bin/env python3
"""
Security audit script for D&D Beyond Character Scraper.

This script scans the project for potential security issues including:
- Hardcoded webhook URLs
- Session cookies in configuration files
- Sensitive data in version control
- File permission issues
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from discord.services.configuration_validator import ConfigurationValidator, SecurityWarning, SecurityLevel
except ImportError:
    print("Warning: Could not import configuration validator. Some checks will be skipped.")
    ConfigurationValidator = None


class SecurityAuditor:
    """Comprehensive security auditor for the project."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.validator = ConfigurationValidator() if ConfigurationValidator else None
        
        # Patterns to search for
        self.webhook_pattern = re.compile(r'https://discord\.com/api/webhooks/\d{10,}/[a-zA-Z0-9_-]{20,}')
        self.cookie_pattern = re.compile(r'session.*cookie.*[a-zA-Z0-9]{20,}', re.IGNORECASE)
        self.api_key_pattern = re.compile(r'(api[_-]?key|token|secret)["\']?\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}', re.IGNORECASE)
        
        # Files to scan
        self.scan_extensions = ['.py', '.yaml', '.yml', '.json', '.txt', '.md', '.sh', '.bat', '.env']
        
        # Files/directories to exclude
        self.exclude_patterns = [
            r'\.git/',
            r'__pycache__/',
            r'\.pytest_cache/',
            r'node_modules/',
            r'venv/',
            r'\.env$',  # These should be in .gitignore anyway
            r'test_.*\.py$',
            r'.*_test\.py$',
            r'.*\.template$'
        ]
    
    def is_excluded(self, file_path: Path) -> bool:
        """Check if file should be excluded from scanning."""
        path_str = str(file_path.relative_to(self.project_root))
        
        for pattern in self.exclude_patterns:
            if re.search(pattern, path_str):
                return True
        return False
    
    def scan_file_for_secrets(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan a single file for potential secrets."""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    # Check for webhook URLs
                    if self.webhook_pattern.search(line):
                        findings.append({
                            'type': 'webhook_url',
                            'severity': 'HIGH',
                            'file': str(file_path.relative_to(self.project_root)),
                            'line': line_num,
                            'message': 'Discord webhook URL found',
                            'recommendation': 'Use environment variables instead'
                        })
                    
                    # Check for session cookies
                    if self.cookie_pattern.search(line):
                        findings.append({
                            'type': 'session_cookie',
                            'severity': 'HIGH',
                            'file': str(file_path.relative_to(self.project_root)),
                            'line': line_num,
                            'message': 'Session cookie found',
                            'recommendation': 'Use environment variables instead'
                        })
                    
                    # Check for API keys/tokens
                    if self.api_key_pattern.search(line):
                        findings.append({
                            'type': 'api_key',
                            'severity': 'MEDIUM',
                            'file': str(file_path.relative_to(self.project_root)),
                            'line': line_num,
                            'message': 'Potential API key or token found',
                            'recommendation': 'Verify if this is sensitive data and use environment variables if needed'
                        })
        
        except (IOError, OSError, UnicodeDecodeError) as e:
            print(f"Warning: Could not scan {file_path}: {e}")
        
        return findings
    
    def check_gitignore(self) -> List[Dict[str, Any]]:
        """Check if .gitignore has appropriate security entries."""
        findings = []
        gitignore_path = self.project_root / '.gitignore'
        
        if not gitignore_path.exists():
            findings.append({
                'type': 'missing_gitignore',
                'severity': 'MEDIUM',
                'file': '.gitignore',
                'message': '.gitignore file is missing',
                'recommendation': 'Create .gitignore to exclude sensitive files'
            })
            return findings
        
        try:
            with open(gitignore_path, 'r') as f:
                gitignore_content = f.read()
            
            # Check for important security patterns
            security_patterns = [
                ('config/discord.yaml', 'Discord configuration files'),
                ('.env', 'Environment files'),
                ('**/*_secrets.*', 'Secret files'),
                ('**/*webhook*', 'Webhook files')
            ]
            
            for pattern, description in security_patterns:
                if pattern not in gitignore_content:
                    findings.append({
                        'type': 'gitignore_missing_pattern',
                        'severity': 'LOW',
                        'file': '.gitignore',
                        'message': f'Missing security pattern: {pattern}',
                        'recommendation': f'Add pattern to exclude {description}'
                    })
        
        except (IOError, OSError) as e:
            findings.append({
                'type': 'gitignore_error',
                'severity': 'MEDIUM',
                'file': '.gitignore',
                'message': f'Could not read .gitignore: {e}',
                'recommendation': 'Ensure .gitignore is readable'
            })
        
        return findings
    
    def check_file_permissions(self) -> List[Dict[str, Any]]:
        """Check file permissions for sensitive files."""
        findings = []
        
        # Files that should have restricted permissions
        sensitive_files = [
            'config/discord.yaml',
            '.env',
            '.env.local',
            '.env.production'
        ]
        
        for file_path in sensitive_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    stat_info = os.stat(full_path)
                    permissions = oct(stat_info.st_mode)[-3:]
                    
                    # Check if file is world-readable (last digit >= 4)
                    if int(permissions[2]) >= 4:
                        findings.append({
                            'type': 'file_permissions',
                            'severity': 'MEDIUM',
                            'file': file_path,
                            'message': f'File is world-readable (permissions: {permissions})',
                            'recommendation': 'Restrict permissions: chmod 600 (owner read/write only)'
                        })
                
                except (OSError, ValueError) as e:
                    print(f"Warning: Could not check permissions for {file_path}: {e}")
        
        return findings
    
    def audit_configurations(self) -> List[Dict[str, Any]]:
        """Audit configuration files using the configuration validator."""
        findings = []
        
        if not self.validator:
            return findings
        
        config_files = [
            'config/discord.yaml',
            'discord/discord_config.yml'
        ]
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    import yaml
                    with open(config_path, 'r') as f:
                        config_data = yaml.safe_load(f)
                    
                    if config_data:
                        result = self.validator.validate_discord_config(config_data, str(config_path))
                        
                        for warning in result.security_warnings:
                            findings.append({
                                'type': 'config_security',
                                'severity': warning.severity.value,
                                'file': config_file,
                                'message': warning.message,
                                'recommendation': warning.recommendation
                            })
                
                except Exception as e:
                    findings.append({
                        'type': 'config_error',
                        'severity': 'MEDIUM',
                        'file': config_file,
                        'message': f'Could not audit configuration: {e}',
                        'recommendation': 'Ensure configuration file is valid YAML'
                    })
        
        return findings
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Run complete security audit."""
        print("Starting security audit...")
        
        all_findings = []
        
        # Scan files for secrets
        print("Scanning files for secrets...")
        for file_path in self.project_root.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix in self.scan_extensions and 
                not self.is_excluded(file_path)):
                
                findings = self.scan_file_for_secrets(file_path)
                all_findings.extend(findings)
        
        # Check .gitignore
        print("Checking .gitignore...")
        gitignore_findings = self.check_gitignore()
        all_findings.extend(gitignore_findings)
        
        # Check file permissions
        print("Checking file permissions...")
        permission_findings = self.check_file_permissions()
        all_findings.extend(permission_findings)
        
        # Audit configurations
        print("Auditing configurations...")
        config_findings = self.audit_configurations()
        all_findings.extend(config_findings)
        
        # Categorize findings
        high_severity = [f for f in all_findings if f['severity'] == 'HIGH']
        medium_severity = [f for f in all_findings if f['severity'] == 'MEDIUM']
        low_severity = [f for f in all_findings if f['severity'] == 'LOW']
        
        return {
            'total_findings': len(all_findings),
            'high_severity': len(high_severity),
            'medium_severity': len(medium_severity),
            'low_severity': len(low_severity),
            'findings': {
                'high': high_severity,
                'medium': medium_severity,
                'low': low_severity
            }
        }
    
    def print_report(self, audit_results: Dict[str, Any]):
        """Print formatted audit report."""
        print("\n" + "="*60)
        print("SECURITY AUDIT REPORT")
        print("="*60)
        
        total = audit_results['total_findings']
        high = audit_results['high_severity']
        medium = audit_results['medium_severity']
        low = audit_results['low_severity']
        
        print(f"Total Findings: {total}")
        print(f"High Severity: {high}")
        print(f"Medium Severity: {medium}")
        print(f"Low Severity: {low}")
        print()
        
        if total == 0:
            print("No security issues found! Your project looks secure.")
            return
        
        # Print findings by severity
        for severity, findings in audit_results['findings'].items():
            if not findings:
                continue
                
            print(f"{severity.upper()} SEVERITY FINDINGS:")
            print("-" * 40)
            
            for finding in findings:
                print(f"File: {finding['file']}")
                if 'line' in finding:
                    print(f"Line: {finding['line']}")
                print(f"Issue: {finding['message']}")
                print(f"Recommendation: {finding['recommendation']}")
                print()
        
        print("NEXT STEPS:")
        print("1. Address HIGH severity issues immediately")
        print("2. Review MEDIUM severity issues")
        print("3. Consider LOW severity improvements")
        print("4. Run this audit regularly")
        print()


def main():
    """Main function."""
    auditor = SecurityAuditor()
    
    try:
        results = auditor.run_full_audit()
        auditor.print_report(results)
        
        # Save detailed results to file
        results_file = auditor.project_root / 'security_audit_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Detailed results saved to: {results_file}")
        
        # Exit with error code if high severity issues found
        if results['high_severity'] > 0:
            print("\nSecurity audit failed due to high severity issues.")
            return 1
        else:
            print("\nSecurity audit passed.")
            return 0
    
    except Exception as e:
        print(f"Security audit failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
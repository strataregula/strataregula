"""
Integration tests for StrataRegula security system
Tests end-to-end security workflows and CI/CD integration
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestSecurityIntegration(unittest.TestCase):
    """Integration tests for complete security system"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.root_dir = Path(__file__).parent.parent.parent
        self.script_path = self.root_dir / "secret-audit.ps1"
        self.test_repo = None
    
    def tearDown(self):
        """Clean up test environment"""
        if self.test_repo and os.path.exists(self.test_repo):
            import shutil
            shutil.rmtree(self.test_repo)
    
    def create_mock_repository(self, files: dict) -> str:
        """Create a mock Git repository for testing"""
        self.test_repo = tempfile.mkdtemp(prefix="strataregula_integration_test_")
        
        # Initialize Git repo
        subprocess.run(['git', 'init'], cwd=self.test_repo, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], 
                      cwd=self.test_repo, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], 
                      cwd=self.test_repo, capture_output=True)
        
        # Create files
        for filepath, content in files.items():
            full_path = os.path.join(self.test_repo, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
        
        # Copy security scripts to test repo
        import shutil
        shutil.copy(self.script_path, self.test_repo)
        
        return self.test_repo
    
    def test_end_to_end_detection_workflow(self):
        """Test complete detection workflow from commit to CI"""
        # Create repo with secrets
        files = {
            'src/config.py': '''
# Configuration with secrets
GITHUB_TOKEN = "ghp_1234567890123456789012345678901234567890"
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
''',
            'src/clean_file.py': '''
# Clean configuration
DATABASE_URL = os.environ.get("DATABASE_URL")
''',
            '.github/workflows/security.yml': '''
name: Security Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run security scan
        run: pwsh ./secret-audit.ps1
'''
        }
        
        repo_path = self.create_mock_repository(files)
        
        # Test PowerShell scan
        result = subprocess.run([
            'pwsh', '-File', 'secret-audit.ps1', '-ScanPath', '.'
        ], cwd=repo_path, capture_output=True, text=True)
        
        # Should detect secrets
        self.assertEqual(result.returncode, 1)
        self.assertIn("SECRETS DETECTED", result.stdout)
        self.assertIn("GitHub Personal Access Token", result.stdout)
        self.assertIn("AWS Access Key ID", result.stdout)
    
    def test_false_positive_handling(self):
        """Test handling of legitimate patterns that might trigger false positives"""
        files = {
            'docs/README.md': '''
# Security Documentation

Example patterns to avoid:
- Don't use patterns like `ghp_` for GitHub tokens
- AWS keys start with `AKIA` but this is just documentation
- OpenAI keys look like `sk-...` but this is explanation

## Configuration Examples
```python
# Use environment variables
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
```
''',
            'tests/test_patterns.py': '''
def test_token_patterns():
    """Test that we can identify token patterns"""
    # These are test patterns, not real tokens
    github_pattern = "ghp_" + "x" * 36
    aws_pattern = "AKIA" + "X" * 16
    
    assert is_github_token_pattern(github_pattern)
    assert is_aws_key_pattern(aws_pattern)
'''
        }
        
        repo_path = self.create_mock_repository(files)
        
        # Test scan - should be clean due to context
        result = subprocess.run([
            'pwsh', '-File', 'secret-audit.ps1', '-ScanPath', '.'
        ], cwd=repo_path, capture_output=True, text=True)
        
        # Should be clean (documentation and test patterns)
        self.assertEqual(result.returncode, 0)
        self.assertIn("No secrets detected", result.stdout)
    
    def test_multi_file_secret_detection(self):
        """Test detection across multiple files and directories"""
        files = {
            'backend/config/database.py': '''
DATABASE_CONFIG = {
    "host": "localhost",
    "user": "admin",
    "password": "secure_password_123"  # This might trigger detection
}
''',
            'frontend/.env': '''
REACT_APP_API_URL=http://localhost:3000
GITHUB_TOKEN=ghp_1234567890123456789012345678901234567890
''',
            'scripts/deploy.sh': '''#!/bin/bash
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
''',
            'tests/test_clean.py': '''
import unittest

class TestClean(unittest.TestCase):
    def test_example(self):
        self.assertTrue(True)
'''
        }
        
        repo_path = self.create_mock_repository(files)
        
        result = subprocess.run([
            'pwsh', '-File', 'secret-audit.ps1', '-ScanPath', '.', '-Verbose'
        ], cwd=repo_path, capture_output=True, text=True)
        
        # Should detect secrets in multiple files
        self.assertEqual(result.returncode, 1)
        self.assertIn("GitHub Personal Access Token", result.stdout)
        self.assertIn("AWS Access Key ID", result.stdout)
    
    def test_exclusion_effectiveness(self):
        """Test that exclusion patterns work correctly"""
        files = {
            # These should be excluded
            '__pycache__/cached_secrets.py': 'ghp_1234567890123456789012345678901234567890',
            'node_modules/package/secret.js': 'AKIAIOSFODNN7EXAMPLE',
            '.git/config': 'sk-1234567890123456789012345678901234567890',
            'build/secrets.json': '{"token": "ghp_1234567890123456789012345678901234567890"}',
            'dist/bundle.js': 'const token="ghp_1234567890123456789012345678901234567890"',
            
            # This should be scanned
            'src/main.py': '''
import os

def get_token():
    return os.environ.get("GITHUB_TOKEN", "")

print("Application starting...")
'''
        }
        
        repo_path = self.create_mock_repository(files)
        
        result = subprocess.run([
            'pwsh', '-File', 'secret-audit.ps1', '-ScanPath', '.', '-Verbose'
        ], cwd=repo_path, capture_output=True, text=True)
        
        # Should be clean because excluded directories contain the secrets
        self.assertEqual(result.returncode, 0)
        self.assertIn("No secrets detected", result.stdout)
    
    def test_performance_with_large_repository(self):
        """Test performance with a larger number of files"""
        files = {}
        
        # Create 100 clean files
        for i in range(100):
            files[f'src/module_{i}.py'] = f'''
"""Module {i} - Clean implementation"""

import os
from typing import Optional

class Module{i}:
    def __init__(self):
        self.config = os.environ.get("MODULE_{i}_CONFIG", "{{}}")
    
    def process(self, data: str) -> str:
        return f"Processed by module {i}: {{data}}"
'''
        
        # Add one file with a secret
        files['src/config_with_secret.py'] = '''
# This file contains a secret
GITHUB_TOKEN = "ghp_1234567890123456789012345678901234567890"
'''
        
        repo_path = self.create_mock_repository(files)
        
        import time
        start_time = time.time()
        
        result = subprocess.run([
            'pwsh', '-File', 'secret-audit.ps1', '-ScanPath', '.'
        ], cwd=repo_path, capture_output=True, text=True, timeout=60)
        
        end_time = time.time()
        scan_duration = end_time - start_time
        
        # Should detect the secret
        self.assertEqual(result.returncode, 1)
        self.assertIn("GitHub Personal Access Token", result.stdout)
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(scan_duration, 30, 
                       f"Scan took {scan_duration:.2f} seconds, too slow")
    
    def test_utf8_and_special_characters(self):
        """Test handling of UTF-8 and special characters"""
        files = {
            'src/unicode_config.py': '''
# Configuration with Unicode comments
# 設定ファイル - これは日本語のコメントです
GITHUB_TOKEN = "ghp_1234567890123456789012345678901234567890"

# Émojis and special chars: 🔒🛡️⚡
SECRET_KEY = "not_a_real_secret_but_contains_unicode_🔑"
''',
            'src/encoding_test.py': '''
# -*- coding: utf-8 -*-
"""
Test file with various encodings and characters
Тест с кириллицей
测试中文字符
"""

def process_data(data: str) -> str:
    return f"Processed: {data}"
'''
        }
        
        repo_path = self.create_mock_repository(files)
        
        result = subprocess.run([
            'pwsh', '-File', 'secret-audit.ps1', '-ScanPath', '.'
        ], cwd=repo_path, capture_output=True, text=True)
        
        # Should handle UTF-8 correctly and detect the GitHub token
        self.assertEqual(result.returncode, 1)
        self.assertIn("GitHub Personal Access Token", result.stdout)


class TestCIWorkflowIntegration(unittest.TestCase):
    """Test CI/CD workflow integration"""
    
    def test_workflow_syntax_validation(self):
        """Test that workflow YAML files are syntactically correct"""
        workflow_files = [
            Path(__file__).parent.parent.parent / ".github" / "workflows" / "security.yml",
            Path(__file__).parent.parent.parent / ".github" / "workflows" / "secret-audit.yml"
        ]
        
        try:
            import yaml
            
            for workflow_file in workflow_files:
                if workflow_file.exists():
                    with open(workflow_file) as f:
                        workflow_content = yaml.safe_load(f)
                    
                    # Basic workflow structure validation
                    self.assertIn('name', workflow_content)
                    self.assertIn('on', workflow_content)
                    self.assertIn('jobs', workflow_content)
                    
                    # Validate job structure
                    for job_name, job_config in workflow_content['jobs'].items():
                        self.assertIn('runs-on', job_config)
                        self.assertIn('steps', job_config)
                        
                        # Check steps structure
                        for step in job_config['steps']:
                            self.assertTrue(
                                'name' in step or 'uses' in step or 'run' in step,
                                f"Invalid step in job {job_name}: {step}"
                            )
                        
        except ImportError:
            self.skipTest("PyYAML not available for workflow validation")
    
    def test_required_workflow_components(self):
        """Test that workflows contain required security components"""
        security_workflow = Path(__file__).parent.parent.parent / ".github" / "workflows" / "security.yml"
        
        if not security_workflow.exists():
            self.skipTest("Security workflow file not found")
        
        with open(security_workflow) as f:
            content = f.read()
        
        # Check for required components
        required_components = [
            'gitleaks',  # GitLeaks integration
            'powershell',  # PowerShell scanning
            'secret-audit.ps1',  # Our custom script
            'GITHUB_STEP_SUMMARY'  # Summary generation
        ]
        
        for component in required_components:
            self.assertIn(component, content.lower(),
                         f"Missing required component: {component}")


if __name__ == '__main__':
    # Run integration tests
    unittest.main(verbosity=2)
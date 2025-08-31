"""
Test suite for StrataRegula security systems
Tests secret detection, pattern matching, and CI integration
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional


class TestSecretDetection(unittest.TestCase):
    """Test PowerShell-based secret detection system"""
    
    def setUp(self):
        """Set up test environment"""
        self.script_path = Path(__file__).parent.parent.parent / "secret-audit.ps1"
        self.test_dir = None
        
    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir and os.path.exists(self.test_dir):
            import shutil
            shutil.rmtree(self.test_dir)
    
    def create_test_directory(self, files: Dict[str, str]) -> str:
        """Create temporary directory with test files"""
        self.test_dir = tempfile.mkdtemp(prefix="strataregula_security_test_")
        
        for filename, content in files.items():
            file_path = os.path.join(self.test_dir, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return self.test_dir
    
    def run_powershell_scan(self, scan_path: str) -> tuple[int, str, str]:
        """Execute PowerShell security scan"""
        try:
            result = subprocess.run([
                'pwsh', '-File', str(self.script_path),
                '-ScanPath', scan_path
            ], capture_output=True, text=True, timeout=30)
            
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Scan timeout"
        except FileNotFoundError:
            return -1, "", "PowerShell not found"
    
    def test_github_token_detection(self):
        """Test GitHub token pattern detection"""
        test_files = {
            'config.py': '''
GITHUB_TOKEN = "ghp_1234567890123456789012345678901234567890"
API_KEY = "some_other_key"
''',
            'clean_file.py': '''
# This file should not trigger detection
EXAMPLE_VAR = "some_value"
'''
        }
        
        test_dir = self.create_test_directory(test_files)
        return_code, stdout, stderr = self.run_powershell_scan(test_dir)
        
        # Should detect secret (exit code 1)
        self.assertEqual(return_code, 1)
        self.assertIn("GitHub Personal Access Token", stdout)
        self.assertIn("ghp_", stdout)
    
    def test_aws_key_detection(self):
        """Test AWS credential detection"""
        test_files = {
            'aws_config.py': '''
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET = "some_secret_here"
''',
            'normal_file.py': '''
# Regular configuration
DATABASE_URL = "postgresql://localhost:5432/mydb"
'''
        }
        
        test_dir = self.create_test_directory(test_files)
        return_code, stdout, stderr = self.run_powershell_scan(test_dir)
        
        self.assertEqual(return_code, 1)
        self.assertIn("AWS Access Key ID", stdout)
        self.assertIn("AKIA", stdout)
    
    def test_openai_key_detection(self):
        """Test OpenAI API key detection"""
        test_files = {
            'ai_config.json': '''{
    "openai_api_key": "sk-1234567890123456789012345678901234567890123456789012345678"
}''',
            'readme.md': '''
# Project Documentation
This project uses AI services.
'''
        }
        
        test_dir = self.create_test_directory(test_files)
        return_code, stdout, stderr = self.run_powershell_scan(test_dir)
        
        self.assertEqual(return_code, 1)
        self.assertIn("OpenAI API Key", stdout)
        self.assertIn("sk-", stdout)
    
    def test_jwt_token_detection(self):
        """Test JWT token detection"""
        test_files = {
            'auth.py': '''
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
'''
        }
        
        test_dir = self.create_test_directory(test_files)
        return_code, stdout, stderr = self.run_powershell_scan(test_dir)
        
        self.assertEqual(return_code, 1)
        self.assertIn("JWT Token", stdout)
        self.assertIn("eyJ", stdout)
    
    def test_private_key_detection(self):
        """Test private key detection"""
        test_files = {
            'key.pem': '''-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890ABCDEF...
-----END RSA PRIVATE KEY-----'''
        }
        
        test_dir = self.create_test_directory(test_files)
        return_code, stdout, stderr = self.run_powershell_scan(test_dir)
        
        self.assertEqual(return_code, 1)
        self.assertIn("Private Key", stdout)
        self.assertIn("BEGIN", stdout)
    
    def test_clean_repository(self):
        """Test scanning clean repository (no secrets)"""
        test_files = {
            'main.py': '''
import os
from typing import Optional

def get_config_value(key: str) -> Optional[str]:
    return os.environ.get(key)

# This is a clean configuration
DATABASE_URL = get_config_value("DATABASE_URL")
''',
            'config.py': '''
# Environment-based configuration
DEBUG = True
LOG_LEVEL = "INFO"
''',
            'README.md': '''
# Project Documentation
This project follows security best practices.
'''
        }
        
        test_dir = self.create_test_directory(test_files)
        return_code, stdout, stderr = self.run_powershell_scan(test_dir)
        
        # Should be clean (exit code 0)
        self.assertEqual(return_code, 0)
        self.assertIn("No secrets detected", stdout)
    
    def test_exclusion_patterns(self):
        """Test that excluded directories are not scanned"""
        test_files = {
            '__pycache__/secret.pyc': 'ghp_1234567890123456789012345678901234567890',
            '.git/config': 'AKIAIOSFODNN7EXAMPLE',
            'node_modules/package/secret.js': 'sk-1234567890123456789012345678901234567890',
            'src/main.py': '''
# Clean source file
def main():
    print("Hello, World!")
'''
        }
        
        test_dir = self.create_test_directory(test_files)
        return_code, stdout, stderr = self.run_powershell_scan(test_dir)
        
        # Should be clean because excluded dirs contain secrets
        self.assertEqual(return_code, 0)
        self.assertIn("No secrets detected", stdout)
    
    def test_multiple_secrets_detection(self):
        """Test detection of multiple different secret types"""
        test_files = {
            'multi_secrets.py': '''
# Multiple secrets in one file
GITHUB_TOKEN = "ghp_1234567890123456789012345678901234567890"
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
OPENAI_KEY = "sk-1234567890123456789012345678901234567890123456789012345678"
JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature"
'''
        }
        
        test_dir = self.create_test_directory(test_files)
        return_code, stdout, stderr = self.run_powershell_scan(test_dir)
        
        self.assertEqual(return_code, 1)
        # Should detect all 4 types
        self.assertIn("GitHub Personal Access Token", stdout)
        self.assertIn("AWS Access Key ID", stdout)
        self.assertIn("OpenAI API Key", stdout)
        self.assertIn("JWT Token", stdout)


class TestGitLeaksIntegration(unittest.TestCase):
    """Test GitLeaks integration and configuration"""
    
    def setUp(self):
        """Set up GitLeaks test environment"""
        self.config_path = Path(__file__).parent.parent.parent / ".github" / "gitleaks.toml"
    
    def test_gitleaks_config_exists(self):
        """Test that GitLeaks configuration file exists"""
        self.assertTrue(self.config_path.exists(), 
                       f"GitLeaks config not found at {self.config_path}")
    
    def test_gitleaks_config_valid(self):
        """Test that GitLeaks configuration is valid TOML"""
        try:
            import tomli
            with open(self.config_path, 'rb') as f:
                config = tomli.load(f)
            
            # Check required sections
            self.assertIn('rules', config)
            self.assertIsInstance(config['rules'], list)
            self.assertGreater(len(config['rules']), 0)
            
            # Check rule structure
            for rule in config['rules']:
                self.assertIn('id', rule)
                self.assertIn('description', rule)
                self.assertIn('regex', rule)
                self.assertIn('tags', rule)
                
        except ImportError:
            self.skipTest("tomli not available for TOML parsing")
    
    def test_gitleaks_execution(self):
        """Test GitLeaks command execution (if available)"""
        try:
            result = subprocess.run([
                'gitleaks', 'detect', '--config', str(self.config_path),
                '--no-git', '--verbose'
            ], capture_output=True, text=True, timeout=30, cwd=Path(__file__).parent.parent.parent)
            
            # GitLeaks should execute successfully (exit code 0 or 1)
            self.assertIn(result.returncode, [0, 1])
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("GitLeaks not available for testing")


class TestSecurityWorkflow(unittest.TestCase):
    """Test GitHub Actions security workflow configuration"""
    
    def setUp(self):
        """Set up workflow test environment"""
        self.workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "security.yml"
        self.secret_audit_workflow = Path(__file__).parent.parent.parent / ".github" / "workflows" / "secret-audit.yml"
    
    def test_workflow_files_exist(self):
        """Test that workflow files exist"""
        self.assertTrue(self.workflow_path.exists(), 
                       f"Security workflow not found at {self.workflow_path}")
        self.assertTrue(self.secret_audit_workflow.exists(),
                      f"Secret audit workflow not found at {self.secret_audit_workflow}")
    
    def test_workflow_yaml_valid(self):
        """Test that workflow YAML is valid"""
        try:
            import yaml
            
            with open(self.workflow_path) as f:
                workflow = yaml.safe_load(f)
            
            # Check required workflow structure
            self.assertIn('name', workflow)
            self.assertIn('on', workflow)
            self.assertIn('jobs', workflow)
            
            # Check job structure
            jobs = workflow['jobs']
            self.assertIsInstance(jobs, dict)
            self.assertGreater(len(jobs), 0)
            
            for job_name, job_config in jobs.items():
                self.assertIn('runs-on', job_config)
                self.assertIn('steps', job_config)
                self.assertIsInstance(job_config['steps'], list)
                
        except ImportError:
            self.skipTest("PyYAML not available for YAML parsing")


class TestPreCommitConfiguration(unittest.TestCase):
    """Test pre-commit hooks configuration"""
    
    def setUp(self):
        """Set up pre-commit test environment"""
        self.precommit_config = Path(__file__).parent.parent.parent / ".pre-commit-config.yaml"
    
    def test_precommit_config_exists(self):
        """Test that pre-commit config exists"""
        self.assertTrue(self.precommit_config.exists(),
                       f"Pre-commit config not found at {self.precommit_config}")
    
    def test_precommit_config_valid(self):
        """Test that pre-commit config is valid YAML"""
        try:
            import yaml
            
            with open(self.precommit_config) as f:
                config = yaml.safe_load(f)
            
            # Check required structure
            self.assertIn('repos', config)
            self.assertIsInstance(config['repos'], list)
            self.assertGreater(len(config['repos']), 0)
            
            # Check for security-related hooks
            repo_hooks = []
            for repo in config['repos']:
                if 'hooks' in repo:
                    repo_hooks.extend([hook['id'] for hook in repo['hooks']])
            
            # Should include GitLeaks
            self.assertIn('gitleaks', repo_hooks)
            
        except ImportError:
            self.skipTest("PyYAML not available for YAML parsing")


class TestSecurityDocumentation(unittest.TestCase):
    """Test security documentation completeness"""
    
    def setUp(self):
        """Set up documentation test environment"""
        self.root_dir = Path(__file__).parent.parent.parent
        self.security_trail = self.root_dir / "SECURITY_AUDIT_TRAIL.md"
        self.deployment_guide = self.root_dir / "SECURITY_DEPLOYMENT_GUIDE.md"
    
    def test_security_documentation_exists(self):
        """Test that security documentation files exist"""
        self.assertTrue(self.security_trail.exists(),
                       f"Security audit trail not found at {self.security_trail}")
        self.assertTrue(self.deployment_guide.exists(),
                       f"Deployment guide not found at {self.deployment_guide}")
    
    def test_documentation_content(self):
        """Test that documentation contains required sections"""
        with open(self.security_trail) as f:
            audit_content = f.read()
        
        # Check required sections
        required_sections = [
            "# Security Audit Trail",
            "## 🎯 Audit Objective",
            "## 🔍 Security Scope",
            "## 🛡️ Security Controls",
            "## 📊 Risk Assessment"
        ]
        
        for section in required_sections:
            self.assertIn(section, audit_content,
                         f"Missing section: {section}")


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSecretDetection))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestGitLeaksIntegration))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSecurityWorkflow))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestPreCommitConfiguration))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSecurityDocumentation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
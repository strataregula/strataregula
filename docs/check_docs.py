#!/usr/bin/env python3
"""
Documentation quality checker for Strataregula.
Validates markdown files, checks for dead links, and ensures consistency.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set
from urllib.parse import urlparse
import json
import yaml


class DocChecker:
    def __init__(self, docs_dir: str = "docs"):
        self.docs_dir = Path(docs_dir)
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.stats = {
            'files_checked': 0,
            'links_checked': 0,
            'code_blocks_checked': 0,
            'issues_found': 0,
            'warnings_found': 0
        }

    def check_all(self) -> bool:
        """Check all documentation files."""
        print("🔍 Checking Strataregula documentation quality...")
        
        if not self.docs_dir.exists():
            self.issues.append(f"Documentation directory not found: {self.docs_dir}")
            return False
        
        # Check markdown files
        for md_file in self.docs_dir.rglob("*.md"):
            self.check_markdown_file(md_file)
        
        # Check for common documentation patterns
        self.check_documentation_structure()
        
        # Check external links
        self.check_external_links()
        
        # Print results
        self.print_results()
        
        return len(self.issues) == 0

    def check_markdown_file(self, file_path: Path):
        """Check individual markdown file."""
        self.stats['files_checked'] += 1
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            self.issues.append(f"Encoding error in {file_path}: Not UTF-8")
            return
        
        # Check for TODO/FIXME markers
        self.check_incomplete_content(file_path, content)
        
        # Check internal links
        self.check_internal_links(file_path, content)
        
        # Check code blocks
        self.check_code_blocks(file_path, content)
        
        # Check markdown formatting
        self.check_markdown_formatting(file_path, content)
        
        # Check for required sections
        self.check_required_sections(file_path, content)

    def check_incomplete_content(self, file_path: Path, content: str):
        """Check for incomplete content markers."""
        todo_patterns = [
            r'TODO\b',
            r'FIXME\b',
            r'XXX\b',
            r'HACK\b',
            r'BUG\b',
            r'\[TBD\]',
            r'\[TODO\]'
        ]
        
        for pattern in todo_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.warnings.append(
                    f"Incomplete content in {file_path}:{line_num} - {match.group()}"
                )

    def check_internal_links(self, file_path: Path, content: str):
        """Check internal markdown links."""
        # Find all markdown links
        link_pattern = r'\[([^\]]*)\]\(([^)]+)\)'
        links = re.findall(link_pattern, content)
        
        for link_text, link_url in links:
            self.stats['links_checked'] += 1
            
            # Skip external links
            if link_url.startswith(('http://', 'https://', 'mailto:', 'tel:')):
                continue
            
            # Skip anchors within same page
            if link_url.startswith('#'):
                self.check_anchor_exists(file_path, content, link_url[1:])
                continue
            
            # Check internal file links
            self.check_internal_file_link(file_path, link_url)

    def check_anchor_exists(self, file_path: Path, content: str, anchor: str):
        """Check if anchor exists in current file."""
        # Convert anchor to potential heading patterns
        heading_patterns = [
            f"# {anchor.replace('-', ' ')}",
            f"## {anchor.replace('-', ' ')}",
            f"### {anchor.replace('-', ' ')}",
            f"#### {anchor.replace('-', ' ')}"
        ]
        
        # Also check for HTML id attributes
        html_id_pattern = f'id="{anchor}"'
        
        found = any(pattern.lower() in content.lower() for pattern in heading_patterns)
        found = found or html_id_pattern in content
        
        if not found:
            self.warnings.append(
                f"Anchor not found in {file_path}: #{anchor}"
            )

    def check_internal_file_link(self, file_path: Path, link_url: str):
        """Check if internal file link exists."""
        # Remove anchor part
        file_part = link_url.split('#')[0]
        if not file_part:
            return
        
        # Resolve relative to current file
        current_dir = file_path.parent
        target_path = current_dir / file_part
        
        # Try to resolve the path
        try:
            target_path = target_path.resolve()
            if not target_path.exists():
                self.issues.append(
                    f"Dead link in {file_path}: {link_url} -> {target_path}"
                )
        except (OSError, ValueError):
            self.issues.append(
                f"Invalid link path in {file_path}: {link_url}"
            )

    def check_code_blocks(self, file_path: Path, content: str):
        """Check code blocks for syntax errors."""
        # Find Python code blocks
        python_pattern = r'```python\n(.*?)\n```'
        python_blocks = re.findall(python_pattern, content, re.DOTALL)
        
        for i, code in enumerate(python_blocks):
            self.stats['code_blocks_checked'] += 1
            try:
                compile(code, f'<{file_path}:block{i}>', 'exec')
            except SyntaxError as e:
                self.issues.append(
                    f"Python syntax error in {file_path} block {i}: {e}"
                )
        
        # Check YAML blocks
        yaml_pattern = r'```ya?ml\n(.*?)\n```'
        yaml_blocks = re.findall(yaml_pattern, content, re.DOTALL)
        
        for i, yaml_content in enumerate(yaml_blocks):
            try:
                yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                self.issues.append(
                    f"YAML syntax error in {file_path} block {i}: {e}"
                )
        
        # Check JSON blocks
        json_pattern = r'```json\n(.*?)\n```'
        json_blocks = re.findall(json_pattern, content, re.DOTALL)
        
        for i, json_content in enumerate(json_blocks):
            try:
                json.loads(json_content)
            except json.JSONDecodeError as e:
                self.issues.append(
                    f"JSON syntax error in {file_path} block {i}: {e}"
                )

    def check_markdown_formatting(self, file_path: Path, content: str):
        """Check markdown formatting consistency."""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Check for trailing whitespace
            if line.rstrip() != line:
                self.warnings.append(
                    f"Trailing whitespace in {file_path}:{line_num}"
                )
            
            # Check heading format
            if line.startswith('#'):
                # Should have space after #
                if not re.match(r'^#+\s', line) and len(line.strip()) > 1:
                    self.warnings.append(
                        f"Heading format issue in {file_path}:{line_num}: {line[:50]}"
                    )

    def check_required_sections(self, file_path: Path, content: str):
        """Check for required sections in documentation."""
        # Skip check for certain files
        skip_files = {'index.md', 'README.md'}
        if file_path.name in skip_files:
            return
        
        # Check for common required sections based on file type
        if 'getting-started' in str(file_path):
            required = ['installation', 'usage', 'example']
            self.check_has_sections(file_path, content, required)
        
        elif 'api' in str(file_path):
            required = ['parameters', 'returns', 'example']
            self.check_has_sections(file_path, content, required)
        
        elif 'tutorial' in str(file_path):
            required = ['prerequisites', 'steps', 'example']
            self.check_has_sections(file_path, content, required)

    def check_has_sections(self, file_path: Path, content: str, required_sections: List[str]):
        """Check if content has required sections."""
        content_lower = content.lower()
        
        for section in required_sections:
            if section not in content_lower:
                self.warnings.append(
                    f"Missing recommended section in {file_path}: {section}"
                )

    def check_documentation_structure(self):
        """Check overall documentation structure."""
        expected_files = [
            'index.md',
            'getting-started/installation.md',
            'api/index.md',
            'plugins/doe-runner.md',
            'examples/getting-started.md'
        ]
        
        for expected in expected_files:
            expected_path = self.docs_dir / expected
            if not expected_path.exists():
                self.warnings.append(f"Missing recommended file: {expected}")

    def check_external_links(self):
        """Check external links (basic validation)."""
        # This could be extended to actually check HTTP status
        # For now, just validate URL format
        
        for md_file in self.docs_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', content)
                
                for link_text, link_url in links:
                    if link_url.startswith(('http://', 'https://')):
                        parsed = urlparse(link_url)
                        if not parsed.netloc:
                            self.issues.append(
                                f"Invalid URL in {md_file}: {link_url}"
                            )
            except Exception:
                continue

    def print_results(self):
        """Print check results."""
        self.stats['issues_found'] = len(self.issues)
        self.stats['warnings_found'] = len(self.warnings)
        
        print(f"\n📊 Documentation Check Results")
        print("=" * 40)
        print(f"Files checked: {self.stats['files_checked']}")
        print(f"Links checked: {self.stats['links_checked']}")
        print(f"Code blocks checked: {self.stats['code_blocks_checked']}")
        print(f"Issues found: {self.stats['issues_found']}")
        print(f"Warnings: {self.stats['warnings_found']}")
        
        if self.issues:
            print(f"\n❌ Issues Found ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  - {issue}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.issues and not self.warnings:
            print("\n✅ Documentation is clean!")
        elif not self.issues:
            print(f"\n✅ No critical issues found (only {len(self.warnings)} warnings)")
        else:
            print(f"\n❌ Found {len(self.issues)} issues that need attention")


def main():
    """Main entry point."""
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "docs"
    
    checker = DocChecker(docs_dir)
    success = checker.check_all()
    
    # Exit with appropriate code
    if not success:
        sys.exit(1)
    elif checker.warnings:
        sys.exit(0)  # Warnings don't fail the check
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
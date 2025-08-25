"""
SuperClaude Core - Main orchestrator for development assistance
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import subprocess
import ast
import re

from .analyzer import ProjectAnalyzer
from .generator import CodeGenerator
from .assistant import DevelopmentAssistant
from .reporter import ReportGenerator


@dataclass
class ProjectContext:
    """Project context and metadata."""
    project_root: Path
    project_name: str = "strataregula"
    version: str = "0.1.1"
    main_language: str = "python"
    test_framework: str = "pytest"
    doc_system: str = "mkdocs"
    ci_system: str = "github_actions"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_root": str(self.project_root),
            "project_name": self.project_name,
            "version": self.version,
            "main_language": self.main_language,
            "test_framework": self.test_framework,
            "doc_system": self.doc_system,
            "ci_system": self.ci_system
        }


class SuperClaude:
    """
    SuperClaude - The intelligent development assistant for Strataregula.
    
    Provides comprehensive project analysis, code generation, documentation
    management, and development workflow automation.
    """
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize SuperClaude with project context."""
        self.project_root = Path(project_root or os.getcwd())
        self.context = self._load_project_context()
        
        # Initialize components
        self.analyzer = ProjectAnalyzer(self.project_root)
        self.generator = CodeGenerator(self.context)
        self.assistant = DevelopmentAssistant(self.context)
        self.reporter = ReportGenerator(self.context)
        
        # Load configuration
        self.config = self._load_config()
        
        print(f"🤖 SuperClaude initialized for {self.context.project_name} v{self.context.version}")
    
    def _load_project_context(self) -> ProjectContext:
        """Load project context from configuration files."""
        context = ProjectContext(project_root=self.project_root)
        
        # Try to load from pyproject.toml
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists():
            try:
                import toml
                data = toml.load(pyproject_path)
                if "project" in data:
                    context.project_name = data["project"].get("name", context.project_name)
                    context.version = data["project"].get("version", context.version)
            except ImportError:
                # Fall back to basic parsing
                content = pyproject_path.read_text()
                if match := re.search(r'name = "([^"]+)"', content):
                    context.project_name = match.group(1)
                if match := re.search(r'version = "([^"]+)"', content):
                    context.version = match.group(1)
        
        return context
    
    def _load_config(self) -> Dict[str, Any]:
        """Load SuperClaude configuration."""
        config_path = self.project_root / ".superclaude.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Default configuration
        return {
            "analysis": {
                "enabled": True,
                "complexity_threshold": 10,
                "coverage_threshold": 80,
                "lint_on_save": True
            },
            "generation": {
                "templates_dir": "templates",
                "output_dir": "generated",
                "auto_format": True
            },
            "documentation": {
                "auto_update": True,
                "check_links": True,
                "generate_api_docs": True
            },
            "assistance": {
                "suggestions": True,
                "auto_fix": False,
                "explain_errors": True
            }
        }
    
    def analyze_project(self) -> Dict[str, Any]:
        """
        Perform comprehensive project analysis.
        
        Returns:
            Analysis report with metrics, issues, and suggestions
        """
        print("🔍 Analyzing Strataregula project...")
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "project": self.context.to_dict(),
            "code_analysis": self.analyzer.analyze_code(),
            "test_coverage": self.analyzer.analyze_test_coverage(),
            "documentation": self.analyzer.analyze_documentation(),
            "dependencies": self.analyzer.analyze_dependencies(),
            "security": self.analyzer.security_scan(),
            "performance": self.analyzer.performance_analysis()
        }
        
        # Generate insights
        analysis["insights"] = self._generate_insights(analysis)
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    def generate_code(self, 
                     template: str,
                     context: Dict[str, Any],
                     output_path: Optional[str] = None) -> str:
        """
        Generate code from templates.
        
        Args:
            template: Template name or path
            context: Context variables for template
            output_path: Optional output file path
            
        Returns:
            Generated code as string
        """
        print(f"🔨 Generating code from template: {template}")
        
        code = self.generator.generate(template, context)
        
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(code)
            print(f"✅ Generated code saved to: {output_path}")
        
        return code
    
    def assist_development(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Provide development assistance for various tasks.
        
        Args:
            task: Task type (debug, optimize, refactor, test, document)
            **kwargs: Task-specific parameters
            
        Returns:
            Assistance result with suggestions and actions
        """
        print(f"🎯 Assisting with: {task}")
        
        task_handlers = {
            "debug": self.assistant.debug_issue,
            "optimize": self.assistant.optimize_code,
            "refactor": self.assistant.refactor_code,
            "test": self.assistant.generate_tests,
            "document": self.assistant.generate_documentation,
            "review": self.assistant.code_review,
            "fix": self.assistant.auto_fix_issues
        }
        
        if task not in task_handlers:
            return {
                "status": "error",
                "message": f"Unknown task: {task}",
                "available_tasks": list(task_handlers.keys())
            }
        
        return task_handlers[task](**kwargs)
    
    def create_plugin(self, plugin_name: str, plugin_type: str = "standard") -> Dict[str, Any]:
        """
        Create a new Strataregula plugin with boilerplate.
        
        Args:
            plugin_name: Name of the plugin
            plugin_type: Type of plugin (standard, doe, analysis, etc.)
            
        Returns:
            Creation result with file paths
        """
        print(f"🔌 Creating new plugin: {plugin_name}")
        
        plugin_data = {
            "name": plugin_name,
            "type": plugin_type,
            "package_name": f"strataregula_{plugin_name.replace('-', '_')}",
            "class_name": ''.join(word.capitalize() for word in plugin_name.split('-')) + "Plugin"
        }
        
        # Generate plugin structure
        created_files = self.generator.create_plugin_structure(plugin_data)
        
        return {
            "status": "success",
            "plugin": plugin_data,
            "created_files": created_files,
            "next_steps": [
                f"1. cd strataregula-{plugin_name}",
                "2. pip install -e .",
                "3. Implement plugin logic in src/*/plugin.py",
                "4. Add tests in tests/",
                "5. Update README.md with usage examples"
            ]
        }
    
    def optimize_performance(self, target: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze and optimize performance bottlenecks.
        
        Args:
            target: Specific module or function to optimize
            
        Returns:
            Optimization report with suggestions
        """
        print("⚡ Analyzing performance...")
        
        # Run performance profiling
        profile_data = self.analyzer.profile_performance(target)
        
        # Generate optimization suggestions
        optimizations = self.assistant.suggest_optimizations(profile_data)
        
        return {
            "profile": profile_data,
            "optimizations": optimizations,
            "estimated_improvement": self._estimate_improvement(optimizations)
        }
    
    def update_documentation(self, scope: str = "all") -> Dict[str, Any]:
        """
        Update project documentation.
        
        Args:
            scope: Documentation scope (all, api, guides, examples)
            
        Returns:
            Update result with modified files
        """
        print(f"📚 Updating documentation (scope: {scope})")
        
        updated_files = []
        
        if scope in ["all", "api"]:
            # Update API documentation
            api_files = self.generator.update_api_docs()
            updated_files.extend(api_files)
        
        if scope in ["all", "guides"]:
            # Update user guides
            guide_files = self.generator.update_guides()
            updated_files.extend(guide_files)
        
        if scope in ["all", "examples"]:
            # Update examples
            example_files = self.generator.update_examples()
            updated_files.extend(example_files)
        
        # Check documentation quality
        doc_issues = self.analyzer.check_documentation_quality()
        
        return {
            "status": "success",
            "updated_files": updated_files,
            "documentation_issues": doc_issues,
            "coverage": self.analyzer.get_documentation_coverage()
        }
    
    def run_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """
        Run predefined development workflow.
        
        Args:
            workflow_name: Name of workflow to run
            
        Returns:
            Workflow execution result
        """
        print(f"🔄 Running workflow: {workflow_name}")
        
        workflows = {
            "pre-commit": self._run_pre_commit_workflow,
            "release": self._run_release_workflow,
            "test": self._run_test_workflow,
            "deploy": self._run_deploy_workflow,
            "quality": self._run_quality_workflow
        }
        
        if workflow_name not in workflows:
            return {
                "status": "error",
                "message": f"Unknown workflow: {workflow_name}",
                "available_workflows": list(workflows.keys())
            }
        
        return workflows[workflow_name]()
    
    def generate_report(self, report_type: str = "summary") -> str:
        """
        Generate project status report.
        
        Args:
            report_type: Type of report (summary, detailed, metrics)
            
        Returns:
            Formatted report as string
        """
        print(f"📊 Generating {report_type} report...")
        
        # Gather data
        analysis = self.analyze_project()
        
        # Generate report
        if report_type == "summary":
            return self.reporter.generate_summary_report(analysis)
        elif report_type == "detailed":
            return self.reporter.generate_detailed_report(analysis)
        elif report_type == "metrics":
            return self.reporter.generate_metrics_report(analysis)
        else:
            return self.reporter.generate_custom_report(analysis, report_type)
    
    def interactive_mode(self):
        """
        Start interactive SuperClaude session.
        """
        print("🤖 SuperClaude Interactive Mode")
        print("=" * 50)
        print("Available commands:")
        print("  analyze     - Analyze project")
        print("  generate    - Generate code")
        print("  assist      - Get development assistance")
        print("  optimize    - Optimize performance")
        print("  document    - Update documentation")
        print("  workflow    - Run workflow")
        print("  report      - Generate report")
        print("  help        - Show help")
        print("  exit        - Exit interactive mode")
        print("=" * 50)
        
        while True:
            try:
                command = input("\n🤖 SuperClaude> ").strip().lower()
                
                if command == "exit":
                    print("👋 Goodbye!")
                    break
                elif command == "help":
                    self._show_help()
                elif command == "analyze":
                    result = self.analyze_project()
                    print(json.dumps(result, indent=2))
                elif command.startswith("generate"):
                    self._interactive_generate()
                elif command.startswith("assist"):
                    self._interactive_assist()
                elif command == "optimize":
                    result = self.optimize_performance()
                    print(json.dumps(result, indent=2))
                elif command == "document":
                    result = self.update_documentation()
                    print(json.dumps(result, indent=2))
                elif command.startswith("workflow"):
                    parts = command.split()
                    if len(parts) > 1:
                        result = self.run_workflow(parts[1])
                        print(json.dumps(result, indent=2))
                    else:
                        print("Usage: workflow <name>")
                elif command == "report":
                    report = self.generate_report()
                    print(report)
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    # Private helper methods
    
    def _generate_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate insights from analysis data."""
        insights = []
        
        # Code quality insights
        if "code_analysis" in analysis:
            code = analysis["code_analysis"]
            if code.get("complexity_average", 0) > 10:
                insights.append("⚠️ High code complexity detected in some modules")
            if code.get("duplicate_code_percentage", 0) > 5:
                insights.append("📋 Significant code duplication found")
        
        # Test coverage insights
        if "test_coverage" in analysis:
            coverage = analysis["test_coverage"]
            if coverage.get("overall", 0) < 80:
                insights.append("🧪 Test coverage below recommended 80%")
        
        # Documentation insights
        if "documentation" in analysis:
            docs = analysis["documentation"]
            if docs.get("undocumented_functions", 0) > 10:
                insights.append("📚 Many functions lack documentation")
        
        # Security insights
        if "security" in analysis:
            security = analysis["security"]
            if security.get("vulnerabilities", []):
                insights.append("🔒 Security vulnerabilities detected")
        
        return insights
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Based on insights
        insights = analysis.get("insights", [])
        
        if "High code complexity" in str(insights):
            recommendations.append({
                "priority": "high",
                "category": "code_quality",
                "action": "Refactor complex functions",
                "command": "superclaude assist refactor --complexity-threshold 10"
            })
        
        if "Test coverage below" in str(insights):
            recommendations.append({
                "priority": "high",
                "category": "testing",
                "action": "Increase test coverage",
                "command": "superclaude assist test --generate-missing"
            })
        
        if "functions lack documentation" in str(insights):
            recommendations.append({
                "priority": "medium",
                "category": "documentation",
                "action": "Add missing documentation",
                "command": "superclaude document --scope api"
            })
        
        if "Security vulnerabilities" in str(insights):
            recommendations.append({
                "priority": "critical",
                "category": "security",
                "action": "Fix security vulnerabilities",
                "command": "superclaude assist fix --security"
            })
        
        return recommendations
    
    def _estimate_improvement(self, optimizations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate performance improvement from optimizations."""
        total_time_saved = 0
        total_memory_saved = 0
        
        for opt in optimizations:
            total_time_saved += opt.get("estimated_time_improvement", 0)
            total_memory_saved += opt.get("estimated_memory_improvement", 0)
        
        return {
            "time_improvement_percent": total_time_saved,
            "memory_improvement_percent": total_memory_saved,
            "overall_improvement": (total_time_saved + total_memory_saved) / 2
        }
    
    def _run_pre_commit_workflow(self) -> Dict[str, Any]:
        """Run pre-commit workflow."""
        steps = [
            ("Linting", "ruff check ."),
            ("Type checking", "mypy ."),
            ("Tests", "pytest"),
            ("Documentation check", "python docs/check_docs.py")
        ]
        
        results = []
        for step_name, command in steps:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            results.append({
                "step": step_name,
                "command": command,
                "success": result.returncode == 0,
                "output": result.stdout if result.returncode == 0 else result.stderr
            })
        
        return {
            "workflow": "pre-commit",
            "status": "success" if all(r["success"] for r in results) else "failed",
            "results": results
        }
    
    def _run_release_workflow(self) -> Dict[str, Any]:
        """Run release workflow."""
        return {
            "workflow": "release",
            "status": "not_implemented",
            "message": "Release workflow coming soon"
        }
    
    def _run_test_workflow(self) -> Dict[str, Any]:
        """Run test workflow."""
        result = subprocess.run("pytest -v", shell=True, capture_output=True, text=True)
        return {
            "workflow": "test",
            "status": "success" if result.returncode == 0 else "failed",
            "output": result.stdout,
            "errors": result.stderr if result.returncode != 0 else None
        }
    
    def _run_deploy_workflow(self) -> Dict[str, Any]:
        """Run deployment workflow."""
        return {
            "workflow": "deploy",
            "status": "not_implemented",
            "message": "Deploy workflow coming soon"
        }
    
    def _run_quality_workflow(self) -> Dict[str, Any]:
        """Run code quality workflow."""
        analysis = self.analyze_project()
        return {
            "workflow": "quality",
            "status": "success",
            "analysis": analysis,
            "recommendations": analysis.get("recommendations", [])
        }
    
    def _show_help(self):
        """Show interactive mode help."""
        print("""
SuperClaude Commands:
=====================
analyze              - Perform comprehensive project analysis
generate <template>  - Generate code from template
assist <task>        - Get assistance (debug, optimize, refactor, test, document)
optimize [target]    - Optimize performance
document [scope]     - Update documentation (all, api, guides, examples)
workflow <name>      - Run workflow (pre-commit, release, test, deploy, quality)
report [type]        - Generate report (summary, detailed, metrics)
help                 - Show this help message
exit                 - Exit interactive mode
        """)
    
    def _interactive_generate(self):
        """Interactive code generation."""
        print("Available templates:")
        print("  plugin     - Strataregula plugin")
        print("  test       - Test file")
        print("  command    - CLI command")
        print("  component  - Component class")
        
        template = input("Template name: ").strip()
        if template == "plugin":
            name = input("Plugin name: ").strip()
            self.create_plugin(name)
        else:
            print(f"Template '{template}' not implemented yet")
    
    def _interactive_assist(self):
        """Interactive development assistance."""
        print("Available assistance tasks:")
        print("  debug      - Debug issue")
        print("  optimize   - Optimize code")
        print("  refactor   - Refactor code")
        print("  test       - Generate tests")
        print("  document   - Generate documentation")
        print("  review     - Code review")
        print("  fix        - Auto-fix issues")
        
        task = input("Task: ").strip()
        if task:
            result = self.assist_development(task)
            print(json.dumps(result, indent=2))
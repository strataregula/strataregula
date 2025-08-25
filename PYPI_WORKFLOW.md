# PyPI Publication Workflow for Strataregula

## Overview
This document provides a comprehensive guide for publishing the Strataregula package to PyPI, including setup, testing, and automation workflows.

## Prerequisites

### 1. PyPI Account Setup
```bash
# Create accounts at:
# - PyPI: https://pypi.org/account/register/
# - TestPyPI: https://test.pypi.org/account/register/

# Generate API tokens at:
# - PyPI: https://pypi.org/manage/account/token/
# - TestPyPI: https://test.pypi.org/manage/account/token/
```

### 2. Install Required Tools
```bash
pip install --upgrade pip
pip install --upgrade build twine keyring
```

### 3. Configure PyPI Credentials
```bash
# Store API tokens securely
python -m keyring set https://upload.pypi.org/legacy/ __token__
python -m keyring set https://test.pypi.org/legacy/ __token__

# Or create ~/.pypirc
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-api-token-here
```

## Version Management Strategy

### Current Setup
- **Single Source of Truth**: `strataregula/__init__.py`
- **Dynamic Versioning**: pyproject.toml reads from `__version__`
- **Version Format**: Semantic Versioning (MAJOR.MINOR.PATCH)

### Version Update Process
```bash
# 1. Update version in strataregula/__init__.py
__version__ = "0.2.0"

# 2. Verify consistency
python -c "import strataregula; print(strataregula.__version__)"

# 3. Update CLI version if needed
# Edit strataregula/cli/main.py
@click.version_option(version="0.2.0", prog_name="strataregula")
```

## Publication Process

### 1. Pre-Publication Checks
```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Run tests
python -m pytest tests/ -v

# Build package
python -m build

# Verify package contents
tar -tzf dist/strataregula-*.tar.gz
unzip -l dist/strataregula-*-py3-none-any.whl

# Check package metadata
python -m twine check dist/*
```

### 2. Test Publication (TestPyPI)
```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ strataregula

# Verify installation
python -c "import strataregula; print(strataregula.__version__)"
strataregula --version
```

### 3. Production Publication (PyPI)
```bash
# Upload to PyPI
python -m twine upload dist/*

# Verify publication
pip install strataregula
python -c "import strataregula; print(strataregula.__version__)"
```

## GitHub Actions Workflow

### Automated Release Pipeline
Create `.github/workflows/release.yml`:

```yaml
name: Build and Publish to PyPI

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install build dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Check package
      run: python -m twine check dist/*
    
    - name: Publish to Test PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.TEST_PYPI_API_TOKEN }}
      run: |
        python -m twine upload --repository testpypi dist/*
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: |
        python -m twine upload dist/*
```

### GitHub Secrets Setup
```bash
# Add these secrets to GitHub repository settings:
# Settings -> Secrets and variables -> Actions

TEST_PYPI_API_TOKEN=pypi-your-test-token-here
PYPI_API_TOKEN=pypi-your-production-token-here
```

## Release Process

### 1. Prepare Release
```bash
# Update version
vim strataregula/__init__.py
vim strataregula/cli/main.py

# Update CHANGELOG.md
vim CHANGELOG.md

# Commit changes
git add .
git commit -m "Bump version to 0.2.0"
```

### 2. Create Release Tag
```bash
# Create and push tag
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0

# This triggers GitHub Actions workflow
```

### 3. Manual Release (if needed)
```bash
# Clean and build
rm -rf dist/
python -m build

# Test upload
python -m twine upload --repository testpypi dist/*

# Production upload
python -m twine upload dist/*
```

## Quality Assurance

### Pre-Release Checklist
- [ ] All tests pass (`pytest`)
- [ ] Version updated in `__init__.py` and `cli/main.py`
- [ ] CHANGELOG.md updated
- [ ] Package builds successfully (`python -m build`)
- [ ] Package metadata valid (`twine check dist/*`)
- [ ] Test installation from TestPyPI works
- [ ] Documentation updated

### Post-Release Verification
- [ ] Package available on PyPI
- [ ] Installation works: `pip install strataregula`
- [ ] CLI commands work: `strataregula --version`
- [ ] Import works: `import strataregula`
- [ ] GitHub release created
- [ ] Documentation updated

## Package Metadata Summary

- **Name**: strataregula
- **Description**: Layered Configuration Management with Strata Rules Architecture
- **Author**: Strataregula Team
- **Email**: team@strataregula.com
- **License**: Apache-2.0
- **Python Version**: >=3.8
- **Repository**: https://github.com/strataregula/strataregula
- **Homepage**: https://github.com/strataregula/strataregula

## Support and Maintenance

### Version Lifecycle
- **Patch releases (0.1.x)**: Bug fixes, security updates
- **Minor releases (0.x.0)**: New features, backwards compatible
- **Major releases (x.0.0)**: Breaking changes, major rewrites

### Update Schedule
- Security patches: As needed
- Bug fixes: Monthly
- Feature releases: Quarterly
- Major releases: Annually

## Troubleshooting

### Common Issues
1. **Upload failed**: Check API token validity and permissions
2. **Package rejected**: Run `twine check dist/*` for validation errors
3. **Import errors**: Verify package structure and dependencies
4. **Version conflicts**: Ensure version consistency across files

### Debug Commands
```bash
# Check package structure
python -m pip show strataregula

# List package contents
python -c "import strataregula; print(dir(strataregula))"

# Verify entry points
python -m strataregula.cli.main --help
```

## Conclusion

This workflow ensures reliable, automated PyPI publication for the Strataregula package with proper version management, quality assurance, and GitHub Actions integration.
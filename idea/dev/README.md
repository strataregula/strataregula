# Development Files Directory

This directory contains temporary development, testing, and validation files that are not part of the public release.

## Contents

### Development Scripts
- `quickstart_test.py` - Validates README examples work correctly
- `test_doc_examples.py` - Tests documentation examples for accuracy
- `test_performance.py` - Performance validation with large datasets
- `security_review.py` - Security vulnerability checks
- `generate_uml_diagrams.py` - UML diagram generation script

### Test Data Files
- `demo.yaml` - Sample configuration for demonstrations
- `test_config_dump.yaml` - Test data for config dump features
- `test_intellisense_demo.yaml` - IntelliSense testing data
- `test_tree_complex.yaml` - Complex tree structure test data

### Generated Artifacts
- `coverage.json` - Test coverage data
- `dump.json` - Configuration dump samples
- `.coverage` - Python coverage database

## Purpose

These files are kept for:
1. **Quality assurance** - Validating documentation examples
2. **Performance testing** - Ensuring system scales properly
3. **Security validation** - Regular security reviews
4. **Development iteration** - Quick testing during development

## Not for Release

These files are excluded from public releases via `.gitignore` patterns:
- `*_test.py`
- `*_review.py`
- `quickstart*.py`
- `generate_*.py`
- `demo_*.py`
- `sample_*.py`
- `test_*.yaml`
- Coverage and dump files

## Usage

Run development scripts from the repository root:

```bash
# Validate README examples
python idea/dev/quickstart_test.py

# Test documentation accuracy
python idea/dev/test_doc_examples.py

# Performance validation
python idea/dev/test_performance.py

# Security review
python idea/dev/security_review.py
```

These scripts help maintain quality while keeping the main repository clean for users.
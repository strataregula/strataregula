# First Strataregula Project

This guide walks you through creating your first Strataregula project from scratch.

## Prerequisites

Before starting, ensure you have:
- Python 3.8 or higher
- Strataregula installed (`pip install strataregula`)
- Basic understanding of YAML

## Step 1: Project Setup

Create a new project directory:
```bash
mkdir my-strataregula-project
cd my-strataregula-project

# Create directory structure
mkdir -p config/environments
mkdir -p output
mkdir -p validation
```

## Step 2: Base Configuration

Create `config/base.yaml`:
```yaml
# Base configuration template
services:
  api.*:
    port: 8080
    protocol: "https"
    health_check: "/api/v1/health"
    
  web.*:
    port: 3000
    protocol: "https"
    health_check: "/health"
    
  cache.*:
    port: 6379
    protocol: "redis"
    
  monitor.*:
    port: 9090
    protocol: "http"

regions:
  tokyo: { zone: "ap-northeast-1a" }
  osaka: { zone: "ap-northeast-1b" }
  kyoto: { zone: "ap-northeast-1c" }
```

## Step 3: Environment-Specific Configuration

### Development Environment

Create `config/environments/development.yaml`:
```yaml
# Development environment
extends: "../base.yaml"

environment: development

services:
  api.dev.*:
    replicas: 1
    resources:
      memory: "512Mi"
      cpu: "250m"
  
  web.dev.*:
    replicas: 1
    resources:
      memory: "256Mi" 
      cpu: "100m"
      
  cache.dev.*:
    replicas: 1
    
  monitor.dev.*:
    replicas: 1
```

### Production Environment

Create `config/environments/production.yaml`:
```yaml
# Production environment
extends: "../base.yaml"

environment: production

services:
  api.prod.*:
    replicas: 3
    resources:
      memory: "1Gi"
      cpu: "500m"
  
  web.prod.*:
    replicas: 2
    resources:
      memory: "512Mi"
      cpu: "250m"
      
  cache.prod.*:
    replicas: 2
    
  monitor.prod.*:
    replicas: 1
```

## Step 4: Compile Configuration

Test the basic compilation:
```bash
# Compile development environment
strataregula compile config/environments/development.yaml

# Save to file in Python format
strataregula compile config/environments/development.yaml \
    --output output/development.py \
    --format python
    
# Save to JSON format
strataregula compile config/environments/development.yaml \
    --output output/development.json \
    --format json
```

## Step 5: Verify Output

Check the generated Python configuration:
```bash
# View generated services
python -c "
from output.development import services
print(f'Generated {len(services)} services:')
for name in sorted(services.keys())[:5]:  # Show first 5
    print(f'  - {name}')
"
```

Expected output:
```
Generated 12 services:
  - api.dev.tokyo.service
  - api.dev.osaka.service  
  - api.dev.kyoto.service
  - web.dev.tokyo.frontend
  - web.dev.osaka.frontend
```

## Step 6: Validation Script

Create `validation/validate_config.py`:
```python
#!/usr/bin/env python3
"""Validate generated configuration."""

import sys
import importlib.util

def validate_config(config_file):
    """Validate configuration structure."""
    
    # Load generated config
    spec = importlib.util.spec_from_file_location("config", config_file)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    
    services = getattr(config, 'services', {})
    
    print(f"📊 Configuration Validation")
    print(f"=" * 30)
    print(f"Total services: {len(services)}")
    
    # Check service categories
    categories = {}
    for service_name in services:
        category = service_name.split('.')[0]
        categories[category] = categories.get(category, 0) + 1
    
    print(f"Service categories:")
    for category, count in categories.items():
        print(f"  - {category}: {count} instances")
    
    # Validate required fields
    missing_fields = []
    for name, service in services.items():
        required = ['port', 'protocol']
        for field in required:
            if field not in service:
                missing_fields.append(f"{name}: missing {field}")
    
    if missing_fields:
        print(f"\n❌ Validation errors:")
        for error in missing_fields[:5]:  # Show first 5
            print(f"  - {error}")
        return False
    
    print(f"\n✅ Validation passed")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_config.py <config_file>")
        sys.exit(1)
    
    success = validate_config(sys.argv[1])
    sys.exit(0 if success else 1)
```

## Step 7: Build Script

Create `build.sh`:
```bash
#!/bin/bash
# Build script for Strataregula project

set -e

echo "🏗️  Building Strataregula project..."

# Clean output directory
rm -rf output/*

# Compile configurations
echo "📄 Compiling configurations..."

for env in development production; do
    echo "  Processing $env environment..."
    
    # Generate Python format
    strataregula compile config/environments/$env.yaml \
        --output output/$env.py \
        --format python
    
    # Generate JSON format
    strataregula compile config/environments/$env.yaml \
        --output output/$env.json \
        --format json
    
    # Validate configuration
    echo "  Validating $env configuration..."
    python validation/validate_config.py output/$env.py
done

echo "✅ Build completed successfully!"
```

Make it executable and run:
```bash
chmod +x build.sh
./build.sh
```

## Step 8: Advanced Patterns

### Complex Service Names

Create `config/advanced.yaml`:
```yaml
# Advanced pattern examples
services:
  # Multi-level wildcards
  "service-*-*-*":
    type: "microservice"
    
  # Specific pattern matching
  "api-v[12]-*":
    version_aware: true
    
  # Environment-specific patterns
  "*.{dev,staging,prod}.*":
    environment_specific: true
```

### Hierarchical Expansion

```yaml
# Regional hierarchy
regions:
  kanto:
    prefectures: ["tokyo", "kanagawa", "saitama", "chiba"]
  kansai:
    prefectures: ["osaka", "kyoto", "hyogo", "nara"]

services:
  "api.*.*":
    # Expands to all region/prefecture combinations
    deployment: "regional"
```

## Next Steps

Congratulations! You've created your first Strataregula project. Here's what you've accomplished:

- ✅ Set up a structured project layout
- ✅ Created base and environment-specific configurations
- ✅ Generated configurations in multiple formats
- ✅ Implemented validation scripts
- ✅ Created build automation

### Continue Learning

1. **[Pattern Syntax](../user-guide/patterns.md)** - Learn advanced pattern matching
2. **[CLI Reference](../user-guide/cli.md)** - Complete command documentation
3. **[Examples](../examples/examples.md)** - More practical examples
4. **[Best Practices](../user-guide/best-practices.md)** - Production recommendations

### Community Resources

- **Documentation**: Complete guides and references
- **Examples**: Real-world configuration templates
- **Issues**: [Report problems or suggestions](https://github.com/strataregula/strataregula/issues)
- **Discussions**: [Community Q&A](https://github.com/strataregula/strataregula/discussions)

Happy configuring! 🚀
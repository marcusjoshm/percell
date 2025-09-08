# Comprehensive Analysis Guide for Percell Ports & Adapters Architecture

## 1. Architecture Analysis Methods

### 1.1 Static Code Analysis Tools

#### **Python-Specific Tools**

**1. PyReverse (Part of Pylint)**
```bash
# Install
pip install pylint

# Generate UML diagrams
pyreverse -o png -p Percell percell/
pyreverse -o dot -p Percell percell/  # For Graphviz format
```
- Generates class diagrams and package dependency diagrams
- Shows relationships between modules
- Helps visualize the separation between ports and adapters

**2. Pydeps - Dependency Visualization**
```bash
# Install
pip install pydeps

# Generate dependency graph
pydeps percell --max-bacon 2 --cluster
pydeps percell --show-deps --no-output
```
- Creates visual dependency graphs
- Identifies circular dependencies
- Shows module coupling

**3. Import-linter - Architecture Enforcement**
```bash
# Install
pip install import-linter

# Create .importlinter config file
```
```ini
[importlinter]
root_package = percell

[importlinter:contract:1]
name = Ports and adapters architecture
type = layers
layers =
    percell.domain
    percell.application
    percell.adapters
    percell.infrastructure
```

### 1.2 Architecture Fitness Functions

Create automated tests to verify architectural constraints:

```python
# tests/test_architecture.py
import ast
import os
from pathlib import Path

def test_no_infrastructure_imports_in_domain():
    """Domain layer should not depend on infrastructure"""
    domain_path = Path("percell/domain")
    for py_file in domain_path.rglob("*.py"):
        with open(py_file) as f:
            tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "infrastructure" not in alias.name
                        assert "adapters" not in alias.name

def test_adapters_implement_ports():
    """All adapters should implement corresponding port interfaces"""
    # Check that each adapter has a corresponding port interface
    pass
```

## 2. Visualization Tools

### 2.1 Architecture Decision Records (ADRs)
Document your architectural decisions:

```markdown
# ADR-001: Adopt Ports and Adapters Architecture

## Status
Accepted

## Context
Need to improve testability and maintainability of the Percell project

## Decision
Implement hexagonal architecture pattern

## Consequences
- Better separation of concerns
- Easier testing through dependency injection
- More complex initial setup
```

### 2.2 Interactive Visualization with Python

```python
# visualize_architecture.py
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
import ast

def analyze_imports(root_dir):
    """Analyze import structure of the project"""
    G = nx.DiGraph()
    
    for py_file in Path(root_dir).rglob("*.py"):
        module_name = str(py_file.relative_to(root_dir))[:-3].replace('/', '.')
        
        with open(py_file) as f:
            try:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith('percell'):
                            G.add_edge(module_name, node.module)
            except:
                pass
    
    return G

def visualize_layers(G):
    """Visualize the architecture layers"""
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    # Color nodes by layer
    colors = []
    for node in G.nodes():
        if 'domain' in node:
            colors.append('gold')
        elif 'application' in node:
            colors.append('lightblue')
        elif 'adapters' in node:
            colors.append('lightgreen')
        elif 'infrastructure' in node:
            colors.append('coral')
        else:
            colors.append('gray')
    
    plt.figure(figsize=(15, 10))
    nx.draw(G, pos, node_color=colors, with_labels=True, 
            node_size=500, font_size=8, arrows=True)
    plt.title("Percell Architecture Dependencies")
    plt.savefig("architecture_graph.png", dpi=300, bbox_inches='tight')
    plt.show()

# Usage
G = analyze_imports('percell')
visualize_layers(G)
```

## 3. Metrics and Quality Assessment

### 3.1 Coupling and Cohesion Metrics

```python
# metrics.py
from radon.complexity import cc_visit
from radon.metrics import mi_visit
from pathlib import Path

def analyze_metrics(root_dir):
    """Calculate maintainability and complexity metrics"""
    results = {}
    
    for py_file in Path(root_dir).rglob("*.py"):
        with open(py_file) as f:
            code = f.read()
            
        # Cyclomatic Complexity
        cc = cc_visit(code)
        
        # Maintainability Index
        mi = mi_visit(code, multi=True)
        
        results[str(py_file)] = {
            'complexity': sum(block.complexity for block in cc),
            'maintainability': mi
        }
    
    return results

# Generate report
metrics = analyze_metrics('percell')
```

### 3.2 Architecture Conformance Checking

```yaml
# architecture-rules.yml
rules:
  - name: "Domain Independence"
    source: "percell.domain.*"
    forbidden_dependencies:
      - "percell.infrastructure.*"
      - "percell.adapters.*"
      - "cellpose"
      - "fiji"
  
  - name: "Adapter Implementation"
    source: "percell.adapters.*"
    required_dependencies:
      - "percell.ports.*"
  
  - name: "Infrastructure Isolation"
    source: "percell.infrastructure.*"
    forbidden_dependencies:
      - "percell.domain.*"
```

## 4. Comprehensive Analysis Dashboard

```python
# analysis_dashboard.py
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class ArchitectureAnalyzer:
    def __init__(self, project_path):
        self.project_path = project_path
        self.metrics = {}
    
    def analyze_layer_sizes(self):
        """Analyze the size of each architectural layer"""
        layers = ['domain', 'application', 'adapters', 'infrastructure']
        sizes = {}
        
        for layer in layers:
            layer_path = Path(self.project_path) / layer
            if layer_path.exists():
                sizes[layer] = {
                    'files': len(list(layer_path.rglob('*.py'))),
                    'lines': sum(len(open(f).readlines()) 
                                for f in layer_path.rglob('*.py'))
                }
        
        return sizes
    
    def check_dependency_violations(self):
        """Check for architectural rule violations"""
        violations = []
        # Implementation of dependency checking
        return violations
    
    def generate_report(self):
        """Generate comprehensive HTML report"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Layer Sizes', 'Dependencies', 
                          'Complexity Distribution', 'Test Coverage'),
            specs=[[{'type': 'bar'}, {'type': 'scatter'}],
                   [{'type': 'box'}, {'type': 'pie'}]]
        )
        
        # Add visualizations
        # ... implementation ...
        
        fig.write_html("architecture_analysis.html")
```

## 5. Testing Strategy for Ports & Adapters

### 5.1 Unit Testing Ports
```python
# tests/test_ports.py
from unittest.mock import Mock
from percell.ports.segmentation_port import SegmentationPort

def test_segmentation_port_interface():
    """Test that port defines correct interface"""
    mock_adapter = Mock(spec=SegmentationPort)
    
    # Test interface methods exist
    assert hasattr(mock_adapter, 'segment_cells')
    assert hasattr(mock_adapter, 'get_parameters')
```

### 5.2 Integration Testing Adapters
```python
# tests/test_adapters.py
def test_cellpose_adapter_implements_port():
    """Test that CellposeAdapter correctly implements SegmentationPort"""
    from percell.adapters.cellpose_adapter import CellposeAdapter
    from percell.ports.segmentation_port import SegmentationPort
    
    adapter = CellposeAdapter()
    assert isinstance(adapter, SegmentationPort)
```

## 6. Continuous Architecture Validation

### 6.1 Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: architecture-check
        name: Check Architecture Constraints
        entry: python scripts/check_architecture.py
        language: python
        files: \.py$
```

### 6.2 CI/CD Pipeline Integration
```yaml
# .github/workflows/architecture.yml
name: Architecture Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install dependencies
        run: |
          pip install import-linter pydeps radon
      
      - name: Check architecture constraints
        run: |
          import-linter
          
      - name: Generate architecture report
        run: |
          python scripts/analyze_architecture.py
          
      - name: Upload artifacts
        uses: actions/upload-artifact@v2
        with:
          name: architecture-report
          path: |
            architecture_graph.png
            architecture_analysis.html
```

## 7. Refactoring Assessment Checklist

### Domain Layer
- [ ] Contains only business logic and entities
- [ ] No dependencies on external libraries
- [ ] All business rules encapsulated
- [ ] Value objects are immutable

### Application Layer
- [ ] Contains use cases/application services
- [ ] Orchestrates domain objects
- [ ] Defines port interfaces
- [ ] No infrastructure concerns

### Adapters Layer
- [ ] All adapters implement port interfaces
- [ ] Proper error handling and translation
- [ ] No business logic
- [ ] Clear separation between different adapter types

### Infrastructure Layer
- [ ] Contains technical implementations
- [ ] Database configurations
- [ ] External service integrations
- [ ] Framework-specific code

## 8. Recommended Tools Summary

| Tool | Purpose | Installation |
|------|---------|--------------|
| PyReverse | UML diagram generation | `pip install pylint` |
| Pydeps | Dependency visualization | `pip install pydeps` |
| Import-linter | Architecture rule enforcement | `pip install import-linter` |
| Radon | Code metrics | `pip install radon` |
| Prospector | Code quality analysis | `pip install prospector` |
| Graphviz | Graph visualization | `apt-get install graphviz` |
| PlantUML | Architecture diagrams | Download from plantuml.com |

## 9. Next Steps

1. **Run initial analysis**: Use the provided scripts to generate baseline metrics
2. **Document findings**: Create ADRs for architectural decisions
3. **Set up automation**: Implement pre-commit hooks and CI/CD checks
4. **Iterate on design**: Based on findings, refine the architecture
5. **Monitor trends**: Track metrics over time to ensure improvement

## 10. Example Analysis Script

```bash
#!/bin/bash
# run_analysis.sh

echo "Starting Percell Architecture Analysis..."

# Generate dependency graphs
echo "Generating dependency graphs..."
pydeps percell --max-bacon 2 --cluster -o dependencies.svg

# Run architecture linter
echo "Checking architecture constraints..."
import-linter

# Generate UML diagrams
echo "Creating UML diagrams..."
pyreverse -o png -p Percell percell/

# Calculate metrics
echo "Calculating code metrics..."
radon cc percell -s -j > complexity_report.json
radon mi percell -s > maintainability_report.txt

# Run custom analysis
echo "Running custom architecture analysis..."
python scripts/analyze_architecture.py

echo "Analysis complete! Check generated reports."
```

This comprehensive guide provides you with multiple approaches to analyze and validate your ports and adapters architecture refactoring. The combination of static analysis, visualization, metrics, and automated validation will help you ensure your refactoring is successful and identify areas for improvement.
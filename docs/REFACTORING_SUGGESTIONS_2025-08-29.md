Looking at your call graphs, I can see you've made good progress toward hexagonal architecture, but there are several areas where the boundaries could be cleaner. Here are my main suggestions:

## 1. **Module Dependencies are Inverted**
Your `percell.modules` package has extensive dependencies on infrastructure and core components. In hexagonal architecture, these should be application services that depend on ports, not concrete implementations.

**Issues:**
- Modules directly import and use `core.progress.run_subprocess_with_spinner`
- Direct file system operations instead of using ports
- Tight coupling to ImageJ implementation details

**Fix:**
- Move modules to an `application` layer
- Have them depend on domain ports, not infrastructure
- Inject dependencies rather than importing them directly

## 2. **Core Layer is Doing Too Much**
Your `core` package contains infrastructure concerns (progress bars, logging implementation details) mixed with what should be application orchestration.

**Suggestions:**
- Move `progress`, `logger` implementations to infrastructure
- Keep only interfaces/ports in core or domain
- `pipeline` and `stages` look like application services and should move there

## 3. **Direct Infrastructure Access**
Many components directly access infrastructure without going through ports:

```python
# Bad - modules directly calling infrastructure
percell.modules.create_cell_masks -> core.progress.run_subprocess_with_spinner

# Good - would be through a port
percell.application.create_cell_masks -> domain.ports.ProgressReporter
```

## 4. **CLI Mixed with Core Logic**
The CLI (`percell.cli.app`) has business logic mixed in (like validation and directory setup). 

**Fix:**
- CLI should be a thin adapter that only handles user interaction
- Move business logic to application services
- CLI calls application services through a facade or command bus

## 5. **Missing Clear Boundaries**

Here's how I'd restructure:

```
percell/
├── domain/
│   ├── models/          # Keep as is
│   ├── ports/           # All interfaces
│   └── exceptions/      # Domain exceptions
├── application/
│   ├── services/        # Current modules refactored
│   ├── workflows/       # Pipeline orchestration
│   └── commands/        # Command/Query handlers
├── infrastructure/
│   ├── adapters/        # Implementations of ports
│   ├── file_service/    
│   ├── imagej/         
│   ├── progress/        # Move from core
│   └── logging/         # Move from core
├── adapters/
│   ├── cli/            # CLI adapter
│   └── web/            # Future web adapter
└── main.py             # Composition root
```

## 6. **Specific Refactoring Steps**

1. **Extract interfaces from concrete implementations:**
   - Create a `ProgressPort` interface in domain
   - Move current progress implementation to infrastructure
   
2. **Dependency injection in modules:**
   ```python
   # Instead of:
   class CreateCellMasks:
       def run(self):
           run_subprocess_with_spinner(...)  # Direct call
   
   # Do:
   class CreateCellMasks:
       def __init__(self, subprocess_runner: SubprocessPort):
           self.subprocess_runner = subprocess_runner
       
       def run(self):
           self.subprocess_runner.run_with_progress(...)
   ```

3. **Remove circular dependencies:**
   - `percell.core` imports from `percell.cli.app`
   - This suggests core depends on the adapter layer, which is backwards

4. **Consolidate service factories:**
   - Your `ServiceFactory` is good but needs to be the composition root
   - All wiring should happen there, not scattered throughout

5. **Separate configuration from domain:**
   - Config loading is infrastructure
   - Domain should receive already-validated configuration objects

The main principle: dependencies should flow inward. Adapters → Application → Domain, never the reverse. Your domain should have zero imports from other layers, and your application should only import from domain.
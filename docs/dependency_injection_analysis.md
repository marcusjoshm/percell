# Dependency Injection Analysis

## Current State

### DI Container Implementation

**Location**: `percell/application/container.py`

The codebase uses a **simple dataclass-based DI container** with manual wiring:

```python
@dataclass(slots=True)
class Container:
    cfg: ConfigurationService
    orchestrator: WorkflowOrchestrationService
    workflow: WorkflowCoordinator
    step_exec: StepExecutionCoordinator
    imagej: ImageJMacroAdapter
    cellpose: CellposeSubprocessAdapter
    fs: LocalFileSystemAdapter
    imgproc: PILImageProcessingAdapter

def build_container(config_path: Path) -> Container:
    # Manual construction and wiring of dependencies
    ...
```

### Bootstrap Wrapper

**Location**: `percell/main/bootstrap.py`

```python
def bootstrap(config_path: str | Path):
    """Build and return the DI container for the application."""
    return build_container(Path(config_path))
```

**Purpose**: Converts string path to Path object before calling `build_container`.

### Current Usage Pattern

1. **Main Entry Point** (`main/main.py`):
   ```python
   container = bootstrap(config_path)  # Line 103

   ports = {
       "imagej": container.imagej,
       "fs": container.fs,
       "imgproc": container.imgproc,
       "cellpose": container.cellpose,
   }
   pipeline = Pipeline(config, logger, args, ports=ports)
   ```

2. **Pipeline** (`application/pipeline_api.py`):
   ```python
   def __init__(self, ..., ports: Optional[Dict[str, Any]] = None):
       self.ports = ports or {}
       self.executor = StageExecutor(..., ports=self.ports)
   ```

3. **Stage Executor** (`application/stages_api.py`):
   - Passes ports to stages via `**kwargs`

4. **Individual Stages**:
   ```python
   def run(self, **kwargs):
       imagej = kwargs.get('imagej')
       imgproc = kwargs.get('imgproc')
       # Use dependencies
   ```

---

## Analysis

### ✅ What's Working Well

1. **Proper Hexagonal Architecture**
   - Container creates adapters that implement ports
   - Dependencies flow inward (adapters → ports → domain)

2. **Centralized Wiring**
   - All dependency construction in one place (`build_container`)
   - Easy to see the entire object graph

3. **Testability**
   - Stages accept dependencies via kwargs
   - Easy to inject mocks for testing

4. **Type Safety**
   - Dataclass provides type hints for all dependencies
   - IDE autocomplete works well

### ⚠️ Current Limitations

1. **Kwargs-Based Injection**
   - Stages use `kwargs.get('imagej')` instead of constructor injection
   - No compile-time validation of dependencies
   - Manual extraction of dependencies in each stage

2. **Ports Dictionary Pattern**
   - Converts structured Container to flat dict: `{"imagej": adapter, ...}`
   - Loses type information
   - Requires manual key matching

3. **Bootstrap Wrapper**
   - **Unnecessary abstraction** - only converts string to Path
   - Adds extra layer with no real benefit
   - Could be eliminated

4. **Manual Fallback Logic**
   - Stages create adapters if not provided via kwargs
   - Example: `adapter = kwargs.get('cellpose') or CellposeSubprocessAdapter(...)`
   - Duplicates initialization logic

---

## Recommendations

### Priority 1: Remove Bootstrap Wrapper ✅ RECOMMENDED

**Current**:
```python
from percell.main.bootstrap import bootstrap
container = bootstrap(config_path)
```

**Simplified**:
```python
from percell.application.container import build_container
container = build_container(Path(config_path))
```

**Benefits**:
- One less file to maintain
- More direct and explicit
- No loss of functionality

**Implementation**:
1. Update `main.py` to import `build_container` directly
2. Delete `bootstrap.py`
3. Update any tests that use bootstrap

---

### Priority 2: Consider Constructor-Based Injection (Optional)

**Current Pattern** (kwargs-based):
```python
class SegmentationStage(StageBase):
    def run(self, **kwargs):
        imagej = kwargs.get('imagej')
        imgproc = kwargs.get('imgproc')
        # Use dependencies
```

**Alternative** (constructor-based):
```python
class SegmentationStage(StageBase):
    def __init__(self, config, logger, imagej, imgproc, stage_name="segmentation"):
        super().__init__(config, logger, stage_name)
        self.imagej = imagej
        self.imgproc = imgproc

    def run(self):
        # Use self.imagej, self.imgproc directly
```

**Pros**:
- Explicit dependencies declared in constructor
- Type checking at construction time
- No need for kwargs.get() everywhere
- Clearer what each stage needs

**Cons**:
- More changes required across all stages
- Breaks current stage registration pattern
- Would need to update StageExecutor

**Recommendation**: Keep current pattern for now unless you're doing a major refactor

---

### Priority 3: Improve Container → Pipeline Bridge (Optional)

**Current**:
```python
ports = {
    "imagej": container.imagej,
    "fs": container.fs,
    "imgproc": container.imgproc,
    "cellpose": container.cellpose,
}
pipeline = Pipeline(config, logger, args, ports=ports)
```

**Alternative 1** - Pass container directly:
```python
pipeline = Pipeline(config, logger, args, container=container)
```

**Alternative 2** - Keep container as singleton:
```python
# In container.py
_global_container: Optional[Container] = None

def get_container() -> Container:
    if _global_container is None:
        raise RuntimeError("Container not initialized")
    return _global_container

def initialize_container(config_path: Path) -> Container:
    global _global_container
    _global_container = build_container(config_path)
    return _global_container
```

Then stages could do:
```python
from percell.application.container import get_container
container = get_container()
imagej = container.imagej
```

**Pros**: More centralized, less parameter passing
**Cons**: Global state, less testable, hides dependencies

**Recommendation**: Keep current pattern - explicit is better than implicit

---

## Comparison with Full DI Frameworks

### Current Approach vs. dependency-injector / punq / etc.

**Current (Manual DI)**:
```python
@dataclass
class Container:
    imagej: ImageJMacroAdapter

def build_container(config_path):
    imagej = ImageJMacroAdapter(config.get("imagej_path"))
    return Container(imagej=imagej)
```

**With dependency-injector**:
```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    imagej = providers.Singleton(
        ImageJMacroAdapter,
        config.imagej_path
    )
```

### Should You Use a Framework?

**Current Complexity**: ~10 dependencies, simple object graph
**Framework Overhead**: Learning curve, additional dependency, more magic

**Verdict**: ❌ **Not recommended** for this codebase

**Reasons**:
1. Current manual DI is simple and clear
2. No circular dependencies or complex lifetime management
3. Object graph is straightforward
4. No need for features like scopes, lazy loading, etc.
5. Manual approach is easier to debug and understand

---

## Action Items

### Immediate (Low Effort, High Value)

1. ✅ **Remove `bootstrap.py` wrapper**
   - Replace with direct `build_container()` calls
   - Delete `percell/main/bootstrap.py`
   - Update tests

### Medium-Term (Consider If Refactoring)

2. ⏸️ **Consolidate adapter fallback logic**
   - Stages shouldn't create adapters inline
   - All adapter creation should go through container
   - Requires ensuring container is always available

### Long-Term (Only If Needed)

3. ⏸️ **Move to constructor injection** (only if adding many new stages)
4. ⏸️ **Consider DI framework** (only if dependency graph becomes complex)

---

## Summary

### Is DI Being Used Well? ✅ **Yes, with minor improvements possible**

**Strengths**:
- Proper hexagonal architecture
- Centralized dependency wiring
- Testable design
- Clear, maintainable code

**Quick Win**:
- Remove unnecessary `bootstrap.py` wrapper

**Current Pattern is Good Enough**:
- Manual DI works well for this codebase size
- No need for heavy DI framework
- kwargs-based injection is fine for current scale

### Final Recommendation

**Remove `bootstrap.py`** - it's an unnecessary wrapper with no benefits.

**Keep everything else as-is** - the current DI pattern is appropriate for the codebase complexity and follows good hexagonal architecture principles.

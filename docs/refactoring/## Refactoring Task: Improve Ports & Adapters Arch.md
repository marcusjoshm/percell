## Refactoring Task: Improve Ports & Adapters Architecture

You are tasked with refining an existing ports and adapters architecture implementation based on code review feedback. The codebase has been successfully refactored but needs specific improvements for type safety, error handling, and architectural consistency.

### Context
The project uses hexagonal architecture with:
- Domain layer (services, value objects)
- Ports (interfaces) 
- Adapters (implementations)
- Application layer (use cases, commands)
- Infrastructure layer (DI container, configuration)

### Required Changes

#### 1. Fix Container Type Safety
**Current Issue**: Container methods return concrete adapters but use type ignores
**Solution**: Change all container methods to return port interfaces instead of concrete implementations

Files to modify:
- `percell/infrastructure/bootstrap/container.py`

Changes needed:
```python
# Instead of:
def image_adapter(self) -> TifffileImageAdapter:
    return self._factory.build_image_reader()  # type: ignore[return-value]

# Change to:
def image_reader(self) -> ImageReaderPort:
    return self._factory.build_image_reader()

def image_writer(self) -> ImageWriterPort:
    return self._factory.build_image_writer()
```

Update all adapter-returning methods to return their port interface types. Update any calling code to use the new method names.

#### 2. Remove Global Singleton Pattern
**Current Issue**: Global container singleton limits testability
**Solution**: Remove global state, use dependency injection at entry points

Changes needed:
- Remove `_GLOBAL_CONTAINER` and `get_container()` function
- Modify main.py to instantiate container directly
- Pass container explicitly where needed

#### 3. Fix Mixed Responsibilities in Use Cases
**Current Issue**: GroupCellsUseCase directly imports pandas
**Solution**: Move DataFrame creation to metadata adapter

Files to modify:
- `percell/application/use_cases/group_cells.py`
- `percell/adapters/outbound/pandas_metadata_adapter.py`
- `percell/ports/outbound/metadata_port.py`

Add to MetadataStorePort:
```python
def create_dataframe_from_records(self, records: List[Dict[str, Any]]) -> Any:
    """Create a dataframe from records (implementation-specific return type)."""
```

#### 4. Add Domain-Specific Exceptions
**Current Issue**: Generic ValueError/RuntimeError in domain
**Solution**: Create domain-specific exceptions

Create new file: `percell/domain/exceptions.py`
```python
class DomainException(Exception):
    """Base exception for domain errors."""

class InvalidGroupingParametersError(DomainException):
    """Raised when grouping parameters are invalid."""

class GroupingStrategyNotAvailableError(DomainException):
    """Raised when a grouping strategy requires unavailable dependencies."""

class InvalidROIGeometryError(DomainException):
    """Raised when ROI geometry is insufficient for operations."""
```

Update domain services to use these exceptions.

#### 5. Improve Configuration Adapter
**Current Issue**: Configuration loads on every call
**Solution**: Cache configuration after first load

Modify `percell/infrastructure/config/json_configuration_adapter.py`:
- Add `_loaded: bool = False` attribute
- Check and skip reload if already loaded
- Add `reload()` method for explicit refresh

#### 6. Strategy Availability Checking
**Current Issue**: Runtime errors for missing scikit-learn
**Solution**: Add capability checking to service

Add to `CellGroupingService`:
```python
@classmethod
def available_strategies(cls) -> List[str]:
    """Return list of available grouping strategies based on installed dependencies."""
    strategies = ["uniform"]
    try:
        import sklearn
        strategies.extend(["kmeans", "gmm"])
    except ImportError:
        pass
    return strategies
```

#### 7. Update Shim Documentation
Add docstring to `percell/modules/group_cells.py`:
```python
"""Legacy compatibility shim for group_cells module.

This module provides backward compatibility for existing code using the old
group_cells interface. New code should use the ports & adapters architecture
directly via the use cases in percell.application.use_cases.group_cells.

Migration path:
1. Set PERCELL_USE_NEW_ARCH=1 to test with new architecture
2. Update imports to use new use case classes
3. Remove dependency on this shim module

This shim will be deprecated in version X.0 and removed in version Y.0.
"""
```

### Testing Requirements
After making changes:
1. Ensure all existing tests pass
2. Add unit tests for new domain exceptions
3. Add tests for strategy availability checking
4. Verify type checking passes without ignores

### Success Criteria
- No type: ignore comments in production code
- Container methods return port interfaces
- Domain exceptions provide clear error semantics
- Configuration caches properly
- Strategy selection handles missing dependencies gracefully
- Documentation clearly explains migration path

### Additional Notes
- Maintain backward compatibility through shims
- Keep changes focused and incremental
- Ensure each change has corresponding tests
- Update docstrings where interfaces change
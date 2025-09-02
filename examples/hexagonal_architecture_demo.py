#!/usr/bin/env python3
"""
Hexagonal Architecture Demonstration

This script demonstrates the new hexagonal architecture implementation
for the Percell project, showing how to use the composition root and
application services.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from percell.main.composition_root import get_composition_root, reset_composition_root
from percell.domain.exceptions import DomainError


def demonstrate_composition_root():
    """Demonstrate the composition root and dependency injection."""
    print("🔧 Hexagonal Architecture Demonstration")
    print("=" * 50)
    
    # Get the composition root
    composition_root = get_composition_root()
    
    print("✅ Composition root created successfully")
    
    # List available services
    services = composition_root.list_available_services()
    print(f"📋 Available services: {', '.join(services)}")
    
    return composition_root


def demonstrate_service_creation():
    """Demonstrate creating and using application services."""
    print("\n🎯 Application Service Demonstration")
    print("-" * 40)
    
    composition_root = get_composition_root()
    
    # Get the create cell masks service
    service = composition_root.get_service('create_cell_masks_service')
    
    print("✅ CreateCellMasksService retrieved from composition root")
    print(f"📦 Service type: {type(service).__name__}")
    
    # Check dependencies
    print("🔗 Service dependencies:")
    print(f"  - SubprocessPort: {type(service.subprocess_port).__name__}")
    print(f"  - FileSystemPort: {type(service.filesystem_port).__name__}")
    print(f"  - LoggingPort: {type(service.logging_port).__name__}")
    
    return service


def demonstrate_dependency_injection():
    """Demonstrate dependency injection and interface usage."""
    print("\n🔌 Dependency Injection Demonstration")
    print("-" * 40)
    
    composition_root = get_composition_root()
    
    # Get infrastructure adapters
    subprocess_adapter = composition_root.get_service('subprocess_port')
    filesystem_adapter = composition_root.get_service('filesystem_port')
    logging_adapter = composition_root.get_service('logging_port')
    
    print("✅ Infrastructure adapters retrieved")
    print(f"  - SubprocessAdapter: {type(subprocess_adapter).__name__}")
    print(f"  - FileSystemAdapter: {type(filesystem_adapter).__name__}")
    print(f"  - LoggingAdapter: {type(logging_adapter).__name__}")
    
    # Test logging
    logging_adapter.log_info("Testing hexagonal architecture")
    logging_adapter.log_warning("This is a demonstration")
    
    return subprocess_adapter, filesystem_adapter, logging_adapter


def demonstrate_error_handling():
    """Demonstrate domain exception handling."""
    print("\n🚨 Error Handling Demonstration")
    print("-" * 40)
    
    from percell.domain.exceptions import (
        DomainError, 
        FileSystemError, 
        SubprocessError, 
        ConfigurationError
    )
    
    try:
        raise FileSystemError("Example file system error")
    except DomainError as e:
        print(f"✅ Caught domain error: {e}")
    
    try:
        raise SubprocessError("Example subprocess error")
    except DomainError as e:
        print(f"✅ Caught domain error: {e}")
    
    try:
        raise ConfigurationError("Example configuration error")
    except DomainError as e:
        print(f"✅ Caught domain error: {e}")


def demonstrate_clean_architecture():
    """Demonstrate clean architecture principles."""
    print("\n🏗️ Clean Architecture Principles")
    print("-" * 40)
    
    composition_root = get_composition_root()
    service = composition_root.get_service('create_cell_masks_service')
    
    print("✅ Dependency Inversion:")
    print("  - Application service depends on domain ports (interfaces)")
    print("  - Infrastructure adapters implement domain ports")
    print("  - Dependencies flow inward: Adapters → Application → Domain")
    
    print("\n✅ Interface Segregation:")
    print("  - Each port has a single, focused responsibility")
    print("  - Services depend only on the interfaces they need")
    
    print("\n✅ Single Responsibility:")
    print("  - Each service has one clear purpose")
    print("  - Each adapter handles one type of external system")
    
    print("\n✅ Open/Closed Principle:")
    print("  - Easy to add new implementations of ports")
    print("  - Easy to extend with new services")


def demonstrate_testability():
    """Demonstrate how the architecture improves testability."""
    print("\n🧪 Testability Demonstration")
    print("-" * 40)
    
    from unittest.mock import Mock
    from percell.domain.ports import SubprocessPort, FileSystemPort, LoggingPort
    from percell.application.services.create_cell_masks_service import CreateCellMasksService
    
    # Create mock dependencies
    mock_subprocess = Mock(spec=SubprocessPort)
    mock_filesystem = Mock(spec=FileSystemPort)
    mock_logging = Mock(spec=LoggingPort)
    mock_image_processing = Mock()
    
    # Create service with mocked dependencies
    service = CreateCellMasksService(
        subprocess_port=mock_subprocess,
        filesystem_port=mock_filesystem,
        logging_port=mock_logging,
        image_processing_service=mock_image_processing
    )
    
    print("✅ Service created with mocked dependencies")
    print("✅ No real infrastructure dependencies")
    print("✅ Easy to test in isolation")


def main():
    """Run the hexagonal architecture demonstration."""
    try:
        # Reset composition root for clean demonstration
        reset_composition_root()
        
        # Run demonstrations
        demonstrate_composition_root()
        demonstrate_service_creation()
        demonstrate_dependency_injection()
        demonstrate_error_handling()
        demonstrate_clean_architecture()
        demonstrate_testability()
        
        print("\n🎉 Hexagonal Architecture Demonstration Complete!")
        print("\n📚 Key Benefits Demonstrated:")
        print("  - Clean separation of concerns")
        print("  - Dependency injection and inversion")
        print("  - Improved testability")
        print("  - Better error handling")
        print("  - Maintainable and extensible design")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

"""
Tests for hexagonal architecture implementation.

This test suite validates the clean architecture implementation
and demonstrates proper dependency injection and separation of concerns.
"""

import unittest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import shutil

from percell.main.composition_root import get_composition_root, reset_composition_root
from percell.domain.ports import SubprocessPort, FileSystemPort, LoggingPort
from percell.application.services.create_cell_masks_service import CreateCellMasksService


class TestHexagonalArchitecture(unittest.TestCase):
    """Test the hexagonal architecture implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Reset composition root for clean state
        reset_composition_root()
        
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.roi_dir = Path(self.temp_dir) / "rois"
        self.mask_dir = Path(self.temp_dir) / "masks"
        self.output_dir = Path(self.temp_dir) / "output"
        
        self.roi_dir.mkdir()
        self.mask_dir.mkdir()
        self.output_dir.mkdir()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
        reset_composition_root()
    
    def test_composition_root_creation(self):
        """Test that composition root can be created and provides services."""
        composition_root = get_composition_root()
        
        # Verify composition root exists
        self.assertIsNotNone(composition_root)
        
        # Verify it provides expected services
        services = composition_root.list_available_services()
        self.assertIn('create_cell_masks_service', services)
        self.assertIn('subprocess_port', services)
        self.assertIn('filesystem_port', services)
        self.assertIn('logging_port', services)
    
    def test_service_dependency_injection(self):
        """Test that services receive their dependencies through injection."""
        composition_root = get_composition_root()
        service = composition_root.get_service('create_cell_masks_service')
        
        # Verify service is properly injected with dependencies
        self.assertIsInstance(service, CreateCellMasksService)
        self.assertIsInstance(service.subprocess_port, SubprocessPort)
        self.assertIsInstance(service.filesystem_port, FileSystemPort)
        self.assertIsInstance(service.logging_port, LoggingPort)
    
    def test_clean_dependency_flow(self):
        """Test that dependencies flow inward (adapters → application → domain)."""
        composition_root = get_composition_root()
        
        # Application service should depend on domain ports (interfaces)
        service = composition_root.get_service('create_cell_masks_service')
        
        # Verify service depends on abstractions, not concretions
        self.assertIsInstance(service.subprocess_port, SubprocessPort)  # Interface
        self.assertIsInstance(service.filesystem_port, FileSystemPort)  # Interface
        self.assertIsInstance(service.logging_port, LoggingPort)        # Interface
        
        # Verify infrastructure adapters implement domain ports
        subprocess_adapter = composition_root.get_service('subprocess_port')
        filesystem_adapter = composition_root.get_service('filesystem_port')
        logging_adapter = composition_root.get_service('logging_port')
        
        self.assertIsInstance(subprocess_adapter, SubprocessPort)  # Implements interface
        self.assertIsInstance(filesystem_adapter, FileSystemPort)  # Implements interface
        self.assertIsInstance(logging_adapter, LoggingPort)        # Implements interface
    
    def test_service_isolation(self):
        """Test that services can be tested in isolation with mocks."""
        # Create mock dependencies
        mock_subprocess = Mock(spec=SubprocessPort)
        mock_filesystem = Mock(spec=FileSystemPort)
        mock_logging = Mock(spec=LoggingPort)
        mock_image_processing = Mock(spec=object)
        
        # Create service with mocked dependencies
        service = CreateCellMasksService(
            subprocess_port=mock_subprocess,
            filesystem_port=mock_filesystem,
            logging_port=mock_logging,
            image_processing_service=mock_image_processing
        )
        
        # Verify service was created successfully
        self.assertIsInstance(service, CreateCellMasksService)
        self.assertEqual(service.subprocess_port, mock_subprocess)
        self.assertEqual(service.filesystem_port, mock_filesystem)
        self.assertEqual(service.logging_port, mock_logging)
    
    def test_domain_exceptions(self):
        """Test that domain exceptions are used for business logic errors."""
        from percell.domain.exceptions import DomainError, FileSystemError, SubprocessError
        
        # Verify domain exceptions exist and are properly structured
        self.assertTrue(issubclass(FileSystemError, DomainError))
        self.assertTrue(issubclass(SubprocessError, DomainError))
        
        # Test that exceptions can be raised and caught
        try:
            raise FileSystemError("Test error")
        except DomainError as e:
            self.assertIsInstance(e, FileSystemError)
            self.assertEqual(str(e), "Test error")
    
    def test_configuration_injection(self):
        """Test that configuration is properly injected into adapters."""
        composition_root = get_composition_root()
        config = composition_root.get_config()
        
        # Verify configuration exists
        self.assertIsNotNone(config)
        
        # Verify filesystem adapter has access to configuration
        filesystem_adapter = composition_root.get_service('filesystem_port')
        self.assertIsNotNone(filesystem_adapter.config)
    
    @patch('percell.infrastructure.adapters.subprocess_adapter.subprocess.run')
    def test_subprocess_adapter_implementation(self, mock_subprocess_run):
        """Test that subprocess adapter properly implements the port."""
        # Mock subprocess.run to return success
        mock_subprocess_run.return_value.returncode = 0
        
        composition_root = get_composition_root()
        subprocess_adapter = composition_root.get_service('subprocess_port')
        
        # Test simple command execution
        result = subprocess_adapter.run_simple(['echo', 'test'])
        self.assertEqual(result, 0)
        
        # Verify subprocess.run was called
        mock_subprocess_run.assert_called_once()
    
    def test_filesystem_adapter_implementation(self):
        """Test that filesystem adapter properly implements the port."""
        composition_root = get_composition_root()
        filesystem_adapter = composition_root.get_service('filesystem_port')
        
        # Test directory creation
        test_dir = Path(self.temp_dir) / "test_create"
        filesystem_adapter.create_directory(test_dir)
        
        # Verify directory was created
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())
        
        # Test file existence check
        test_file = Path(self.temp_dir) / "test_file.txt"
        test_file.write_text("test")
        
        self.assertTrue(filesystem_adapter.file_exists(test_file))
        self.assertFalse(filesystem_adapter.file_exists(Path("nonexistent.txt")))
    
    def test_logging_adapter_implementation(self):
        """Test that logging adapter properly implements the port."""
        composition_root = get_composition_root()
        logging_adapter = composition_root.get_service('logging_port')
        
        # Test logger creation
        logger = logging_adapter.get_logger("test_logger")
        self.assertIsNotNone(logger)
        
        # Test logging methods (should not raise exceptions)
        logging_adapter.log_info("Test info message")
        logging_adapter.log_warning("Test warning message")
        logging_adapter.log_error("Test error message")
        logging_adapter.log_debug("Test debug message")


class TestCreateCellMasksService(unittest.TestCase):
    """Test the CreateCellMasksService specifically."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_composition_root()
        
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.roi_dir = Path(self.temp_dir) / "rois"
        self.mask_dir = Path(self.temp_dir) / "masks"
        self.output_dir = Path(self.temp_dir) / "output"
        
        self.roi_dir.mkdir()
        self.mask_dir.mkdir()
        self.output_dir.mkdir()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
        reset_composition_root()
    
    def test_service_initialization(self):
        """Test that service can be initialized with dependencies."""
        composition_root = get_composition_root()
        service = composition_root.get_service('create_cell_masks_service')
        
        # Verify service has all required dependencies
        self.assertIsNotNone(service.subprocess_port)
        self.assertIsNotNone(service.filesystem_port)
        self.assertIsNotNone(service.logging_port)
        self.assertIsNotNone(service.logger)
    
    def test_service_method_signature(self):
        """Test that service has the expected public interface."""
        composition_root = get_composition_root()
        service = composition_root.get_service('create_cell_masks_service')
        
        # Verify service has the expected method
        self.assertTrue(hasattr(service, 'create_cell_masks'))
        self.assertTrue(callable(service.create_cell_masks))
        
        # Verify method signature
        import inspect
        sig = inspect.signature(service.create_cell_masks)
        params = list(sig.parameters.keys())
        
        # Check that all expected parameters are present
        expected_params = ['roi_directory', 'mask_directory', 'output_directory', 'imagej_path', 'auto_close']
        for param in expected_params:
            self.assertIn(param, params)


if __name__ == '__main__':
    unittest.main()

"""
Analysis port interface for Percell.

Defines the contract for analysis operations and result generation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from percell.domain.entities.cell import Cell
from percell.domain.entities.image import Image
from percell.domain.value_objects.file_path import FilePath


class AnalysisPort(ABC):
    """
    Port interface for analysis operations.
    
    This interface defines how external systems can trigger analysis
    and retrieve results.
    """
    
    @abstractmethod
    def analyze_cells(self, cells: List[Cell], 
                     analysis_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform analysis on a collection of cells.
        
        Args:
            cells: List of cells to analyze
            analysis_parameters: Analysis configuration
            
        Returns:
            Analysis results
            
        Raises:
            AnalysisError: If analysis fails
        """
        pass
    
    @abstractmethod
    def generate_summary_statistics(self, cells: List[Cell]) -> Dict[str, Any]:
        """
        Generate summary statistics for a cell population.
        
        Args:
            cells: List of cells to summarize
            
        Returns:
            Summary statistics
        """
        pass
    
    @abstractmethod
    def create_analysis_report(self, analysis_results: Dict[str, Any], 
                             output_path: FilePath) -> None:
        """
        Create a comprehensive analysis report.
        
        Args:
            analysis_results: Analysis results to include
            output_path: Path to save the report
            
        Raises:
            AnalysisError: If report creation fails
        """
        pass
    
    @abstractmethod
    def export_results_csv(self, cells: List[Cell], 
                          output_path: FilePath) -> None:
        """
        Export cell analysis results to CSV.
        
        Args:
            cells: Cells with analysis results
            output_path: Path to save CSV file
            
        Raises:
            AnalysisError: If export fails
        """
        pass
    
    @abstractmethod
    def export_results_excel(self, analysis_results: Dict[str, Any], 
                           output_path: FilePath) -> None:
        """
        Export analysis results to Excel file.
        
        Args:
            analysis_results: Analysis results to export
            output_path: Path to save Excel file
            
        Raises:
            AnalysisError: If export fails
        """
        pass
    
    @abstractmethod
    def create_visualization(self, cells: List[Cell], 
                           visualization_type: str,
                           parameters: Dict[str, Any]) -> FilePath:
        """
        Create visualization of analysis results.
        
        Args:
            cells: Cells to visualize
            visualization_type: Type of visualization
            parameters: Visualization parameters
            
        Returns:
            Path to created visualization
            
        Raises:
            AnalysisError: If visualization creation fails
        """
        pass
    
    @abstractmethod
    def compare_conditions(self, cell_groups: Dict[str, List[Cell]]) -> Dict[str, Any]:
        """
        Compare analysis results between different conditions.
        
        Args:
            cell_groups: Dictionary mapping condition names to cell lists
            
        Returns:
            Comparison results
        """
        pass
    
    @abstractmethod
    def perform_statistical_tests(self, cell_groups: Dict[str, List[Cell]], 
                                 test_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform statistical tests on analysis results.
        
        Args:
            cell_groups: Dictionary mapping groups to cell lists
            test_parameters: Statistical test parameters
            
        Returns:
            Statistical test results
        """
        pass
    
    @abstractmethod
    def validate_analysis_results(self, cells: List[Cell]) -> Dict[str, Any]:
        """
        Validate analysis results for quality and completeness.
        
        Args:
            cells: Cells with analysis results to validate
            
        Returns:
            Validation results
        """
        pass
    
    @abstractmethod
    def get_analysis_progress(self, analysis_id: str) -> Dict[str, Any]:
        """
        Get progress information for a running analysis.
        
        Args:
            analysis_id: ID of the analysis
            
        Returns:
            Progress information
        """
        pass


class AnalysisError(Exception):
    """Exception raised by analysis operations."""
    pass

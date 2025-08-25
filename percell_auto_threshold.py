#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Standalone Auto-Threshold Analysis Launcher

This script provides a standalone interface for the auto-threshold analysis module.
It can be run independently of the main PerCell pipeline.

Usage:
    python percell_auto_threshold.py --input /path/to/images --output /path/to/results --method otsu
"""

import sys
import os
from pathlib import Path

# Add the percell package to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Main entry point for standalone auto-threshold analysis."""
    try:
        # Import the auto-threshold analysis module
        from percell.modules.auto_threshold_analysis import main as auto_threshold_main
        
        # Run the auto-threshold analysis
        auto_threshold_main()
        
    except ImportError as e:
        print(f"Error: Could not import auto-threshold analysis module: {e}")
        print("Make sure you're running this script from the percell directory.")
        sys.exit(1)
    except Exception as e:
        print(f"Error running auto-threshold analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

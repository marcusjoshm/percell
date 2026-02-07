"""
Main module for Percell package

To run the main entry point, use:
    python -m percell.main.main
"""

__all__ = ['main']


def main():
    """Lazy import wrapper to avoid RuntimeWarning."""
    from .main import main as _main
    return _main()

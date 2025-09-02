"""
Infrastructure adapters implementing domain ports.

These adapters provide concrete implementations of the domain ports
for external systems like file systems, subprocess execution, etc.
"""

__all__ = [
    "SubprocessAdapter",
    "FileSystemAdapter", 
    "ConfigurationAdapter",
    "LoggingAdapter",
    "ImageJAdapter",
    "StageRegistryAdapter"
]

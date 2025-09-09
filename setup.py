#!/usr/bin/env python3
"""
Setup script for Percell package
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("percell/setup/requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="percell",
    version="1.0.0",
    author="Joshua Marcus",
    author_email="joshua.marcus@bcm.edu",
    description="Microscopy Per Cell Analysis Pipeline - Global Installation Available",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/marcusjoshm/percell",
    packages=[
        "percell",
        "percell.adapters", 
        "percell.application",
        "percell.domain",
        "percell.domain.services",
        "percell.main",
        "percell.ports",
        "percell.ports.driven",
        "percell.ports.driving",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Image Processing",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "percell=percell.main.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "percell": [
            "config/*.json",
            "config/*.template.json",
            "bash/*.sh",
            "macros/*.ijm", 
            "art/*.png",
            "setup/*.txt",
            "setup/*.py",
            "setup/*.sh",
        ],
    },
    zip_safe=False,
) 
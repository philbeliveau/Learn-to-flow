"""
Setup script for EZBI Analytics ML Engine
"""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ezbi-analytics-ml-engine",
    version="1.0.0",
    author="EZBI Analytics Team",
    author_email="dev@ezbi-analytics.com",
    description="Manufacturing ML Engine with Prophet, LSTM, and Ensemble models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/ezbi-analytics",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Manufacturing",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.1.0",
            "pytest-cov>=3.0.0",
            "pytest-mock>=3.8.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "pre-commit>=2.17.0",
        ],
        "docs": [
            "sphinx>=4.5.0",
            "sphinx-rtd-theme>=1.0.0",
            "sphinx-autodoc-typehints>=1.17.0",
        ],
        "monitoring": [
            "grafana-api>=1.0.0",
            "prometheus-client>=0.14.0",
            "wandb>=0.13.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ezbi-ml=ml_engine:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "ml_engine": [
            "config/*.py",
            "*.md",
            "*.txt",
        ],
    },
    keywords="machine learning, manufacturing, forecasting, prophet, lstm, ensemble, time series",
    project_urls={
        "Bug Reports": "https://github.com/your-org/ezbi-analytics/issues",
        "Source": "https://github.com/your-org/ezbi-analytics",
        "Documentation": "https://docs.ezbi-analytics.com",
    },
)
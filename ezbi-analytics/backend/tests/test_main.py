#!/usr/bin/env python3
"""
Basic smoke tests for EZBI Analytics platform.
"""
import pytest
import os
from pathlib import Path


@pytest.mark.smoke
def test_project_structure():
    """Test that essential project structure exists."""
    project_root = Path(__file__).parent.parent
    
    # Check main directories
    assert (project_root / "app").exists()
    assert (project_root / "requirements.txt").exists()
    
    # Check main application files
    assert (project_root / "app" / "__init__.py").exists()
    assert (project_root / "app" / "main.py").exists()


@pytest.mark.smoke
def test_environment_variables():
    """Test that required environment variables are available."""
    # These should be set during testing
    assert os.getenv("TESTING") == "1"
    assert os.getenv("ENVIRONMENT") == "testing"


@pytest.mark.smoke  
def test_basic_imports():
    """Test that core modules can be imported."""
    try:
        import fastapi
        import sqlalchemy
        import pydantic
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import required module: {e}")


@pytest.mark.smoke
def test_configuration_files():
    """Test that configuration files exist."""
    project_root = Path(__file__).parent.parent.parent
    
    # Check configuration files
    assert (project_root / "docker-compose.yml").exists()
    assert (project_root / ".env.example").exists()
    assert (project_root / "README.md").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
SmartHire Gateway backend package.

This package exposes the FastAPI application factory via ``create_app`` to
enable flexible instantiation during testing and deployment.
"""

from .main import create_app

__all__ = ["create_app"]

"""Local-only HTTP API for the MEGIS guided IR seam."""

from .server import ApiConfigurationError, create_server

__all__ = ["ApiConfigurationError", "create_server"]

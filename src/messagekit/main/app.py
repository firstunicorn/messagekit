"""Application instance for uvicorn entry point."""

from messagekit.main.app_factory import create_app

app = create_app()

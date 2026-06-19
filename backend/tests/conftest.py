import os

# Set required env vars before any app module is imported so pydantic-settings
# doesn't raise a ValidationError during test collection.
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("ELEVENLABS_API_KEY", "test-key")

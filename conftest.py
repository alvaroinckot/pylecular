import pytest

# Configure pytest-asyncio to use function scope for event loops
def pytest_configure(config):
    config.option.asyncio_mode = "strict"
    
    # Set default fixture loop scope to function scope to avoid deprecation warning
    config.option.asyncio_default_fixture_loop_scope = "function"

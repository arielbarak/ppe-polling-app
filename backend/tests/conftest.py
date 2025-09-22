import warnings
import pytest

def pytest_configure(config):
    """
    Configure pytest - filter out specific warnings we don't want to see
    """
    # Filter out Pydantic deprecation warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
    
    # Filter out RuntimeWarnings about coroutines not being awaited from unittest mock
    warnings.filterwarnings("ignore", category=RuntimeWarning, message="coroutine.*never awaited")
    
    # Filter out UserWarnings from Pydantic serializer
    warnings.filterwarnings("ignore", message="Pydantic serializer warnings")
"""
Shared pytest configuration for duvc-ctl tests.
Override camera selection via command line.
"""
import pytest
import os
import duvc_ctl
from typing import List, Optional

def pytest_addoption(parser):
    """Add custom command-line options."""
    parser.addoption(
        "--camera-index",
        action="store",
        default="0",
        type=int,
        help="Camera index to use for hardware tests (default: 0)"
    )

@pytest.fixture(scope="session")
def camera_index(request):
    """Get camera index from command line."""
    return request.config.getoption("--camera-index")

@pytest.fixture(scope="session")
def available_devices() -> List:
    """Get all available camera devices."""
    return duvcctl.list_devices()

@pytest.fixture(scope="session")
def test_device(available_devices, camera_index) -> Optional:
    """Get camera at specified index for testing."""
    if not available_devices:
        pytest.skip("No camera devices available")
    
    if camera_index >= len(available_devices):
        pytest.skip(f"Camera {camera_index} not available (only {len(available_devices)} found)")
    
    device = available_devices[camera_index]
    print(f"\n[TEST] Using camera {camera_index}: {device.name}")
    return device

@pytest.fixture(scope="function")
def first_device(test_device):
    """Alias for backward compatibility."""
    return test_device

@pytest.fixture(scope="function")
def first_device_path(test_device):
    """Get device path."""
    return test_device.path

import sys
import platform
from setuptools import setup

# Platform checks
if platform.system() != "Windows":
    print("ERROR: duvc-ctl only supports Windows operating systems.")
    print(f"Your platform: {platform.system()} {platform.machine()}")
    sys.exit(1)

if sys.version_info < (3, 8):
    print(f"ERROR: duvc-ctl requires Python 3.8 or newer.")
    print(f"Your Python version: {sys.version_info.major}.{sys.version_info.minor}")
    sys.exit(1)

if sys.version_info >= (3, 13):
    print(f"ERROR: duvc-ctl supports Python 3.8-3.12.")
    print(f"Your Python version: {sys.version_info.major}.{sys.version_info.minor} is not supported.")
    sys.exit(1)

# If we get here, platform is supported - proceed with normal setup
setup()

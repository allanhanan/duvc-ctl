import sys
import platform
import os

# Platform checks BEFORE any imports
if platform.system() != "Windows":
    print("\n" + "="*60)
    print("ERROR: duvc-ctl only supports Windows operating systems.")
    print(f"Your platform: {platform.system()} {platform.machine()}")
    print("To force installation from source: pip install --no-binary=duvc-ctl duvc-ctl")
    print("="*60 + "\n")
    # Exit before setuptools/scikit-build get involved
    os._exit(1)

if sys.version_info < (3, 8) or sys.version_info >= (3, 13):
    print("\n" + "="*60)
    print("ERROR: duvc-ctl requires Python 3.8-3.12.")
    print(f"Your Python: {sys.version_info.major}.{sys.version_info.minor}")
    print("="*60 + "\n")
    os._exit(1)

# Only proceed if platform is supported (Windows)
print("Platform check passed - proceeding with build...")

# For Windows: Don't call setup() - let scikit-build-core handle the building
# The os._exit() calls above ensure this only runs on supported platforms

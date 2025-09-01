"""
setup.py for duvc-ctl

This is a legacy setup.py for compatibility with older build systems.
Modern builds should use pyproject.toml and scikit-build-core.
"""

from skbuild import setup
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="duvc-ctl",
    version="2.0.0",
    author="allanhanan",
    author_email="allan.hanan04@gmail.com",
    description="DirectShow UVC Camera Control Library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/allanhanan/duvc-ctl",
    license="MIT",
    packages=["duvc_ctl"],
    package_dir={"duvc_ctl": "duvc_ctl"},
    cmake_args=[
        "-DDUVC_BUILD_PYTHON=ON",
        "-DDUVC_BUILD_CLI=OFF",
        "-DDUVC_BUILD_STATIC=ON",
    ],
    cmake_install_dir="duvc_ctl",
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: C++",
        "Topic :: Multimedia :: Video",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="camera uvc directshow ptz video control webcam",
    zip_safe=False,
)

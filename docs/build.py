#!/usr/bin/env python3

"""
Documentation build automation script for duvc-ctl.

This script handles building both Sphinx and Doxygen documentation with proper
dependency management, error handling, and build optimization.

Usage:
python docs/build.py [options]

Examples:
python docs/build.py # Build all documentation
python docs/build.py --sphinx-only # Build only Sphinx docs
python docs/build.py --doxygen-only # Build only Doxygen docs
python docs/build.py --clean # Clean build (remove cache)
python docs/build.py --parallel 4 # Use 4 parallel processes
python docs/build.py --watch # Watch for changes and rebuild
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

# Color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'

def print_status(message: str, status: str = "INFO") -> None:
    """Print formatted status message."""
    color_map = {
        "INFO": Colors.BLUE,
        "SUCCESS": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "BUILDING": Colors.CYAN
    }
    color = color_map.get(status, Colors.RESET)
    print(f"{color}[{status}]{Colors.RESET} {message}")

def find_project_root() -> Path:
    """Find the project root directory."""
    script_dir = Path(__file__).parent.absolute()
    current = script_dir
    while current != current.parent:
        if (current / "CMakeLists.txt").exists():
            return current
        if (current / "duvc-ctl").is_dir() or (current / "include").is_dir():
            return current
        current = current.parent
    return script_dir.parent

def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if required dependencies are available."""
    missing = []
    # Check Python dependencies
    try:
        import sphinx  # noqa
    except ImportError:
        missing.append("sphinx (pip install sphinx)")
    # Check for Doxygen
    try:
        subprocess.run(["doxygen", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("doxygen (https://doxygen.nl/download.html)")
    # Check for Graphviz (for diagrams)
    try:
        subprocess.run(["dot", "-V"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("graphviz (https://graphviz.org/download/)")
    return len(missing) == 0, missing

def install_sphinx_requirements(docs_dir: Path) -> bool:
    """Install Sphinx requirements if requirements.txt exists."""
    requirements_file = docs_dir / "sphinx" / "requirements.txt"
    if not requirements_file.exists():
        print_status("No requirements.txt found, skipping dependency installation", "WARNING")
        return True
    try:
        print_status("Installing Sphinx requirements...", "BUILDING")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, capture_output=True)
        print_status("Requirements installed successfully", "SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print_status(f"Failed to install requirements: {e}", "ERROR")
        return False

def clean_build_dirs(docs_dir: Path) -> None:
    """Clean build directories."""
    build_dir = docs_dir / "build"
    if build_dir.exists():
        print_status("Cleaning build directory...", "BUILDING")
        shutil.rmtree(build_dir)
        print_status("Build directory cleaned", "SUCCESS")
    else:
        print_status("Build directory already clean", "INFO")

def build_doxygen(docs_dir: Path, project_root: Path) -> bool:
    """Build Doxygen documentation."""
    doxygen_dir = docs_dir / "doxygen"
    doxyfile = doxygen_dir / "Doxyfile"
    output_dir = docs_dir / "build" / "doxygen"
    if not doxyfile.exists():
        print_status("Doxyfile not found, skipping Doxygen build", "WARNING")
        return True
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        print_status("Building Doxygen documentation...", "BUILDING")
        # Set environment variables for Doxygen
        env = os.environ.copy()
        env["PROJECT_ROOT"] = str(project_root)
        env["OUTPUT_DIRECTORY"] = str(output_dir)
        result = subprocess.run([
            "doxygen", str(doxyfile)
        ], cwd=doxygen_dir, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            print_status("Doxygen build failed:", "ERROR")
            print(result.stderr)
            return False
        print_status("Doxygen documentation built successfully", "SUCCESS")
        return True
    except Exception as e:
        print_status(f"Doxygen build error: {e}", "ERROR")
        return False

def build_sphinx(docs_dir: Path, parallel_jobs: int = 1, builder: str = "html") -> bool:
    """Build Sphinx documentation."""
    sphinx_dir = docs_dir / "sphinx"
    output_dir = docs_dir / "build" / "sphinx"
    doctrees_dir = docs_dir / "build" / "doctrees"
    if not sphinx_dir.exists():
        print_status("Sphinx source directory not found", "ERROR")
        return False
    # Ensure output directories exist
    output_dir.mkdir(parents=True, exist_ok=True)
    doctrees_dir.mkdir(parents=True, exist_ok=True)
    try:
        print_status(f"Building Sphinx documentation ({builder})...", "BUILDING")
        cmd = [
            sys.executable, "-m", "sphinx",
            "-b", builder,
            "-d", str(doctrees_dir),
            str(sphinx_dir), str(output_dir)
        ]
        # Add parallel processing if specified
        if parallel_jobs > 1:
            cmd.extend(["-j", str(parallel_jobs)])
        # Add verbosity and warning options
        cmd.extend(["-v", "-W", "--keep-going"])
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print_status("Sphinx build failed:", "ERROR")
            print(result.stdout)
            print(result.stderr)
            return False
        print_status("Sphinx documentation built successfully", "SUCCESS")
        # Show any warnings
        if "warning" in result.stdout.lower():
            print_status("Build completed with warnings:", "WARNING")
            for line in result.stdout.split('\n'):
                if 'warning' in line.lower():
                    print(f" {line}")
        return True
    except Exception as e:
        print_status(f"Sphinx build error: {e}", "ERROR")
        return False

def create_index_html(docs_dir: Path) -> None:
    """Create a unified index.html that links to both documentation sets."""
    build_dir = docs_dir / "build"
    index_file = build_dir / "index.html"
    html_content = """
    <html>
    <head>
        <title>duvc-ctl Documentation</title>
    </head>
    <body>
        <h1>Windows DirectShow UVC Camera Control Library</h1>
        <p>Version 2.0.0</p>
        
        <h2>User Guide and API Reference</h2>
        <a href="sphinx/index.html">Complete user guide, API reference, examples, and tutorials for all language bindings (Python, C, C++).</a>
        
        <h2>Doxygen API Reference</h2>
        <a href="doxygen/html/index.html">Detailed C++ API documentation generated from source code with class hierarchies and member details.</a>
        
        <p>Built with Sphinx and Doxygen</p>
    </body>
    </html>
    """
    with open(index_file, 'w') as f:
        f.write(html_content)
    print_status(f"Created unified index.html at {index_file}", "SUCCESS")

def watch_and_rebuild(docs_dir: Path, project_root: Path, parallel_jobs: int) -> None:
    """Watch for changes and rebuild (requires sphinx-autobuild)."""
    try:
        from sphinx_autobuild import main as autobuild_main
    except ImportError:
        print_status("sphinx-autobuild not installed. Install with 'pip install sphinx-autobuild'", "ERROR")
        return
    
    # First, build Doxygen
    if not build_doxygen(docs_dir, project_root):
        print_status("Initial Doxygen build failed. Watching Sphinx only.", "WARNING")
    
    # Then run autobuild for Sphinx
    sphinx_dir = str(docs_dir / "sphinx")
    output_dir = str(docs_dir / "build" / "sphinx")
    
    print_status("Starting live-reload server...", "BUILDING")
    sys.argv = [sys.argv[0], sphinx_dir, output_dir, "-j", str(parallel_jobs)]
    autobuild_main()

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build duvc-ctl documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--sphinx-only", action="store_true",
                        help="Build only Sphinx documentation")
    parser.add_argument("--doxygen-only", action="store_true",
                        help="Build only Doxygen documentation")
    parser.add_argument("--clean", action="store_true",
                        help="Clean build directories before building")
    parser.add_argument("--parallel", type=int, default=1,
                        help="Number of parallel processes for Sphinx")
    parser.add_argument("--watch", action="store_true",
                        help="Watch for changes and rebuild automatically")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show verbose output")
    
    args = parser.parse_args()
    
    # Conflicting options check
    if args.sphinx_only and args.doxygen_only:
        print_status("Cannot specify both --sphinx-only and --doxygen-only", "ERROR")
        return 1
    
    # Find directories
    project_root = find_project_root()
    docs_dir = project_root / "docs"
    if not docs_dir.exists():
        print_status(f"Documentation directory not found: {docs_dir}", "ERROR")
        return 1
    
    # Check dependencies
    deps_ok, missing = check_dependencies()
    if not deps_ok:
        print_status("Missing dependencies:", "ERROR")
        for dep in missing:
            print(f" - {dep}")
        return 1
    
    # Install Sphinx requirements
    if not args.doxygen_only:
        if not install_sphinx_requirements(docs_dir):
            print_status("Failed to install Sphinx requirements", "ERROR")
            return 1
    
    # Watch mode
    if args.watch:
        watch_and_rebuild(docs_dir, project_root, args.parallel)
        return 0
    
    # Clean if requested
    if args.clean:
        clean_build_dirs(docs_dir)
    
    success = True
    
    # Build Doxygen first (Sphinx depends on its XML)
    if not args.sphinx_only:
        if not build_doxygen(docs_dir, project_root):
            print_status("Doxygen build failed", "ERROR")
            success = False
    
    # Build Sphinx if Doxygen succeeded or if only Sphinx requested
    if not args.doxygen_only and success:
        if not build_sphinx(docs_dir, args.parallel):
            print_status("Sphinx build failed", "ERROR")
            success = False
    
    # Create unified index if both were built
    if success and not args.sphinx_only and not args.doxygen_only:
        create_index_html(docs_dir)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

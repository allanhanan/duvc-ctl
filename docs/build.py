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
    """Clean build directories - calls clean.py."""
    from clean import clean_documentation
    
    clean_documentation(
        docs_dir,
        sphinx_only=False,
        doxygen_only=False,
        dry_run=False,
        verbose=True
    )


def copy_api_docs(docs_dir: Path) -> bool:
    """Copy API documentation folders (with subfolders) into sphinx/api for toctree linking."""
    api_dest_dir = docs_dir / "sphinx" / "api"
    
    # Create destination if it doesn't exist
    api_dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Folders to copy: c, c++, cli, python
    api_dirs = {
        "c": docs_dir / "c",
        "cpp": docs_dir / "c++",
        "cli": docs_dir / "cli",
        "python": docs_dir / "python",
    }
    
    try:
        for name, source_dir in api_dirs.items():
            if source_dir.exists():
                dest_dir = api_dest_dir / name
                # Remove existing if present
                if dest_dir.exists():
                    shutil.rmtree(dest_dir)
                # Copy entire folder with all subfolders
                shutil.copytree(source_dir, dest_dir)
                print_status(f"Copied {name} API docs with all subfolders", "INFO")
            else:
                print_status(f"Source not found: {source_dir}", "WARNING")
        
        print_status("API documentation copied to sphinx/api", "SUCCESS")
        return True
    except Exception as e:
        print_status(f"Failed to copy API docs: {e}", "ERROR")
        return False

from pathlib import Path

# Low-level function
def inject_sphinx_toc(index_md, section_glob, caption=None):
    """
    Appends a hidden MyST toctree to index_md if not present.
    section_glob: glob pattern for section files, e.g., "sections/*.md"
    caption: optional toctree caption text
    """
    index_md = Path(index_md)
    if not index_md.exists():
        return

    # Read content of the file to check for existing toctree
    with open(index_md, encoding="utf-8") as f:
        content = f.read()

    # Check if the toctree is already present
    if "```{toctree}" in content:
        return  # Do not add the toctree again if it is already present

    # Find all section files matching the glob pattern
    section_files = sorted(index_md.parent.glob(section_glob))
    toctree = []
    toctree.append("```{toctree}")
    toctree.append(":maxdepth: 2")
    toctree.append(":hidden:")
    if caption:
        toctree.append(f":caption: {caption}")
    toctree.append("")  # Blank line before section entries

    # Add all section file paths (relative to the index_md file)
    for sf in section_files:
        toctree.append(f"sections/{sf.stem}") # Use the relative file stem (no need for "sections/")

    toctree.append("```")  # Close the toctree block
    toctree_block = "\n" + "\n".join(toctree) + "\n"

    # Append the generated toctree to the index.md file
    with open(index_md, "a", encoding="utf-8") as f:
        f.write(toctree_block)


# High-level function
def inject_api_toctrees(docs_dir: Path) -> bool:
    """Inject toctree blocks into API index.md files for Sphinx sidebar."""
    try:
        api_dest_dir = docs_dir / "sphinx" / "api"
        
        # Inject C++ toctree
        inject_sphinx_toc(
            api_dest_dir / "cpp" / "index.md",
            "sections/*.md",
            caption="C++ Documentation"
        )
        
        # Inject Python toctree
        inject_sphinx_toc(
            api_dest_dir / "python" / "index.md",
            "sections/*.md",
            caption="Python Documentation"
        )
        
        print_status("Injected toctrees into API documentation", "SUCCESS")
        return True
    
    except Exception as e:
        print_status(f"Toctree injection error: {e}", "WARNING")
        return False



def build_doxygen(docs_dir: Path, project_root: Path) -> bool:
    """Build Doxygen documentation."""
    doxygen_dir = docs_dir / "doxygen"
    doxyfile_template = doxygen_dir / "Doxyfile.in"
    doxyfile = doxygen_dir / "Doxyfile"
    output_dir = docs_dir / "build" / "doxygen"
    
    # Expand template if needed
    if doxyfile_template.exists() and not doxyfile.exists():
        print_status("Expanding Doxyfile.in template...", "BUILDING")
        with open(doxyfile_template, 'r') as f:
            content = f.read()
        
        # Replace CMake-style placeholders
        content = content.replace("@PROJECT_SOURCE_DIR@", str(project_root))
        content = content.replace("@PROJECT_BINARY_DIR@", str(project_root))
        content = content.replace("@PROJECT_NAME@", "duvc-ctl")
        content = content.replace("@PROJECT_VERSION@", "2.0.0")
        content = content.replace("@DOXYGEN_SOURCE_DIR@", str(doxygen_dir))
        
        with open(doxyfile, 'w') as f:
            f.write(content)
        print_status("Doxyfile generated from template", "SUCCESS")
    
    if not doxyfile.exists():
        print_status("Doxyfile not found, skipping Doxygen build", "WARNING")
        return True
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        print_status("Building Doxygen documentation...", "BUILDING")
        result = subprocess.run(
            ["doxygen", str(doxyfile)],
            cwd=doxygen_dir,
            capture_output=True,
            text=True
        )
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
        cmd.extend(["-v", "--keep-going"])
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
    # Copy API docs for Sphinx
    if not args.doxygen_only and success:
        if not copy_api_docs(docs_dir):
            success = False
    
    # Inject toctrees into API docs
        if not inject_api_toctrees(docs_dir):
            print_status("Failed to inject toctrees", "WARNING")
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

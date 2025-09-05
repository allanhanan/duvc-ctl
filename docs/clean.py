#!/usr/bin/env python3
"""
Documentation cleanup automation script for duvc-ctl.

This script removes all build artifacts and temporary files generated during
documentation building, including Sphinx and Doxygen outputs.

Usage:
    python docs/clean.py [options]

Examples:
    python docs/clean.py                    # Clean all artifacts
    python docs/clean.py --dry-run          # Show what would be deleted
    python docs/clean.py --verbose          # Verbose output
    python docs/clean.py --sphinx-only      # Clean only Sphinx artifacts
    python docs/clean.py --doxygen-only     # Clean only Doxygen artifacts
"""

import argparse
import os
import shutil
import sys
import time
from pathlib import Path
from typing import List, Optional

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
        "CLEANING": Colors.CYAN
    }
    color = color_map.get(status, Colors.RESET)
    print(f"{color}[{status}]{Colors.RESET} {message}")

def find_project_root() -> Path:
    """Find the project root directory."""
    script_dir = Path(__file__).parent.absolute()
    
    # Look for CMakeLists.txt or other project markers
    current = script_dir
    while current != current.parent:
        if (current / "CMakeLists.txt").exists():
            return current
        if (current / "duvc-ctl").is_dir() or (current / "include").is_dir():
            return current
        current = current.parent
    
    # Fallback to script directory's parent
    return script_dir.parent

def get_size_human_readable(size_bytes: int) -> str:
    """Convert bytes to human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def calculate_directory_size(directory: Path) -> int:
    """Calculate total size of directory and its contents."""
    total_size = 0
    try:
        for entry in directory.rglob('*'):
            if entry.is_file():
                total_size += entry.stat().st_size
    except (OSError, PermissionError):
        pass
    return total_size

def remove_path(path: Path, dry_run: bool = False, verbose: bool = False) -> tuple[bool, int]:
    """
    Remove a file or directory.
    
    Returns:
        tuple: (success, size_freed)
    """
    if not path.exists():
        if verbose:
            print_status(f"Path not found (skipped): {path}", "INFO")
        return True, 0
    
    try:
        # Calculate size before removal
        if path.is_file():
            size_freed = path.stat().st_size
            item_type = "file"
        else:
            size_freed = calculate_directory_size(path)
            item_type = "directory"
        
        if dry_run:
            print_status(f"Would remove {item_type}: {path} ({get_size_human_readable(size_freed)})", "WARNING")
            return True, size_freed
        
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
        
        print_status(f"Removed {item_type}: {path} ({get_size_human_readable(size_freed)})", "SUCCESS")
        return True, size_freed
        
    except PermissionError:
        print_status(f"Permission denied: {path}", "ERROR")
        return False, 0
    except OSError as e:
        print_status(f"Failed to remove {path}: {e}", "ERROR")
        return False, 0
    except Exception as e:
        print_status(f"Unexpected error removing {path}: {e}", "ERROR")
        return False, 0

def get_sphinx_cleanup_paths(docs_dir: Path) -> List[Path]:
    """Get list of Sphinx-related paths to clean."""
    sphinx_dir = docs_dir / "sphinx"
    
    paths = [
        # Main Sphinx build directory
        sphinx_dir / "_build",
        
        # Sphinx cache directories
        sphinx_dir / ".doctrees",
        sphinx_dir / "_doctrees",
        
        # Auto-generated files
        sphinx_dir / "_autosummary",
        
        # Temporary files
        sphinx_dir / ".buildinfo",
    ]
    
    # Add any .pyc files in sphinx directory
    for pyc_file in sphinx_dir.rglob("*.pyc"):
        paths.append(pyc_file)
    
    # Add __pycache__ directories
    for pycache_dir in sphinx_dir.rglob("__pycache__"):
        paths.append(pycache_dir)
    
    return paths

def get_doxygen_cleanup_paths(docs_dir: Path) -> List[Path]:
    """Get list of Doxygen-related paths to clean."""
    doxygen_dir = docs_dir / "doxygen"
    
    paths = [
        # Doxygen output directories
        doxygen_dir / "html",
        doxygen_dir / "latex",
        doxygen_dir / "man",
        doxygen_dir / "rtf",
        doxygen_dir / "xml",
        
        # Doxygen temporary files
        doxygen_dir / "doxygen_sqlite3.db",
        doxygen_dir / "doxygen.log",
    ]
    
    return paths

def get_general_cleanup_paths(docs_dir: Path) -> List[Path]:
    """Get list of general cleanup paths."""
    paths = [
        # Main build directory
        docs_dir / "build",
        
        # Temporary files in docs root
        docs_dir / ".buildinfo",
        docs_dir / "warnings.log",
    ]
    
    # Add any .tmp files
    for tmp_file in docs_dir.rglob("*.tmp"):
        paths.append(tmp_file)
    
    # Add any .bak files
    for bak_file in docs_dir.rglob("*.bak"):
        paths.append(bak_file)
    
    return paths

def clean_documentation(docs_dir: Path, 
                       sphinx_only: bool = False,
                       doxygen_only: bool = False,
                       dry_run: bool = False,
                       verbose: bool = False) -> tuple[int, int]:
    """
    Clean documentation build artifacts.
    
    Returns:
        tuple: (files_processed, total_size_freed)
    """
    print_status(f"Documentation directory: {docs_dir}", "INFO")
    
    # Collect all paths to clean
    all_paths = []
    
    if not doxygen_only:
        all_paths.extend(get_sphinx_cleanup_paths(docs_dir))
    
    if not sphinx_only:
        all_paths.extend(get_doxygen_cleanup_paths(docs_dir))
    
    if not sphinx_only and not doxygen_only:
        all_paths.extend(get_general_cleanup_paths(docs_dir))
    
    # Remove duplicates while preserving order
    unique_paths = []
    seen = set()
    for path in all_paths:
        path_str = str(path)
        if path_str not in seen:
            unique_paths.append(path)
            seen.add(path_str)
    
    if not unique_paths:
        print_status("No cleanup paths found", "INFO")
        return 0, 0
    
    print_status(f"Processing {len(unique_paths)} paths...", "INFO")
    
    # Process each path
    total_size_freed = 0
    files_processed = 0
    errors = 0
    
    for path in unique_paths:
        success, size_freed = remove_path(path, dry_run, verbose)
        if success:
            files_processed += 1
            total_size_freed += size_freed
        else:
            errors += 1
    
    # Summary
    if dry_run:
        print_status(f"Dry run completed: {files_processed} items would be removed", "INFO")
        print_status(f"Total space that would be freed: {get_size_human_readable(total_size_freed)}", "INFO")
    else:
        if errors > 0:
            print_status(f"Cleanup completed with {errors} errors", "WARNING")
        else:
            print_status("Cleanup completed successfully", "SUCCESS")
        
        if files_processed > 0:
            print_status(f"Removed {files_processed} items", "INFO")
            print_status(f"Total space freed: {get_size_human_readable(total_size_freed)}", "INFO")
        else:
            print_status("No files were removed (already clean)", "INFO")
    
    return files_processed, total_size_freed

def create_gitignore_if_missing(docs_dir: Path) -> None:
    """Create .gitignore file for build directories if it doesn't exist."""
    gitignore_path = docs_dir / ".gitignore"
    
    if gitignore_path.exists():
        return
    
    gitignore_content = """# Documentation build artifacts
build/
sphinx/_build/
sphinx/.doctrees/
sphinx/_doctrees/
sphinx/_autosummary/
doxygen/html/
doxygen/latex/
doxygen/man/
doxygen/rtf/
doxygen/xml/
doxygen/doxygen_sqlite3.db
doxygen/doxygen.log

# Temporary files
*.tmp
*.bak
.buildinfo
warnings.log

# Python cache
__pycache__/
*.pyc
*.pyo
"""
    
    try:
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print_status(f"Created .gitignore: {gitignore_path}", "SUCCESS")
    except Exception as e:
        print_status(f"Failed to create .gitignore: {e}", "WARNING")

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Clean duvc-ctl documentation build artifacts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--sphinx-only", action="store_true",
                       help="Clean only Sphinx build artifacts")
    parser.add_argument("--doxygen-only", action="store_true",
                       help="Clean only Doxygen build artifacts")
    parser.add_argument("--dry-run", "-n", action="store_true",
                       help="Show what would be deleted without actually deleting")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Show verbose output")
    parser.add_argument("--create-gitignore", action="store_true",
                       help="Create .gitignore file for build artifacts")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Suppress all output except errors")
    
    args = parser.parse_args()
    
    # Conflicting options
    if args.sphinx_only and args.doxygen_only:
        print_status("Cannot specify both --sphinx-only and --doxygen-only", "ERROR")
        return 1
    
    # Find project directories
    project_root = find_project_root()
    docs_dir = project_root / "docs"
    
    if not docs_dir.exists():
        print_status(f"Documentation directory not found: {docs_dir}", "ERROR")
        return 1
    
    # Redirect output if quiet
    if args.quiet:
        import io
        sys.stdout = io.StringIO()
    
    try:
        # Create .gitignore if requested
        if args.create_gitignore:
            create_gitignore_if_missing(docs_dir)
        
        # Perform cleanup
        start_time = time.time()
        
        files_processed, total_size_freed = clean_documentation(
            docs_dir,
            sphinx_only=args.sphinx_only,
            doxygen_only=args.doxygen_only,
            dry_run=args.dry_run,
            verbose=args.verbose
        )
        
        end_time = time.time()
        
        if args.verbose:
            print_status(f"Cleanup took {end_time - start_time:.2f} seconds", "INFO")
        
        return 0
        
    except KeyboardInterrupt:
        print_status("Cleanup interrupted by user", "WARNING")
        return 1
    except Exception as e:
        print_status(f"Unexpected error: {e}", "ERROR")
        return 1
    finally:
        # Restore stdout if it was redirected
        if args.quiet:
            sys.stdout = sys.__stdout__

if __name__ == "__main__":
    sys.exit(main())

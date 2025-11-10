#!/usr/bin/env python3
"""
Dynamic Sphinx toctree injector - generates toctree directives from section files.

Place this file at: docs/sphinx/scripts/generate_toctree.py
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def find_section_files(sections_dir: Path) -> List[Path]:
    """Find all numbered section markdown files (01_*.md, 02_*.md, etc)."""
    pattern = re.compile(r'^\d+_.*\.md$')
    files = sorted([f for f in sections_dir.glob('*.md') if pattern.match(f.name)])
    return files


def generate_toctree_file(sections_dir: Path, output_file: Path, title: str) -> None:
    """
    Generate a toctree markdown file from section files in a directory.
    
    Args:
        sections_dir: Directory containing numbered section files (01_*.md, etc)
        output_file: Output path for generated _toctree.md file
        title: Caption for the toctree directive
    """
    section_files = find_section_files(sections_dir)
    
    if not section_files:
        return
    
    lines = [
        f"# {title}\n",
        "```{{toctree}}",
        ":maxdepth: 2",
        f":caption: {title}",
        ""
    ]
    
    # Add relative paths to sections (without .md extension)
    for section_file in section_files:
        section_name = section_file.stem  # Remove .md extension
        lines.append(f"sections/{section_name}")
    
    lines.append("```\n")
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def generate_toctree_for_api(app, config) -> None:
    """
    Sphinx event handler for config-inited event.
    Generates toctree files for C++ and Python APIs.
    
    This function is called automatically by Sphinx during initialization.
    Connect it in conf.py: app.connect('config-inited', generate_toctree_for_api)
    """
    docs_dir = Path(app.confdir).parent
    
    # Generate C++ toctree
    cpp_sections_dir = docs_dir / 'api' / 'cpp' / 'sections'
    if cpp_sections_dir.exists():
        cpp_output = docs_dir / 'api' / 'cpp' / '_toctree.md'
        generate_toctree_file(cpp_sections_dir, cpp_output, "C++ API Documentation")
        num_files = len(find_section_files(cpp_sections_dir))
        print(f"[toctree-injector] Generated C++ toctree with {num_files} sections")
    
    # Generate Python toctree
    python_sections_dir = docs_dir / 'api' / 'python' / 'sections'
    if python_sections_dir.exists():
        python_output = docs_dir / 'api' / 'python' / '_toctree.md'
        generate_toctree_file(python_sections_dir, python_output, "Python API Documentation")
        num_files = len(find_section_files(python_sections_dir))
        print(f"[toctree-injector] Generated Python toctree with {num_files} sections")


if __name__ == "__main__":
    # For manual testing from docs/sphinx/ directory
    docs_dir = Path(__file__).parent.parent
    
    cpp_sections = docs_dir / 'api' / 'cpp' / 'sections'
    if cpp_sections.exists():
        generate_toctree_file(cpp_sections, docs_dir / 'api' / 'cpp' / '_toctree.md', "C++")
        print(f"✓ Generated C++ toctree with {len(find_section_files(cpp_sections))} sections")
    
    python_sections = docs_dir / 'api' / 'python' / 'sections'
    if python_sections.exists():
        generate_toctree_file(python_sections, docs_dir / 'api' / 'python' / '_toctree.md', "Python")
        print(f"✓ Generated Python toctree with {len(find_section_files(python_sections))} sections")

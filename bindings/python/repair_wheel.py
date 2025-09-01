import sys
import subprocess
import os
from pathlib import Path

def find_dll_in_bin_release(build_dir: Path, dll_name: str = 'duvc-core.dll') -> str:
    """Search specifically in bin/Release for the DLL."""
    search_path = build_dir / 'bin' / 'Release'
    dll_path = search_path / dll_name
    if dll_path.exists():
        return str(dll_path)
    raise FileNotFoundError(f"Could not find {dll_name} in {search_path}")

if __name__ == "__main__":
    wheel = sys.argv[1]  # {wheel}
    dest_dir = sys.argv[2]  # {dest_dir}
    project_dir = Path(os.environ.get('CIBW_PROJECT_DIR', Path(__file__).parent))

    # Extract wheel tag (e.g., 'cp38-cp38-win_amd64') from filename
    parts = Path(wheel).stem.split('-')
    wheel_tag = '-'.join(parts[2:])  # After name and version

    # Construct build dir (matches cibuildwheel/local patterns)
    build_dir = project_dir / 'build' / wheel_tag

    # Find DLL in bin/Release
    dll_full_path = find_dll_in_bin_release(build_dir)
    dll_dir = os.path.dirname(dll_full_path)

    # Run delvewheel to bundle and repair
    cmd = [
        'delvewheel', 'repair',
        '--add-path', dll_dir,
        '--no-mangle-all',  # Safe default
        '-w', dest_dir,
        '-v',  # Verbose for logs
        wheel
    ]
    subprocess.check_call(cmd)
    print(f"Repaired wheel using DLL from: {dll_full_path}")

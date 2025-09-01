import sys
import subprocess
import os
from pathlib import Path
import shutil

def find_dll_in_bin_release(build_dir: Path, dll_name: str = 'duvc-core.dll') -> str:
    search_path = build_dir / 'bin' / 'Release'
    dll_path = search_path / dll_name
    if dll_path.exists():
        return str(dll_path)
    raise FileNotFoundError(f"Could not find {dll_name} in {search_path}")

if __name__ == "__main__":
    print("=== repair_wheel.py starting ===")
    print("Args:", sys.argv)
    print("CWD:", os.getcwd())
    wheel, dest_dir = sys.argv[1:3]
    project_dir = Path(os.environ.get('CIBW_PROJECT_DIR', Path(__file__).parent))
    wheel_tag = '-'.join(Path(wheel).stem.split('-')[2:])
    build_dir = project_dir / 'build' / wheel_tag

    try:
        dll_full_path = find_dll_in_bin_release(build_dir)
    except FileNotFoundError as e:
        print("ERROR:", e)
        sys.exit(1)
    dll_dir = os.path.dirname(dll_full_path)
    print(f"Using DLL from: {dll_full_path}")

    # Copy wheel as a fallback in case delvewheel fails
    shutil.copy(wheel, dest_dir)
    print(f"Copied wheel to {dest_dir}")

    cmd = [
        'delvewheel', 'repair',
        '--add-path', dll_dir,
        '--no-mangle-all',
        '-w', dest_dir,
        '-v',
        wheel
    ]

    try:
        subprocess.check_call(cmd)
        print("delvewheel repair succeeded")
    except FileNotFoundError:
        print("WARNING: delvewheel not installed—wheel copied only")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: delvewheel failed with code {e.returncode}")
        sys.exit(e.returncode)

    print("=== repair_wheel.py finished ===")

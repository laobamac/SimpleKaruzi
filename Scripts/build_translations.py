import os
import sys
import subprocess
import glob
import shutil
from pathlib import Path

def find_qt_tool(tool_name):
    if shutil.which(tool_name):
        return tool_name
        
    python_root = Path(sys.executable).parent
    possible_paths = [
        python_root / tool_name,
        python_root / f"{tool_name}.exe",
        python_root / "Scripts" / tool_name,
        python_root / "Scripts" / f"{tool_name}.exe",
    ]
    
    for lib_path in sys.path:
        qt_bin = Path(lib_path) / "qt6_applications" / "Qt" / "bin"
        if qt_bin.exists():
            possible_paths.append(qt_bin / tool_name)
            possible_paths.append(qt_bin / f"{tool_name}.exe")
            
    for p in possible_paths:
        if p.exists():
            return str(p)
            
    return None

def run_command(cmd):
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)

def main():
    root_dir = Path(__file__).parent.parent
    scripts_dir = root_dir / "Scripts"
    trans_dir = root_dir / "Translations"
    
    sources = []
    sources.extend(glob.glob(str(scripts_dir / "pages" / "*.py")))
    sources.extend(glob.glob(str(scripts_dir / "*.py")))
    sources.append(str(root_dir / "SimpleKaruzi.py"))
    
    pylupdate = find_qt_tool("pylupdate6")
    if not pylupdate:
        pylupdate = [sys.executable, "-m", "PyQt6.lupdate"]
        pylupdate = "pylupdate6"

    if isinstance(pylupdate, str):
        pylupdate = [pylupdate]

    print("--- Updating Translations ---")
    for lang in ["en_US", "zh_CN"]:
        ts_file = trans_dir / f"{lang}.ts"
        cmd = pylupdate + sources + ["-ts", str(ts_file)]
        run_command(cmd)

    print("--- Auto Translating ---")
    auto_script = scripts_dir / "auto_translate_ts.py"
    if auto_script.exists():
        run_command([sys.executable, str(auto_script)])

    lrelease = find_qt_tool("lrelease")
    if not lrelease:
        print("Warning: lrelease not found. Searching deeper...")
        print("Could not find lrelease. Skipping compilation.")
        return

    print(f"Found lrelease at: {lrelease}")
    
    print("--- Compiling Translations ---")
    ts_files = [str(trans_dir / "en_US.ts"), str(trans_dir / "zh_CN.ts")]
    run_command([lrelease] + ts_files)

if __name__ == "__main__":
    main()

"""Build the C++ greedy solver extension.

Usage:
    python scripts/build_cpp.py          # build
    python scripts/build_cpp.py --clean  # clean build directory
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CPP_DIR = ROOT / "cpp"
BUILD_DIR = ROOT / "build" / "cpp"
TARGET_DIR = ROOT / "vrptw" / "algorithm" / "_solver" / "greedy_cpp_solver"


def build():
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    # Find WinLibs MinGW and prepend to PATH (avoids Anaconda's old GCC 5.3)
    env = os.environ.copy()
    mingw_bin = _find_mingw()
    if mingw_bin:
        env["PATH"] = str(mingw_bin) + os.pathsep + env.get("PATH", "")
        print(f"  using compiler: {mingw_bin / 'g++.exe'}")

    # Configure
    subprocess.run(
        [
            "cmake",
            str(CPP_DIR),
            "-G",
            "Ninja",
            "-DCMAKE_BUILD_TYPE=Release",
            f"-Dpybind11_DIR={_find_pybind11()}",
        ],
        cwd=BUILD_DIR,
        check=True,
        env=env,
    )

    # Build
    subprocess.run(["cmake", "--build", "."], cwd=BUILD_DIR, check=True, env=env)

    # Copy extension module artifacts to the Python package directory
    for pattern in ("_greedy_cpp*.pyd", "_greedy_cpp*.so"):
        for artifact in BUILD_DIR.glob(f"**/{pattern}"):
            dest = TARGET_DIR / artifact.name
            shutil.copy2(artifact, dest)
            print(f"  copied: {artifact.name} -> {dest}")

    # Copy MinGW runtime DLLs (needed on Windows when built with MinGW-w64)
    if mingw_bin:
        for dll_name in ("libstdc++-6.dll", "libgcc_s_seh-1.dll", "libwinpthread-1.dll"):
            dll_src = mingw_bin / dll_name
            if dll_src.exists():
                shutil.copy2(dll_src, TARGET_DIR / dll_name)
                print(f"  copied: {dll_name} -> {TARGET_DIR}")


def _find_pybind11() -> str:
    """Find pybind11 cmake config directory from the installed Python package."""
    import pybind11

    return str(Path(pybind11.get_cmake_dir()))


def _find_mingw() -> Path | None:
    """Find WinLibs MinGW-w64 bin directory (installed via winget)."""
    winget_packages = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    if not winget_packages.exists():
        return None
    for d in winget_packages.iterdir():
        if d.name.startswith("BrechtSanders"):
            mingw_bin = d / "mingw64" / "bin"
            if (mingw_bin / "g++.exe").exists():
                return mingw_bin
    return None


def clean():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print(f"Removed {BUILD_DIR}")


if __name__ == "__main__":
    if "--clean" in sys.argv:
        clean()
    else:
        build()

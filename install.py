"""Creates .venv next to this file, installs the dependencies and writes the launcher:
mermaid2pptx.bat on Windows, mermaid2pptx (a shell script) on Linux and macOS.

    py install.py            runtime only             (python3 install.py on Linux/macOS)
    py install.py dev        runtime + pytest

A Python script rather than a batch file, so the folder can be mailed: mail filters
block .bat files, even inside a zip.
"""
import subprocess
import sys
import venv
from pathlib import Path

HERE = Path(__file__).resolve().parent
WINDOWS = sys.platform == "win32"
BAT = r"""@echo off
rem Runs the converter with the .venv made by install.py. Arguments are passed through.
"%~dp0.venv\Scripts\python.exe" "%~dp0mermaid2pptx.py" %*
"""
SH = """#!/bin/sh
# Runs the converter with the .venv made by install.py. Arguments are passed through.
here=$(cd "$(dirname "$0")" && pwd)
exec "$here/.venv/bin/python" "$here/mermaid2pptx.py" "$@"
"""


def main(argv: list[str]) -> int:
    if sys.version_info < (3, 10):
        hint = "winget install Python.Python.3.12" if WINDOWS else "use your package manager"
        print(f"Python 3.10 or later is required: {hint}")
        return 1
    env = HERE / ".venv"
    py = env / ("Scripts/python.exe" if WINDOWS else "bin/python")
    if not py.exists():
        venv.create(env, with_pip=True)
    req = HERE / ("requirements-dev.txt" if argv[1:2] == ["dev"] else "requirements.txt")
    pip = [str(py), "-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", str(req)]
    if subprocess.run(pip).returncode:
        return 1
    if WINDOWS:
        launcher = HERE / "mermaid2pptx.bat"
        launcher.write_bytes(BAT.replace("\n", "\r\n").encode("ascii"))
        run = launcher.name
    else:
        launcher = HERE / "mermaid2pptx"
        launcher.write_text(SH, encoding="ascii", newline="\n")
        launcher.chmod(0o755)
        run = f"./{launcher.name}"
    print(f"Ready. Convert with:  {run} diagram.mmd")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

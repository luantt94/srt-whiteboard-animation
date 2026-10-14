#!/usr/bin/env python3
"""
Bo khoi dong cho SRT Whiteboard Studio (giao dien PySide6).

Chay file nay bang Python he thong bat ky (>=3.9). No se:
  1. Goi scripts/prepare_env.py de tao/tai dung .venv cua skill va cai
     opencv-python / numpy / av / Pillow.
  2. Cai them PySide6 vao chinh .venv do (chi can cho giao dien).
  3. Mo giao dien bang trinh thong dich cua .venv, nen moi script render
     dung dung mot moi truong, khong le thuoc Python he thong.

Cach dung:
  python app/launch.py

Ghi chu: file nay dung tieng Viet khong dau o phan in ra man hinh de
tranh loi encoding khi output bi chuyen huong tren console cp1252.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREPARE = ROOT / "scripts" / "prepare_env.py"
GUI = Path(__file__).resolve().parent / "whiteboard_studio.py"


def venv_python() -> Path:
    if os.name == "nt":
        return ROOT / ".venv" / "Scripts" / "python.exe"
    return ROOT / ".venv" / "bin" / "python"


def main() -> int:
    # Script trong skill in tieng Trung; ep UTF-8 de tien trinh con khong loi
    # tren console dung codepage cp1252. Bien nay duoc ke thua xuong con.
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"

    print("=" * 60)
    print("SRT Whiteboard Studio - chuan bi moi truong")
    print("=" * 60)

    res = subprocess.run([sys.executable, str(PREPARE)], text=True)
    if res.returncode != 0:
        print("\n[loi] Khong chuan bi duoc moi truong .venv. Xem log o tren.")
        return res.returncode

    env_py = venv_python()
    if not env_py.exists():
        print(f"\n[loi] Khong tim thay trinh thong dich .venv: {env_py}")
        return 1

    check = subprocess.run([str(env_py), "-c", "import PySide6"], capture_output=True)
    if check.returncode != 0:
        print("\n[..] Cai PySide6 vao .venv (chi lan dau, co the mat vai phut) ...")
        pip = subprocess.run(
            [str(env_py), "-m", "pip", "install", "--quiet", "PySide6"], text=True
        )
        if pip.returncode != 0:
            print("[loi] Cai PySide6 that bai.")
            return pip.returncode
        print("[ok] Da cai PySide6.")

    print("\n[..] Mo giao dien ...\n")
    return subprocess.run([str(env_py), str(GUI), *sys.argv[1:]]).returncode


if __name__ == "__main__":
    sys.exit(main())

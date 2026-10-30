"""检查这台电脑能不能跑本周的项目。

用法：
    python check_env.py
"""

from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path

RESULTS: list[tuple[str, bool]] = []


def record(name: str, ok: bool, detail: str = "", fix: str = "") -> None:
    RESULTS.append((name, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))
    if not ok and fix:
        print(f"       修复：{fix}")


def main() -> int:
    print(f"Python {platform.python_version()}  ({'64 位' if sys.maxsize > 2**32 else '32 位'})")
    print(f"解释器：{sys.executable}")
    print()

    record(
        "Python 版本 >= 3.10",
        sys.version_info >= (3, 10),
        platform.python_version(),
        "装 Python 3.12，安装第一页勾选 Add python.exe to PATH",
    )

    for module in ("folium", "pandas"):
        try:
            imported = __import__(module)
            record(f"import {module}", True, getattr(imported, "__version__", "已安装"))
        except ImportError:
            record(f"import {module}", False, "未安装", "pip install -r requirements.txt")

    git = shutil.which("git")
    record("Git 可用", bool(git), git or "没找到", "装 Git，然后关掉终端重新打开")

    code = shutil.which("code")
    if not code:
        candidates = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Microsoft VS Code/Code.exe",
            Path("C:/Program Files/Microsoft VS Code/Code.exe"),
        ]
        code = next((str(p) for p in candidates if p.exists()), None)
    record("VS Code 可用", bool(code), code or "没找到", "装 VS Code，安装时勾选 Add to PATH")

    failed = [name for name, ok in RESULTS if not ok]
    print()
    if failed:
        print(f"{len(failed)} 项没通过，先修完再往下走：{'、'.join(failed)}")
        return 1

    print("全部通过。下一步：填 places.csv 的经纬度，然后 python hometown_map.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

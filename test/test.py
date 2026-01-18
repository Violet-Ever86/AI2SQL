"""
根据项目中的 import 自动生成 requirements.auto.txt 的小工具。

使用方式：
    1. 在当前虚拟环境中先安装好你项目需要的依赖（能正常运行项目即可）
    2. 在项目根目录执行：
           python generate_requirements.py
    3. 脚本会在同一目录下生成/覆盖：
           requirements.auto.txt

说明：
    - 通过静态分析 .py 文件里的 import，收集顶层模块名
    - 再用 importlib.metadata 查出这些模块对应的安装包名字和版本
    - 结果只是“候选依赖”，你可以手动对比、合并到自己的 requirements.txt
"""

from __future__ import annotations

import ast
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, Set

try:
    # Python 3.8+ 标准库
    from importlib import metadata
except ImportError:  # pragma: no cover
    import importlib_metadata as metadata  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_FILE = PROJECT_ROOT / "requirements.auto.txt"


EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode",
    "dist",
    "build",
}


def iter_python_files(root: Path) -> Iterable[Path]:
    """遍历项目中的 .py 文件（排除常见无关目录）"""
    for dirpath, dirnames, filenames in os.walk(root):
        # 过滤掉不需要的目录
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

        for name in filenames:
            if name.endswith(".py"):
                yield Path(dirpath) / name


def collect_imports(root: Path) -> Set[str]:
    """从所有 .py 文件中收集顶层 import 的包名"""
    modules: Set[str] = set()

    for py_file in iter_python_files(root):
        try:
            code = py_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # 个别文件编码异常时跳过
            continue

        try:
            tree = ast.parse(code, filename=str(py_file))
        except SyntaxError:
            # 非法语法文件（临时文件等）直接跳过
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # 只取顶层包名，如 "flask_cors" 从 "flask_cors.ext" 得来
                    top_name = alias.name.split(".")[0]
                    modules.add(top_name)
            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                top_name = node.module.split(".")[0]
                # 排除标准库里的相对导入等
                if node.level and top_name == "":
                    continue
                modules.add(top_name)

    return modules


def map_modules_to_distributions(modules: Set[str]) -> Dict[str, Set[str]]:
    """
    使用 importlib.metadata.packages_distributions 将模块名映射到安装包名。

    返回：
        {distribution_name: {module1, module2, ...}}
    """
    pkg_to_dists = metadata.packages_distributions()
    dist_to_modules: Dict[str, Set[str]] = defaultdict(set)

    for mod in modules:
        dists = pkg_to_dists.get(mod)
        if not dists:
            # 找不到映射时，先假设包名就等于模块名
            dist_to_modules[mod].add(mod)
            continue

        for dist in dists:
            dist_to_modules[dist].add(mod)

    return dist_to_modules


def build_requirements(dist_to_modules: Dict[str, Set[str]]) -> Dict[str, str]:
    """
    为每个分发包生成 `name==version` 或仅 `name`。

    返回：
        {distribution_name: "name==version" 或 "name"}
    """
    requirements: Dict[str, str] = {}
    for dist_name in sorted(dist_to_modules.keys(), key=str.lower):
        try:
            version = metadata.version(dist_name)
            requirements[dist_name] = f"{dist_name}=={version}"
        except metadata.PackageNotFoundError:
            # 当前环境没装这个包，只写名不带版本
            requirements[dist_name] = dist_name

    return requirements


def write_requirements_file(requirements: Dict[str, str]) -> None:
    """写出 requirements.auto.txt 文件"""
    lines = [
        "# 该文件由 generate_requirements.py 自动生成",
        "# 根据当前项目源码中的 import 与当前虚拟环境中已安装的包推断",
        "# 请手动检查、合并到正式 requirements.txt 中使用",
        "",
    ]
    for _, requirement in sorted(requirements.items(), key=lambda kv: kv[0].lower()):
        lines.append(requirement)

    OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    print(f"扫描项目路径: {PROJECT_ROOT}")
    modules = collect_imports(PROJECT_ROOT)
    print(f"共发现顶层 import 模块数: {len(modules)}")

    dist_to_modules = map_modules_to_distributions(modules)
    print(f"推断出可能的安装包数量: {len(dist_to_modules)}")

    requirements = build_requirements(dist_to_modules)
    write_requirements_file(requirements)

    print(f"已生成: {OUTPUT_FILE.name}")
    print("请手动查看并根据需要合并到 requirements.txt 中。")


if __name__ == "__main__":
    main()


"""Generate a Markdown reference of all classes and functions in the project."""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Iterable, List, Sequence

SKIP_DIR_NAMES = {".git", ".venv", "__pycache__", ".mypy_cache", ".pytest_cache"}
SUPPORTED_SUFFIXES = {".py"}
DEFAULT_OUTPUT = Path("docs/API_REFERENCE.md")


def safe_unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    unparse = getattr(ast, "unparse", None)
    if callable(unparse):
        try:
            return unparse(node)
        except Exception:
            return "..."
    return "..."


def clean_docstring(value: str | None) -> str:
    if not value:
        return ""
    return os.linesep.join(line.rstrip() for line in value.strip().splitlines()).strip()


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


@dataclass
class FunctionDoc:
    name: str
    signature: str
    docstring: str


@dataclass
class ClassDoc:
    name: str
    docstring: str
    methods: List[FunctionDoc] = field(default_factory=list)


@dataclass
class ModuleDoc:
    path: Path
    classes: List[ClassDoc] = field(default_factory=list)
    functions: List[FunctionDoc] = field(default_factory=list)

    @property
    def module_heading(self) -> str:
        return str(self.path.as_posix())


def format_arguments(args: ast.arguments) -> str:
    parts: List[str] = []

    positional: List[ast.arg] = list(args.posonlyargs) + list(args.args)
    defaults: List[ast.expr | None] = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)

    for index, arg in enumerate(args.posonlyargs):
        default = defaults[index]
        text = arg.arg
        if default is not None:
            text += f"={safe_unparse(default)}"
        parts.append(text)
    if args.posonlyargs:
        parts.append("/")

    for offset, arg in enumerate(args.args):
        default = defaults[len(args.posonlyargs) + offset]
        text = arg.arg
        if default is not None:
            text += f"={safe_unparse(default)}"
        parts.append(text)

    if args.vararg:
        parts.append(f"*{args.vararg.arg}")
    elif args.kwonlyargs:
        parts.append("*")

    for kwarg, default in zip(args.kwonlyargs, args.kw_defaults):
        text = kwarg.arg
        if default is not None:
            text += f"={safe_unparse(default)}"
        parts.append(text)

    if args.kwarg:
        parts.append(f"**{args.kwarg.arg}")

    return ", ".join(parts)


def build_function_doc(node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionDoc:
    sig = f"{node.name}({format_arguments(node.args)})"
    doc = clean_docstring(ast.get_docstring(node)) or "No docstring provided."
    return FunctionDoc(name=node.name, signature=sig, docstring=doc)


def build_class_doc(node: ast.ClassDef) -> ClassDoc:
    doc = clean_docstring(ast.get_docstring(node)) or "No docstring provided."
    methods: List[FunctionDoc] = []
    for body_item in node.body:
        if isinstance(body_item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(build_function_doc(body_item))
    return ClassDoc(name=node.name, docstring=doc, methods=methods)


def parse_module(path: Path, *, root: Path) -> ModuleDoc | None:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    classes: List[ClassDoc] = []
    functions: List[FunctionDoc] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(build_class_doc(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(build_function_doc(node))

    if not classes and not functions:
        return None

    return ModuleDoc(path=path.relative_to(root), classes=classes, functions=functions)


def iter_python_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if should_skip(path):
            continue
        yield path


def render_markdown(modules: Sequence[ModuleDoc]) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: List[str] = []
    lines.append("# Project API Reference")
    lines.append("")
    lines.append(f"_Generated automatically on {timestamp}._")
    lines.append("")
    lines.append("Each section lists the classes and functions discovered per module. Methods are included under their respective classes.")
    lines.append("")

    for module in modules:
        lines.append(f"## {module.module_heading}")
        lines.append("")
        if module.classes:
            lines.append("### Classes")
            lines.append("")
            for cls in module.classes:
                lines.append(f"#### {cls.name}")
                lines.append("")
                lines.append(cls.docstring)
                lines.append("")
                if cls.methods:
                    lines.append("##### Methods")
                    lines.append("")
                    for method in cls.methods:
                        lines.append(f"- `{method.signature}` — {method.docstring}")
                    lines.append("")
        if module.functions:
            lines.append("### Functions")
            lines.append("")
            for func in module.functions:
                lines.append(f"- `{func.signature}` — {func.docstring}")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def generate_docs(root: Path, output: Path) -> None:
    root = root.resolve()
    modules: List[ModuleDoc] = []
    for file in sorted(iter_python_files(root)):
        if file.suffix not in SUPPORTED_SUFFIXES:
            continue
        module = parse_module(file, root=root)
        if module:
            modules.append(module)
    if not modules:
        raise SystemExit("No classes or functions found to document.")
    markdown = render_markdown(modules)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Destination Markdown file")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project root to scan")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_docs(args.root.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()

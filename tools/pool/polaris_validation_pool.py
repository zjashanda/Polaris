#!/usr/bin/env python3
"""Validate and classify Polaris modular validation-pool documents."""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REQUIRED_SECTIONS = [
    "## 适用需求特征",
    "## 变体维度",
    "## 需求解析字段",
    "## 验证方案模板",
    "## 用例模板",
    "## 断言与证据",
    "## 执行器映射",
    "## 回灌规则",
]

TEXT_EXTS = {".md", ".txt", ".csv", ".json", ".yaml", ".yml", ".h", ".c", ".cpp", ".py"}


@dataclass
class Module:
    path: Path
    module_id: str
    title: str
    tags: list[str]
    source_projects: list[str]
    text: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def pool_dir(root: Path) -> Path:
    return root / "references" / "validation-pool"


def parse_list(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [item.strip().strip("'\"") for item in value.split(",") if item.strip()]


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta


def load_modules(root: Path) -> list[Module]:
    modules: list[Module] = []
    for path in sorted(pool_dir(root).glob("*.md")):
        if path.name in {"INDEX.md", "schema.md"}:
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        meta = parse_frontmatter(text)
        modules.append(
            Module(
                path=path,
                module_id=meta.get("module_id", path.stem),
                title=meta.get("title", path.stem),
                tags=parse_list(meta.get("tags", "")),
                source_projects=parse_list(meta.get("source_projects", "")),
                text=text,
            )
        )
    return modules


def validate(root: Path) -> int:
    errors: list[str] = []
    base = pool_dir(root)
    if not (base / "INDEX.md").exists():
        errors.append("missing references/validation-pool/INDEX.md")
    if not (base / "schema.md").exists():
        errors.append("missing references/validation-pool/schema.md")

    seen: dict[str, Path] = {}
    modules = load_modules(root)
    for mod in modules:
        if not mod.module_id:
            errors.append(f"{mod.path}: missing module_id")
        if mod.module_id in seen:
            errors.append(f"duplicate module_id {mod.module_id}: {seen[mod.module_id]} and {mod.path}")
        seen[mod.module_id] = mod.path
        if not mod.tags:
            errors.append(f"{mod.path}: missing tags")
        for section in REQUIRED_SECTIONS:
            if section not in mod.text:
                errors.append(f"{mod.path}: missing section {section}")

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    print(f"validation pool valid: {len(modules)} modules")
    for mod in modules:
        print(f"- {mod.module_id}: {mod.title}")
    return 0


def iter_text_files(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_EXTS)
    return [path] if path.exists() and path.suffix.lower() in TEXT_EXTS else []


def collect_requirement_text(paths: list[Path]) -> str:
    chunks: list[str] = []
    for raw in paths:
        path = raw.expanduser().resolve()
        for file in iter_text_files(path):
            try:
                text = file.read_text(encoding="utf-8-sig", errors="ignore")
            except Exception:
                continue
            chunks.append(f"\n\n## FILE: {file}\n{text}")
    return "\n".join(chunks)


def score_module(mod: Module, requirement_text: str) -> tuple[int, list[str]]:
    hits: list[str] = []
    text_lower = requirement_text.lower()
    for tag in mod.tags:
        tag = tag.strip()
        if not tag:
            continue
        count = len(re.findall(re.escape(tag.lower()), text_lower))
        if count:
            hits.append(f"{tag}({count})")
    score = 0
    for hit in hits:
        match = re.search(r"\((\d+)\)", hit)
        if match:
            score += min(int(match.group(1)), 5)
    return score, hits


def classify(root: Path, requirement_paths: list[Path], out: Path | None, project_key: str) -> int:
    req_text = collect_requirement_text(requirement_paths)
    if not req_text.strip():
        print("ERROR: no readable requirement text found", file=sys.stderr)
        return 1

    rows: list[tuple[int, Module, list[str]]] = []
    for mod in load_modules(root):
        score, hits = score_module(mod, req_text)
        if score:
            rows.append((score, mod, hits))
    rows.sort(key=lambda item: (-item[0], item[1].module_id))

    lines = [
        f"# {project_key} 模块化验证池匹配结果",
        "",
        "## 输入",
        "",
    ]
    for path in requirement_paths:
        lines.append(f"- `{path}`")
    lines.extend([
        "",
        "## 候选模块",
        "",
        "| 模块 | 分数 | 命中关键词 | 处理建议 |",
        "| --- | ---: | --- | --- |",
    ])
    if rows:
        for score, mod, hits in rows:
            advice = "读取模块并选择变体" if score >= 3 else "低分候选，人工确认"
            lines.append(f"| `{mod.module_id}` | {score} | {', '.join(hits)} | {advice} |")
    else:
        lines.append("| 无 | 0 | - | 需要新增验证池模块 |")
    lines.extend([
        "",
        "## 后续动作",
        "",
        "1. 对高分模块读取对应 `references/validation-pool/*.md`。",
        "2. 按当前需求选择变体，禁止直接套历史结论。",
        "3. 生成当前功能的方案、用例、断言和执行器映射。",
        "4. 执行后将新增通用逻辑回灌验证池。",
        "",
    ])
    text = "\n".join(lines)
    if out:
        out = out.expanduser()
        if not out.is_absolute():
            out = root / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(out)
    else:
        print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Polaris modular validation-pool helper")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="validate module document structure")
    classify_parser = sub.add_parser("classify", help="classify requirement files against modules")
    classify_parser.add_argument("paths", nargs="+", type=Path)
    classify_parser.add_argument("--out", type=Path)
    classify_parser.add_argument("--project-key", default="polaris_midea_ac")
    return parser


def main() -> int:
    root = repo_root()
    args = build_parser().parse_args()
    if args.command == "validate":
        return validate(root)
    if args.command == "classify":
        return classify(root, args.paths, args.out, args.project_key)
    raise RuntimeError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())

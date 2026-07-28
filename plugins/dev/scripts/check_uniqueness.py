#!/usr/bin/env python3
"""(8) 유일성 체크.

카탈로그 uniqueness 규칙별로 대상 파일 종류 안에서 ID 토큰을 헤더 제목에서
수집하고, 같은 파일에서 같은 ID가 두 번 이상 등장하는지 검사한다.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import (  # noqa: E402
    CheckResult,
    Violation,
    dump_result,
    expand_file_kind,
    load_catalog,
    parse_sections,
    read_text,
)


CHECK_NAME = "uniqueness"


def run(catalog: dict, project_root: Path) -> CheckResult:
    result = CheckResult(check=CHECK_NAME)
    rules = catalog.get("uniqueness") or []
    fk = catalog.get("file_kinds") or {}

    for rule in rules:
        scope = rule.get("scope")
        pattern = rule.get("pattern")
        target_kind = rule.get("in")
        if not (scope and pattern and target_kind):
            continue
        kind_def = fk.get(target_kind)
        if not kind_def:
            continue
        regex = re.compile(pattern)

        for rf in expand_file_kind(target_kind, kind_def, project_root):
            if not rf.exists:
                continue
            content = read_text(rf.path)
            occurrences: dict[str, list[int]] = {}
            for sec in parse_sections(content):
                for m in regex.finditer(sec.title):
                    occurrences.setdefault(m.group(0), []).append(sec.line)
            for token, lines in occurrences.items():
                if len(lines) > 1:
                    result.add(Violation(
                        file=str(rf.path), line=lines[0], file_kind=target_kind,
                        rule="uniqueness_duplicate",
                        message=(
                            f"{scope} '{token}' 중복 — 라인 "
                            f"{', '.join(str(x) for x in lines)}"
                        ),
                    ))

    return result.finalize()


def main() -> int:
    parser = argparse.ArgumentParser(description="유일성 체크")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=None)
    args = parser.parse_args()
    catalog = load_catalog(args.catalog)
    result = run(catalog, args.project_root)
    print(dump_result(result))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())

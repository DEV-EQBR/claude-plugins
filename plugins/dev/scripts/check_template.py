#!/usr/bin/env python3
"""(1) 템플릿 적합성 체크.

각 상세설계서 파일이 카탈로그(file_kinds)에 정의된 필수 섹션과 필수 메타데이터를
갖췄는지 검사한다. 단일 경로(path) 정의는 파일 존재 여부도 함께 검사한다
(optional=true 인 경우 제외).

fragment(file_kind="fragment") 등은 generic required_sections/required_metadata만 적용한다.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 같은 디렉토리의 _lib.py를 import 하기 위한 경로 보정
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import (  # noqa: E402
    CheckResult,
    ResolvedFile,
    Violation,
    dump_result,
    expand_all_file_kinds,
    load_catalog,
    parse_metadata_block,
    parse_sections,
    read_text,
)


CHECK_NAME = "template"


def _check_one(rf: ResolvedFile, result: CheckResult) -> None:
    kind_def = rf.kind_def
    optional = bool(kind_def.get("optional"))

    # 단일 path 정의에 대한 파일 존재 검사
    if not rf.exists:
        if not optional:
            result.add(Violation(
                file=str(rf.path),
                file_kind=rf.kind,
                rule="file_exists",
                message=f"필수 파일 누락: {rf.path}",
            ))
        return

    content = read_text(rf.path)

    # 필수 섹션 (## 레벨)
    required_sections = kind_def.get("required_sections") or []
    if required_sections:
        existing = {s.title for s in parse_sections(content) if s.level == 2}
        for required in required_sections:
            if required not in existing:
                result.add(Violation(
                    file=str(rf.path),
                    file_kind=rf.kind,
                    rule="required_section",
                    message=f"필수 섹션 누락: '## {required}'",
                ))

    # 필수 메타데이터 (상단 인용 블록의 키)
    required_metadata = kind_def.get("required_metadata") or []
    if required_metadata:
        metadata = parse_metadata_block(content)
        for key in required_metadata:
            if key not in metadata:
                result.add(Violation(
                    file=str(rf.path),
                    file_kind=rf.kind,
                    rule="required_metadata",
                    message=f"필수 메타데이터 누락: '> {key}: ...'",
                ))

    # fragment 등은 위의 generic required_sections/required_metadata 검증만 적용한다


def run(catalog: dict, project_root: Path) -> CheckResult:
    """run_all.py 등에서 호출할 진입점."""
    result = CheckResult(check=CHECK_NAME)
    for rf in expand_all_file_kinds(catalog, project_root):
        _check_one(rf, result)
    return result.finalize()


def main() -> int:
    parser = argparse.ArgumentParser(description="템플릿 적합성 체크")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=None)
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    result = run(catalog, args.project_root)
    print(dump_result(result))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())

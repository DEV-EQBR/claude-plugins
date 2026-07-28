#!/usr/bin/env python3
"""(5) 스키마 유효성 체크.

각 상세설계서의 메타데이터 인용 블록 값이 카탈로그 metadata_schemas의 정규식과
일치하는지 검사한다. 키 자체의 부재는 (1) 템플릿 체크가 잡으므로 여기서는
'키는 있는데 값 형식이 깨진' 경우만 본다.
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
    expand_all_file_kinds,
    load_catalog,
    parse_metadata_block,
    read_text,
)


CHECK_NAME = "schemas"


def run(catalog: dict, project_root: Path) -> CheckResult:
    result = CheckResult(check=CHECK_NAME)
    schemas = (
        (catalog.get("metadata_schemas") or {}).get("default", {}).get("fields") or {}
    )
    if not schemas:
        return result.finalize()

    for rf in expand_all_file_kinds(catalog, project_root):
        if not rf.exists:
            continue
        required = rf.kind_def.get("required_metadata") or []
        if not required:
            continue
        meta = parse_metadata_block(read_text(rf.path))
        for key in required:
            value = meta.get(key)
            if value is None:
                continue  # template 체크가 담당
            schema = schemas.get(key)
            if not schema:
                continue
            pattern = schema.get("pattern")
            if pattern and not re.fullmatch(pattern, value):
                result.add(Violation(
                    file=str(rf.path), file_kind=rf.kind,
                    rule="metadata_format",
                    message=(
                        f"메타데이터 '{key}' 값 '{value}'이 형식 '{pattern}'과 "
                        f"일치하지 않는다"
                    ),
                ))
    return result.finalize()


def main() -> int:
    parser = argparse.ArgumentParser(description="스키마 유효성 체크")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=None)
    args = parser.parse_args()
    catalog = load_catalog(args.catalog)
    result = run(catalog, args.project_root)
    print(dump_result(result))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())

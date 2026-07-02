#!/usr/bin/env python3
"""(7) 커버리지 체크.

spec/domain/{도메인}/ 디렉토리별로 카탈로그 coverage.domain_required_files에
지정된 필수 파일이 모두 존재하는지 검사한다. cross-domain 디렉토리는 별도
파일 종류라 제외한다.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import (  # noqa: E402
    CheckResult,
    Violation,
    dump_result,
    load_catalog,
)


CHECK_NAME = "coverage"


def run(catalog: dict, project_root: Path) -> CheckResult:
    result = CheckResult(check=CHECK_NAME)
    coverage = catalog.get("coverage") or {}
    required_files = coverage.get("domain_required_files") or []
    if not required_files:
        return result.finalize()

    domain_dir = project_root / "spec" / "domain"
    if not domain_dir.is_dir():
        return result.finalize()

    for d in sorted(domain_dir.iterdir()):
        if not d.is_dir() or d.name == "cross-domain":
            continue
        for fname in required_files:
            target = d / fname
            if not target.exists():
                result.add(Violation(
                    file=str(target), file_kind="domain",
                    rule="coverage_required_file",
                    message=f"도메인 '{d.name}'에 필수 파일 {fname} 누락",
                ))

    return result.finalize()


def main() -> int:
    parser = argparse.ArgumentParser(description="커버리지 체크")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=None)
    args = parser.parse_args()
    catalog = load_catalog(args.catalog)
    result = run(catalog, args.project_root)
    print(dump_result(result))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())

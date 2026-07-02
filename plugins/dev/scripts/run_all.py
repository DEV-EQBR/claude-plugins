#!/usr/bin/env python3
"""spec 검증 deterministic 체크 오케스트레이터.

등록된 모든 체크 모듈을 순서대로 실행하고 통합 JSON 결과를 stdout으로 출력한다.
spec-verifier 에이전트가 이 결과를 파싱해 1차 판정에 활용한다.

체크 등록은 CHECKS 리스트에서 관리한다. 새 체크를 추가하려면 check_*.py를
작성하고 `run(catalog, project_root) -> CheckResult` 시그니처의 함수를 노출한 뒤
이 리스트에 추가한다.

종료 코드:
  0 = 모든 체크 통과
  1 = 1개 이상 체크에서 위반 발견
  2 = 실행 자체가 실패 (카탈로그 로드 실패 등)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import dump_results, load_catalog  # noqa: E402

import check_coverage  # noqa: E402
import check_cross_refs  # noqa: E402
import check_glossary  # noqa: E402
import check_links  # noqa: E402
import check_schemas  # noqa: E402
import check_template  # noqa: E402
import check_types  # noqa: E402
import check_uniqueness  # noqa: E402


# 등록된 체크 모듈. 8개 모두 활성화.
CHECKS = [
    check_template,        # (1) 템플릿 적합성
    check_links,           # (2) 링크 무결성
    check_cross_refs,      # (3) cross-reference 정합성
    check_glossary,        # (4) 용어 일관성
    check_schemas,         # (5) 스키마 유효성
    check_types,           # (6) 타입·포맷 정합성
    check_coverage,        # (7) 커버리지
    check_uniqueness,      # (8) 유일성
]


def main() -> int:
    parser = argparse.ArgumentParser(description="spec deterministic 체크 일괄 실행")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=None)
    args = parser.parse_args()

    try:
        catalog = load_catalog(args.catalog)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    results = [m.run(catalog, args.project_root) for m in CHECKS]

    print(dump_results(results))
    fail_count = sum(1 for r in results if r.status == "fail")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

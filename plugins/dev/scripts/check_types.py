#!/usr/bin/env python3
"""(6) 타입·포맷 정합성 체크 — 폐지됨.

작성 에이전트(`domain-api-writer`)는 api.md 필드 타입을 자연어로 자유 표기하고,
정합성은 `권위` 컬럼의 `entities.md X.Y` 매핑이 보장한다. 따라서 타입 문자열
비교(alias 매칭)는 작성 가이드의 추상화 수준과 어긋난 false-positive 소스다.

권위 참조 대상(엔티티·속성)의 실재 여부는 `check_cross_refs.api_field_authority_entity`가
이미 검증하므로, 본 체크는 별도로 둘 가치가 없다. 메타 원칙(검증↔작성 1:1 정렬)에
따라 본 체크는 폐지하고, 항상 비어 있는 결과만 반환하도록 둔다.

(스크립트 자체는 run_all 호환을 위해 남겨 두지만, 새 룰을 추가하지 말 것 —
타입 정합 영역은 cross_refs 권위 매핑 추적으로 일원화한다.)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import (  # noqa: E402
    CheckResult,
    dump_result,
    load_catalog,
)


CHECK_NAME = "types"


def run(catalog: dict, project_root: Path) -> CheckResult:
    return CheckResult(check=CHECK_NAME).finalize()


def main() -> int:
    parser = argparse.ArgumentParser(description="타입 정합성 체크 (폐지)")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=None)
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    result = run(catalog, args.project_root)
    print(dump_result(result))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
